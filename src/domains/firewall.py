# src/firewall.py
from __future__ import annotations

import logging
import socket
import subprocess
from typing import Sequence

logger = logging.getLogger(__name__)

CHAIN = "shieldx-whitelist"


class FirewallError(Exception):
    pass


def _run(*args: str) -> None:
    result = subprocess.run(
        ["iptables"] + list(args),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise FirewallError(f"iptables error: {result.stderr.strip()}")


class FirewallManager:
    def apply_whitelist(self, domains: Sequence[str]) -> None:
        logger.info("Applying whitelist for %d domain(s)", len(domains))
        self._ensure_chain()
        self._flush_chain()
        self._add_base_rules()

        for domain in domains:
            try:
                _, _, ips = socket.gethostbyname_ex(domain)
            except socket.gaierror as exc:
                logger.warning("Cannot resolve domain %s: %s — skipping", domain, exc)
                continue
            for ip in ips:
                logger.debug("Allowing %s -> %s", domain, ip)
                _run("-A", CHAIN, "-d", ip, "-j", "ACCEPT")

        _run("-A", CHAIN, "-j", "DROP")
        logger.info("Whitelist applied — %d domain(s) allowed", len(domains))

    def flush(self) -> None:
        logger.info("Flushing ShieldX firewall rules")
        try:
            _run("-F", CHAIN)
            _run("-X", CHAIN)
        except FirewallError:
            pass  # chain may not exist on first call

    def _ensure_chain(self) -> None:
        result = subprocess.run(
            ["iptables", "-L", CHAIN],
            capture_output=True,
        )
        if result.returncode != 0:
            _run("-N", CHAIN)
            _run("-I", "OUTPUT", "-j", CHAIN)

    def _flush_chain(self) -> None:
        _run("-F", CHAIN)

    def _add_base_rules(self) -> None:
        # Always allow loopback and established/related connections
        _run("-A", CHAIN, "-o", "lo", "-j", "ACCEPT")
        _run("-A", CHAIN, "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT")
