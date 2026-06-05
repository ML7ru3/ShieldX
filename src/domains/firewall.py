# src/firewall.py
from __future__ import annotations

import logging
import socket
from typing import Sequence
import subprocess

logger = logging.getLogger(__name__)

NFTABLES_TABLE = "shieldx"
NFTABLES_CHAIN = "whitelist"

class FirewallError(Exception):
    pass

def _run_nft(*cmd: str) -> None:
    # Runs an nft command, raises FirewallError on failure
    logger.debug("Running: nft %s", ' '.join(cmd))
    result = subprocess.run(["nft"] + list(cmd), capture_output=True, text=True)
    if result.returncode != 0:
        raise FirewallError(f"nft error: {result.stderr.strip()}")

class FirewallManager:
    def _sanitize_domain(self, domain: str) -> str:
        # Remove http(s) protocol if present
        if '://' in domain:
            domain = domain.split('://', 1)[1]
        # Remove path/query/fragments
        domain = domain.split('/', 1)[0]
        return domain.strip()

    def apply_whitelist(self, domains: Sequence[str]) -> None:
        logger.info("Applying nftables whitelist for %d domain(s)", len(domains))

        resolved_ips = set()
        for domain in domains:
            clean_domain = self._sanitize_domain(domain)
            if not clean_domain:
                logger.warning(f"Received empty/invalid domain after sanitize: {domain}")
                continue
            try:
                _, _, ips = socket.gethostbyname_ex(clean_domain)
            except socket.gaierror as exc:
                logger.warning("Cannot resolve domain %s: %s — skipping", clean_domain, exc)
                continue
            for ip in ips:
                logger.debug("Allowing %s -> %s", clean_domain, ip)
                resolved_ips.add(ip)

        try:
            _run_nft('delete', 'table', 'inet', NFTABLES_TABLE)
        except FirewallError as e:
            logger.debug("Table delete (not present?): %s", e)
        _run_nft('add', 'table', 'inet', NFTABLES_TABLE)

        _run_nft('add', 'chain', 'inet', NFTABLES_TABLE, f'{NFTABLES_CHAIN} {{ type filter hook output priority 0; policy drop; }}')

        _run_nft('add', 'rule', 'inet', NFTABLES_TABLE, NFTABLES_CHAIN, 'oif', 'lo', 'accept')
        _run_nft('add', 'rule', 'inet', NFTABLES_TABLE, NFTABLES_CHAIN, 'ct', 'state', 'established,related', 'accept')
        for ip in resolved_ips:
            _run_nft('add', 'rule', 'inet', NFTABLES_TABLE, NFTABLES_CHAIN, 'ip', 'daddr', ip, 'accept')
        logger.info("Whitelist applied: %d unique IPs whitelisted via nftables", len(resolved_ips))

    def flush(self) -> None:
        logger.info("Flushing all nftables rules for ShieldX")
        try:
            _run_nft('delete', 'table', 'inet', NFTABLES_TABLE)
        except FirewallError as e:
            logger.debug("Flush: Table or chain not present: %s", e)


