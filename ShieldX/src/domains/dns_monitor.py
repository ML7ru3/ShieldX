import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

from scapy.all import AsyncSniffer
from scapy.layers.dns import DNS, DNSQR
from scapy.layers.inet import IP

logger = logging.getLogger(__name__)


@dataclass
class DNSEntry:
    src_ip: str
    domain: str
    timestamp: float


class DNSMonitor:
    def __init__(self, interface: str, maxlen: int = 200):
        self.interface = interface
        self.maxlen = maxlen
        self.entries: deque[DNSEntry] = deque(maxlen=maxlen)
        self._sniffer: Optional[AsyncSniffer] = None

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

    def _on_packet(self, pkt) -> None:
        if not pkt.haslayer(DNS) or not pkt.haslayer(IP):
            return
        dns = pkt[DNS]
        if dns.qr != 0:
            return
        if not dns.qd:
            return
        domain = dns.qd.qname.decode("utf-8", errors="replace").rstrip(".")
        src_ip = pkt[IP].src
        entry = DNSEntry(src_ip=src_ip, domain=domain, timestamp=time.time())
        self._on_packet_callback(entry)

    def _on_packet_callback(self, entry: DNSEntry) -> None:
        self.entries.append(entry)

    def get_entries(self) -> list[DNSEntry]:
        return list(self.entries)

    def drain_entries(self) -> list[DNSEntry]:
        entries = list(self.entries)
        self.entries.clear()
        return entries
