import logging
import os
import signal
import subprocess
import time

logger = logging.getLogger(__name__)

IPTABLES_REDIRECT_RULE = [
    "iptables", "-t", "nat", "-A", "OUTPUT",
    "-p", "udp", "--dport", "53",
    "!", "-d", "127.0.0.1",
    "-j", "REDIRECT", "--to-port", "{port}"
]

IPTABLES_DELETE_RULE = [
    "iptables", "-t", "nat", "-D", "OUTPUT",
    "-p", "udp", "--dport", "53",
    "!", "-d", "127.0.0.1",
    "-j", "REDIRECT", "--to-port", "{port}"
]


class IptablesError(Exception):
    pass


class DnsmasqHandler:
    def __init__(
        self,
        config_path: str = "/tmp/shieldx-dnsmasq.conf",
        port: int = 5353,
        upstream: str = "8.8.8.8",
        fallback_upstream: str = "8.8.4.4",
    ):
        self.config_path = config_path
        self.port = port
        self.upstream = upstream
        self.fallback_upstream = fallback_upstream
        self.process = None

    def _write_config(self, whitelist_domains: list[str]) -> None:
        lines = [
            f"port={self.port}",
            "bind-interfaces",
            "listen-address=127.0.0.1",
            "no-resolv",
            "cache-size=0",
            "no-hosts",
        ]
        if whitelist_domains:
            for domain in whitelist_domains:
                lines.append(f"server=/{domain}/{self.upstream}")
                if self.fallback_upstream:
                    lines.append(f"server=/{domain}/{self.fallback_upstream}")
        else:
            lines.append(f"server={self.upstream}")
            if self.fallback_upstream:
                lines.append(f"server={self.fallback_upstream}")

        os.makedirs(os.path.dirname(self.config_path) or ".", exist_ok=True)
        with open(self.config_path, "w") as f:
            f.write("\n".join(lines) + "\n")
        logger.debug("Wrote dnsmasq config to %s", self.config_path)

    def _iptables_redirect(self, action: str) -> None:
        rule_template = IPTABLES_REDIRECT_RULE if action == "add" else IPTABLES_DELETE_RULE
        cmd = [part.format(port=self.port) for part in rule_template]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=10)
        except subprocess.CalledProcessError as e:
            raise IptablesError(f"iptables {action} failed: {e.stderr.strip()}")

    def enable(self, domains: list[str]) -> None:
        self._write_config(domains)
        self._restart_dnsmasq()

    def disable(self) -> None:
        self._write_config([])
        self._restart_dnsmasq()

    def start(self, domains: list[str], enabled: bool) -> None:
        self._iptables_redirect("add")
        if enabled:
            self.enable(domains)
        else:
            self.disable()

    def stop(self) -> None:
        self._kill_dnsmasq()
        try:
            self._iptables_redirect("delete")
        except IptablesError as e:
            logger.warning("Failed to remove iptables rule: %s", e)

    def update(self, domains: list[str], enabled: bool) -> None:
        if enabled:
            self.enable(domains)
        else:
            self.disable()

    def _restart_dnsmasq(self) -> None:
        self._kill_dnsmasq()
        self._start_dnsmasq()

    def _start_dnsmasq(self) -> None:
        try:
            self.process = subprocess.Popen(
                ["dnsmasq", "-C", self.config_path, "--no-daemon", "--log-facility=-"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            time.sleep(0.5)
            if self.process.poll() is not None:
                logger.error("dnsmasq exited immediately (exit code %d)", self.process.returncode)
                self.process = None
            else:
                logger.info("dnsmasq started (PID %d)", self.process.pid)
        except FileNotFoundError:
            logger.error("dnsmasq binary not found — install dnsmasq")

    def _kill_dnsmasq(self) -> None:
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.debug("dnsmasq (PID %d) terminated", self.process.pid)
            except Exception as e:
                logger.warning("Error stopping dnsmasq: %s", e)
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
