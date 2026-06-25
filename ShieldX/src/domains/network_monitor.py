from __future__ import annotations

import logging
import socket
import time
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

import psutil

logger = logging.getLogger(__name__)

MAX_DOMAINS = 50

@dataclass
class DomainEntry:
    domain: str
    ip: str
    timestamp: float

class NetworkMonitor:
    def __init__(self, maxlen: int = MAX_DOMAINS):
        self._maxlen = maxlen
        self._domains: deque[DomainEntry] = deque(maxlen=maxlen)
        self._seen: set[str] = set()
        self._lock = Lock()
        self._last_updated: float = 0.0

    def _resolve_domain(self, ip: str) -> str:
        try:
            hostname, _, _ = socket.gethostbyaddr(ip)
            return hostname
        except (socket.herror, socket.gaierror, OSError):
            return ip

    def scan(self) -> None:
        now = time.time()
        new_entries = 0
        try:
            for conn in psutil.net_connections():
                if conn.type != socket.SOCK_STREAM:
                    continue
                if conn.status != "ESTABLISHED":
                    continue
                if not conn.raddr:
                    continue
                ip = conn.raddr.ip
                if not ip or ip.startswith(("127.", "0.", "192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.",
                                            "172.20.", "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
                                            "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.")):
                    continue
                domain = self._resolve_domain(ip)
                if domain == ip:
                    continue

                key = f"{domain}|{ip}"
                with self._lock:
                    if key not in self._seen:
                        self._seen.add(key)
                        self._domains.append(DomainEntry(domain=domain, ip=ip, timestamp=now))
                        new_entries += 1
        except Exception as e:
            logger.debug("Network scan error: %s", e)

        self._last_updated = now
        if new_entries > 0:
            logger.debug("Network scan: %d new domain(s)", new_entries)

    def get_domains(self) -> list[DomainEntry]:
        with self._lock:
            return list(self._domains)

    def get_last_updated(self) -> float:
        return self._last_updated
