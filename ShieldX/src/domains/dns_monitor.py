import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

from scapy.all import AsyncSniffer
from scapy.layers.dns import DNS
from scapy.layers.inet import IP
from scapy.layers.inet6 import IPv6

logger = logging.getLogger(__name__)


@dataclass
class DNSEntry:
    src_ip: str
    domain: str
    timestamp: float


class DNSMonitor:
    def __init__(self, interface: str, maxlen: int = 200, log_path: Optional[str] = None):
        self.interface = interface
        self.maxlen = maxlen
        self.entries: deque[DNSEntry] = deque(maxlen=maxlen)
        self._sniffer: Optional[AsyncSniffer] = None
        self._log_file = None
        if log_path:
            self._log_file = open(log_path, "a", encoding="utf-8")
            logger.info("DNS query log: %s", log_path)

    def start(self) -> None:
        self._sniffer = AsyncSniffer(
            iface=self.interface,
            filter="udp and port 53",
            prn=self._on_packet,
            store=False,
        )
        self._sniffer.start()
        logger.info("DNS monitor started on %s", self.interface)

    def stop(self) -> None:
        if self._sniffer is not None:
            self._sniffer.stop()
            self._sniffer = None
            logger.info("DNS monitor stopped")
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None

    def _on_packet(self, pkt) -> None:
        if not pkt.haslayer(DNS):
            return
        if not pkt.haslayer(IP) and not pkt.haslayer(IPv6):
            return
        dns = pkt[DNS]
        if dns.qr != 0:
            return
        if not dns.qd:
            return
        domain = dns.qd.qname.decode("utf-8", errors="replace").rstrip(".")
        src_ip = pkt[IPv6].src if IPv6 in pkt else pkt[IP].src
        entry = DNSEntry(src_ip=src_ip, domain=domain, timestamp=time.time())
        self._on_packet_callback(entry)

    def _on_packet_callback(self, entry: DNSEntry) -> None:
        self.entries.append(entry)
        if self._log_file is not None:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(entry.timestamp))
            self._log_file.write(f"{ts},{entry.src_ip},{entry.domain}\n")
            self._log_file.flush()

    def get_entries(self) -> list[DNSEntry]:
        return list(self.entries)

    def drain_entries(self) -> list[DNSEntry]:
        entries = list(self.entries)
        self.entries.clear()
        return entries
