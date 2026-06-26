# ShieldX Dual-Port Agent — DNS Whitelist + DoH Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add DNS-layer whitelist enforcement (dnsmasq) + DNS query logging (Scapy AsyncSniffer) on port 53 alongside existing DoH detection on port 443.

**Architecture:** Two independent subsystems: (1) Port 53 — pre-startup cleanup → dnsmasq proxy for whitelist enforcement + Scapy AsyncSniffer for unconditional query logging → heartbeat reporting; (2) Port 443 — unchanged existing pipeline with 2-layer ML ensemble.

**Tech Stack:** Python 3, Scapy, dnsmasq (external binary), iptables, nftables, APScheduler, pytest

## Global Constraints

- All pre-startup cleanup failures must be non-fatal (log warning, continue startup)
- dnsmasq runs on port 5353 (not 53) to avoid conflict with systemd-resolved
- iptables redirect covers UDP 53 traffic only
- AsyncSniffer runs unconditionally regardless of whitelist toggle
- DNS query log sent via heartbeat payload, not a separate API call
- Port 443 pipeline code must not be modified
- All new code follows existing project patterns (logging.getLogger(__name__), subprocess.run for system commands)

---
### Task 1: Pre-startup Cleanup

**Files:**
- Create: `src/domains/cleanup.py`
- Test: `tests/test_cleanup.py`

**Interfaces:**
- Produces: `cleanup_browsers(processes: list[str]) -> None`, `flush_dns_cache() -> None`

- [ ] **Step 1: Write the failing test**

```python
import subprocess
from unittest.mock import patch, MagicMock

import pytest


class TestCleanupBrowsers:
    @patch("domains.cleanup.subprocess.run")
    def test_kills_each_process(self, mock_run):
        from domains.cleanup import cleanup_browsers

        cleanup_browsers(["firefox", "chrome"])

        assert mock_run.call_count == 2
        calls = [args[0][0] for args in mock_run.call_args_list]
        assert any("firefox" in str(c) for c in calls)
        assert any("chrome" in str(c) for c in calls)

    @patch("domains.cleanup.subprocess.run")
    def test_non_fatal_on_missing_process(self, mock_run):
        from domains.cleanup import cleanup_browsers

        mock_run.side_effect = FileNotFoundError("no such file")
        cleanup_browsers(["firefox"])  # should not raise

    @patch("domains.cleanup.subprocess.run")
    def test_default_processes_list(self, mock_run):
        from domains.cleanup import DEFAULT_BROWSER_PROCESSES

        assert "firefox" in DEFAULT_BROWSER_PROCESSES
        assert "chrome" in DEFAULT_BROWSER_PROCESSES


class TestFlushDnsCache:
    @patch("domains.cleanup.subprocess.run")
    def test_flush_with_resolvectl(self, mock_run):
        from domains.cleanup import flush_dns_cache

        mock_run.return_value = MagicMock(returncode=0)
        flush_dns_cache()

        assert any("resolvectl" in str(c) for c in mock_run.call_args_list[0][0])

    @patch("domains.cleanup.subprocess.run")
    def test_fallback_on_resolvectl_failure(self, mock_run):
        from domains.cleanup import flush_dns_cache

        mock_run.side_effect = [  # first call fails (no resolvectl)
            FileNotFoundError("no resolvectl"),
            MagicMock(returncode=0),  # second call (systemctl)
        ]
        flush_dns_cache()

        assert mock_run.call_count == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/mltrue/Documents/Repos/DATN/ShieldX && python -m pytest tests/test_cleanup.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'domains.cleanup'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/domains/cleanup.py
import logging
import subprocess

logger = logging.getLogger(__name__)

DEFAULT_BROWSER_PROCESSES = ["firefox", "chrome", "chromium", "msedge", "brave", "opera"]


def cleanup_browsers(processes: list[str]) -> None:
    for proc in processes:
        try:
            subprocess.run(["pkill", "-f", proc], capture_output=True, text=True, timeout=5)
            logger.info("Killed browser process: %s", proc)
        except FileNotFoundError:
            logger.debug("pkill not found, skipping kill for %s", proc)
        except subprocess.TimeoutExpired:
            logger.warning("Timeout killing %s", proc)
        except Exception as e:
            logger.warning("Failed to kill %s: %s", proc, e)


def flush_dns_cache() -> None:
    try:
        subprocess.run(["resolvectl", "flush-caches"], check=True, capture_output=True, text=True, timeout=5)
        logger.info("DNS cache flushed via resolvectl")
        return
    except FileNotFoundError:
        logger.debug("resolvectl not found, trying systemd-resolve")
    except subprocess.TimeoutExpired:
        logger.warning("Timeout flushing DNS cache via resolvectl")
        return
    except subprocess.CalledProcessError as e:
        logger.warning("resolvectl failed: %s", e.stderr.strip())

    try:
        subprocess.run(["systemd-resolve", "--flush-caches"], check=True, capture_output=True, text=True, timeout=5)
        logger.info("DNS cache flushed via systemd-resolve")
    except FileNotFoundError:
        logger.warning("No DNS flush tool found (resolvectl/systemd-resolve)")
    except subprocess.TimeoutExpired:
        logger.warning("Timeout flushing DNS cache via systemd-resolve")
    except subprocess.CalledProcessError as e:
        logger.warning("systemd-resolve failed: %s", e.stderr.strip())
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/mltrue/Documents/Repos/DATN/ShieldX && python -m pytest tests/test_cleanup.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domains/cleanup.py tests/test_cleanup.py
git commit -m "feat: add pre-startup cleanup (browser kill + DNS flush)"
```

---
### Task 2: DnsmasqHandler — DNS Proxy for Whitelist Enforcement

**Files:**
- Create: `src/domains/dns_proxy.py`
- Test: `tests/test_dns_proxy.py`

**Interfaces:**
- Produces:
  - `class DnsmasqHandler` with:
    - `__init__(config_path="/tmp/shieldx-dnsmasq.conf", port=5353, upstream="8.8.8.8", fallback_upstream="8.8.4.4")`
    - `start(domains: list[str], enabled: bool) -> None`
    - `stop() -> None`
    - `enable(domains: list[str]) -> None`
    - `disable() -> None`
    - `update(domains: list[str], enabled: bool) -> None`

- [ ] **Step 1: Write the failing test**

```python
import os
import tempfile
from unittest.mock import patch, MagicMock, call
import pytest


class TestDnsmasqHandler:
    @pytest.fixture
    def handler(self):
        from domains.dns_proxy import DnsmasqHandler
        with tempfile.NamedTemporaryFile(suffix=".conf", delete=False) as f:
            config_path = f.name
        h = DnsmasqHandler(config_path=config_path)
        yield h
        if os.path.exists(config_path):
            os.unlink(config_path)

    def test_init_defaults(self, handler):
        assert handler.port == 5353
        assert handler.upstream == "8.8.8.8"
        assert handler.fallback_upstream == "8.8.4.4"

    def test_enable_creates_config_with_whitelist(self, handler):
        handler.enable(["example.com", "google.com"])
        with open(handler.config_path) as f:
            content = f.read()
        assert "server=/example.com/8.8.8.8" in content
        assert "server=/google.com/8.8.8.8" in content
        assert "port=5353" in content
        assert "bind-interfaces" in content

    def test_enable_no_default_server(self, handler):
        handler.enable(["example.com"])
        with open(handler.config_path) as f:
            content = f.read()
        lines = content.strip().split("\n")
        server_lines = [l for l in lines if l.startswith("server=") and not l.startswith("server=/")]
        assert len(server_lines) == 0

    def test_disable_creates_config_with_default_server(self, handler):
        handler.disable()
        with open(handler.config_path) as f:
            content = f.read()
        assert "server=8.8.8.8" in content

    @patch("domains.dns_proxy.subprocess.run")
    def test_start_calls_iptables_and_dnsmasq(self, mock_run, handler):
        mock_run.return_value = MagicMock(returncode=0)
        handler.start(domains=["example.com"], enabled=True)

        iptables_calls = [c for c in mock_run.call_args_list if "iptables" in str(c)]
        dnsmasq_calls = [c for c in mock_run.call_args_list if "dnsmasq" in str(c)]
        assert len(iptables_calls) == 1
        assert len(dnsmasq_calls) == 1

    @patch("domains.dns_proxy.subprocess.run")
    def test_stop_flushes_iptables_and_kills_dnsmasq(self, mock_run, handler):
        mock_run.return_value = MagicMock(returncode=0)
        handler.process = MagicMock()
        handler.stop()

        iptables_calls = [c for c in mock_run.call_args_list if "iptables" in str(c)]
        assert any("-D" in str(c) for c in iptables_calls)
        handler.process.terminate.assert_called_once()

    @patch("domains.dns_proxy.subprocess.run")
    def test_update_calls_enable_when_enabled(self, mock_run, handler):
        handler.enable = MagicMock()
        handler.disable = MagicMock()
        handler.update(["example.com"], enabled=True)
        handler.enable.assert_called_once_with(["example.com"])
        handler.disable.assert_not_called()

    @patch("domains.dns_proxy.subprocess.run")
    def test_update_calls_disable_when_disabled(self, mock_run, handler):
        handler.enable = MagicMock()
        handler.disable = MagicMock()
        handler.update(["example.com"], enabled=False)
        handler.disable.assert_called_once()
        handler.enable.assert_not_called()

    @patch("domains.dns_proxy.subprocess.run")
    def test_start_without_whitelist_forwards_all(self, mock_run, handler):
        mock_run.return_value = MagicMock(returncode=0)
        handler.start(domains=[], enabled=False)
        dnsmasq_calls = [c for c in mock_run.call_args_list if "dnsmasq" in str(c)]
        assert len(dnsmasq_calls) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/mltrue/Documents/Repos/DATN/ShieldX && python -m pytest tests/test_dns_proxy.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'domains.dns_proxy'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/domains/dns_proxy.py
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/mltrue/Documents/Repos/DATN/ShieldX && python -m pytest tests/test_dns_proxy.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domains/dns_proxy.py tests/test_dns_proxy.py
git commit -m "feat: add DnsmasqHandler for DNS whitelist enforcement"
```

---
### Task 3: DNSMonitor — AsyncSniffer for DNS Query Logging

**Files:**
- Create: `src/domains/dns_monitor.py`
- Test: `tests/test_dns_monitor.py`

**Interfaces:**
- Produces:
  - `@dataclass class DNSEntry(src_ip: str, domain: str, timestamp: float)`
  - `class DNSMonitor` with:
    - `__init__(interface: str, maxlen: int = 200)`
    - `start() -> None`
    - `stop() -> None`
    - `get_entries() -> list[DNSEntry]`
    - `drain_entries() -> list[DNSEntry]`

- [ ] **Step 1: Write the failing test**

```python
import time
from unittest.mock import MagicMock, patch
from collections import deque

import pytest


class TestDNSEntry:
    def test_dns_entry_creation(self):
        from domains.dns_monitor import DNSEntry

        entry = DNSEntry(src_ip="192.168.1.5", domain="example.com", timestamp=1000.0)
        assert entry.src_ip == "192.168.1.5"
        assert entry.domain == "example.com"
        assert entry.timestamp == 1000.0


class TestDNSMonitor:
    @pytest.fixture
    def monitor(self):
        from domains.dns_monitor import DNSMonitor
        return DNSMonitor(interface="eth0", maxlen=5)

    def test_init(self, monitor):
        assert monitor.interface == "eth0"
        assert monitor.maxlen == 5
        assert len(monitor.entries) == 0

    def test_get_entries_returns_copy(self, monitor):
        from domains.dns_monitor import DNSEntry

        monitor._on_packet_callback(DNSEntry(src_ip="1.1.1.1", domain="test.com", timestamp=1.0))
        entries = monitor.get_entries()
        assert len(entries) == 1
        entries.clear()
        assert len(monitor.get_entries()) == 1

    def test_drain_entries_clears_buffer(self, monitor):
        from domains.dns_monitor import DNSEntry

        monitor._on_packet_callback(DNSEntry(src_ip="1.1.1.1", domain="test.com", timestamp=1.0))
        assert len(monitor.drain_entries()) == 1
        assert len(monitor.get_entries()) == 0

    def test_buffer_respects_maxlen(self, monitor):
        from domains.dns_monitor import DNSEntry

        for i in range(10):
            monitor._on_packet_callback(DNSEntry(src_ip="1.1.1.1", domain=f"test{i}.com", timestamp=float(i)))
        assert len(monitor.get_entries()) == 5

    @patch("domains.dns_monitor.AsyncSniffer")
    def test_start_creates_sniffer(self, mock_sniffer_cls, monitor):
        monitor.start()
        mock_sniffer_cls.assert_called_once()
        args, kwargs = mock_sniffer_cls.call_args
        assert kwargs["iface"] == "eth0"
        assert "udp and port 53" in kwargs.get("filter", "")

    @patch("domains.dns_monitor.AsyncSniffer")
    def test_start_starts_sniffer(self, mock_sniffer_cls, monitor):
        mock_sniffer = MagicMock()
        mock_sniffer_cls.return_value = mock_sniffer
        monitor.start()
        mock_sniffer.start.assert_called_once()

    @patch("domains.dns_monitor.AsyncSniffer")
    def test_stop_stops_sniffer(self, mock_sniffer_cls, monitor):
        mock_sniffer = MagicMock()
        mock_sniffer_cls.return_value = mock_sniffer
        monitor.start()
        monitor.stop()
        mock_sniffer.stop.assert_called_once()

    def test_parse_dns_query_packet(self, monitor):
        from domains.dns_monitor import DNSEntry
        from scapy.layers.dns import DNS, DNSQR, DNSRR
        from scapy.layers.inet import IP, UDP
        from scapy.packet import Raw

        pkt = (
            IP(src="192.168.1.10", dst="8.8.8.8") /
            UDP(sport=54321, dport=53) /
            DNS(id=1, qr=0, qd=DNSQR(qname="example.com"))
        )
        monitor._on_packet(pkt)
        entries = monitor.get_entries()
        assert len(entries) == 1
        assert entries[0].src_ip == "192.168.1.10"
        assert entries[0].domain == "example.com"

    def test_ignores_dns_response(self, monitor):
        from scapy.layers.dns import DNS, DNSQR, DNSRR
        from scapy.layers.inet import IP, UDP

        pkt = (
            IP(src="8.8.8.8", dst="192.168.1.10") /
            UDP(sport=53, dport=54321) /
            DNS(id=1, qr=1, qd=DNSQR(qname="example.com"), an=DNSRR(rrname="example.com", rdata="1.2.3.4"))
        )
        monitor._on_packet(pkt)
        assert len(monitor.get_entries()) == 0

    def test_ignores_non_dns_packet(self, monitor):
        from scapy.layers.inet import IP, TCP

        pkt = IP(src="1.1.1.1", dst="2.2.2.2") / TCP(sport=80, dport=443)
        monitor._on_packet(pkt)
        assert len(monitor.get_entries()) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/mltrue/Documents/Repos/DATN/ShieldX && python -m pytest tests/test_dns_monitor.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'domains.dns_monitor'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/domains/dns_monitor.py
import logging
import time
from collections import deque
from dataclasses import dataclass, field
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /home/mltrue/Documents/Repos/DATN/ShieldX && python -m pytest tests/test_dns_monitor.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domains/dns_monitor.py tests/test_dns_monitor.py
git commit -m "feat: add DNSMonitor with AsyncSniffer for query logging"
```

---
### Task 4: Config + Orchestrator Integration

**Files:**
- Modify: `agent_config.yaml` (add new sections)
- Modify: `src/agent_orchestrator.py` (wire cleanup, dnsmasq, DNS monitor into main)
- Test: `tests/test_orchestrator_integration.py`

**Interfaces:**
- Consumes: `cleanup_browsers`, `flush_dns_cache` from `domains.cleanup`
- Consumes: `DnsmasqHandler` from `domains.dns_proxy`
- Consumes: `DNSMonitor`, `DNSEntry` from `domains.dns_monitor`

- [ ] **Step 1: Write the failing test**

```python
import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestOrchestratorIntegration:
    @patch("agent_orchestrator.cleanup_browsers")
    @patch("agent_orchestrator.flush_dns_cache")
    def test_cleanup_called_on_startup(self, mock_flush, mock_cleanup):
        """Verify cleanup functions are called during main() startup sequence."""
        from agent_orchestrator import main

        with patch("agent_orchestrator.load_config") as mock_load_cfg:
            mock_load_cfg.return_value = {
                "api": {"register": "", "heartbeat": "", "malware_alert": "", "get_whitelist": "", "report_recent_domains": ""},
                "heartbeat_interval": 9999,
                "sniff_duration": 9999,
                "network_scan_interval": 9999,
                "log_path": "/tmp/test_shieldx.log",
                "pre_startup": {"browser_processes": ["firefox", "chrome"]},
                "dns_proxy": {"enabled": True, "port": 5353, "upstream": "8.8.8.8", "fallback_upstream": "8.8.4.4", "config_path": "/tmp/test_dnsmasq.conf"},
                "dns_monitor": {"max_buffer": 200, "filter": "udp and port 53"},
            }
            with patch("agent_orchestrator.setup_file_logger"):
                with patch("agent_orchestrator.system_info.collect_system_info") as mock_si:
                    mock_si.return_value = MagicMock(hostname="test-agent")
                    with patch("agent_orchestrator.select_best_interface") as mock_iface:
                        mock_iface.return_value = "eth0"
                        with patch("agent_orchestrator.get_interface_ip") as mock_ip:
                            mock_ip.return_value = "192.168.1.1"
                            with patch("agent_orchestrator.DnsmasqHandler") as mock_dnsmasq_cls:
                                with patch("agent_orchestrator.DNSMonitor") as mock_mon_cls:
                                    with patch("agent_orchestrator.BackgroundScheduler") as mock_sched_cls:
                                        with patch("agent_orchestrator.time.sleep", side_effect=KeyboardInterrupt):
                                            with patch("agent_orchestrator.requests.post") as mock_post:
                                                with patch("agent_orchestrator.requests.get") as mock_get:
                                                    mock_get.return_value.json.return_value = {"domains": [], "whitelist_enabled": True}
                                                    mock_post.return_value = MagicMock()
                                                    mock_sched = MagicMock()
                                                    mock_sched_cls.return_value = mock_sched

                                                    try:
                                                        main()
                                                    except SystemExit:
                                                        pass

                                                    mock_cleanup.assert_called_once_with(["firefox", "chrome"])
                                                    mock_flush.assert_called_once()

    @patch("agent_orchestrator.requests.post")
    def test_heartbeat_includes_dns_queries(self, mock_post):
        """Verify DNSMonitor entries are included in heartbeat payload."""
        from agent_orchestrator import run_heartbeat

        mock_post.return_value = MagicMock()

        mock_cfg = {"api": {"heartbeat": "http://test/", "get_whitelist": "http://test/whitelist", "report_recent_domains": "http://test/recent"}}

        mock_wl = MagicMock()
        mock_monitor = MagicMock()
        mock_dns_mon = MagicMock()
        mock_dns_mon.drain_entries.return_value = [
            MagicMock(src_ip="192.168.1.10", domain="example.com", timestamp=1000.0),
            MagicMock(src_ip="192.168.1.11", domain="test.org", timestamp=1001.0),
        ]

        with patch("agent_orchestrator._fetch_whitelist"):
            with patch("agent_orchestrator._send_recent_domains"):
                run_heartbeat(mock_cfg, "agent-1", "host1", "eth0", mock_wl, mock_monitor, mock_dns_mon, None)

                call_args = mock_post.call_args
                payload = call_args[1]["json"]
                assert "dns_queries" in payload
                assert len(payload["dns_queries"]) == 2
                assert payload["dns_queries"][0]["domain"] == "example.com"

    @patch("agent_orchestrator.requests.post")
    def test_heartbeat_empty_dns_queries(self, mock_post):
        """Verify heartbeat works with empty DNS log."""
        from agent_orchestrator import run_heartbeat

        mock_post.return_value = MagicMock()

        mock_cfg = {"api": {"heartbeat": "http://test/", "get_whitelist": "http://test/whitelist", "report_recent_domains": "http://test/recent"}}

        mock_wl = MagicMock()
        mock_monitor = MagicMock()
        mock_dns_mon = MagicMock()
        mock_dns_mon.drain_entries.return_value = []

        with patch("agent_orchestrator._fetch_whitelist"):
            with patch("agent_orchestrator._send_recent_domains"):
                run_heartbeat(mock_cfg, "agent-1", "host1", "eth0", mock_wl, mock_monitor, mock_dns_mon, None)

                call_args = mock_post.call_args
                payload = call_args[1]["json"]
                assert "dns_queries" in payload
                assert len(payload["dns_queries"]) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/mltrue/Documents/Repos/DATN/ShieldX && python -m pytest tests/test_orchestrator_integration.py -v
```
Expected: FAIL (because `run_heartbeat` still has old signature, no dns_queries in payload)

- [ ] **Step 3: Update config file**

Update `agent_config.yaml` — add new sections after existing content:

```yaml
pre_startup:
  browser_processes:
    - firefox
    - chrome
    - chromium
    - msedge
    - brave
    - opera

dns_proxy:
  enabled: true
  port: 5353
  upstream: 8.8.8.8
  fallback_upstream: 8.8.4.4
  config_path: /tmp/shieldx-dnsmasq.conf

dns_monitor:
  max_buffer: 200
  filter: "udp and port 53"
```

- [ ] **Step 4: Modify `src/agent_orchestrator.py`**

Add imports at top:

```python
from domains.cleanup import cleanup_browsers, flush_dns_cache, DEFAULT_BROWSER_PROCESSES
from domains.dns_proxy import DnsmasqHandler
from domains.dns_monitor import DNSMonitor
```

Modify `run_heartbeat` signature and body — add `dns_mon` parameter and include DNS queries in payload:

```python
def run_heartbeat(cfg, agent_id, hostname, iface, wl, monitor, dns_mon, dns_handler=None):
    try:
        ip = get_interface_ip(iface)
        payload = {
            "agent_id": agent_id,
            "hostname": hostname,
            "ip": ip,
        }
        dns_entries = dns_mon.drain_entries()
        payload["dns_queries"] = [
            {"src_ip": e.src_ip, "domain": e.domain, "timestamp": e.timestamp}
            for e in dns_entries
        ]
        res = requests.post(cfg['api']['heartbeat'], json=payload, timeout=8)
        res.raise_for_status()
        _fetch_whitelist(cfg, wl, dns_handler)
        _send_recent_domains(cfg, agent_id, monitor)
    except Exception as e:
        logger.error("HEARTBEAT failed: %s", e)
```

Modify `main()` — add cleanup at start, DNS proxy + monitor init, wire into heartbeat:

```python
def main():
    cfg = load_config()
    setup_file_logger(cfg.get("log_path", "shieldx.log"))
    logger.info("SHIELDX AGENT starting up...")

    # Pre-startup cleanup
    browser_procs = cfg.get("pre_startup", {}).get("browser_processes", DEFAULT_BROWSER_PROCESSES)
    cleanup_browsers(browser_procs)
    flush_dns_cache()

    si = system_info.collect_system_info()
    iface = select_best_interface()
    ...

    agent_id = si.hostname
    ...

    whitelist = DomainWL()
    _fetch_whitelist(cfg, whitelist)
    apply_firewall_rules(whitelist)

    # DNS proxy (dnsmasq)
    dns_proxy_cfg = cfg.get("dns_proxy", {})
    dns_handler = DnsmasqHandler(
        config_path=dns_proxy_cfg.get("config_path", "/tmp/shieldx-dnsmasq.conf"),
        port=dns_proxy_cfg.get("port", 5353),
        upstream=dns_proxy_cfg.get("upstream", "8.8.8.8"),
        fallback_upstream=dns_proxy_cfg.get("fallback_upstream", "8.8.4.4"),
    )
    dns_handler.start(domains=list(whitelist.set), enabled=whitelist.enabled)

    # DNS monitor
    dns_mon_cfg = cfg.get("dns_monitor", {})
    dns_mon = DNSMonitor(interface=iface, maxlen=dns_mon_cfg.get("max_buffer", 200))
    dns_mon.start()

    monitor = NetworkMonitor(maxlen=50)
    load_model()
    load_l1_model()

    sched = BackgroundScheduler()
    sched.add_job(
        lambda: run_heartbeat(cfg, agent_id, hostname, iface, whitelist, monitor, dns_mon, dns_handler),
        'interval',
        seconds=cfg.get('heartbeat_interval', 90)
    )
    sched.add_job(
        lambda: monitor.scan(),
        'interval',
        seconds=cfg.get('network_scan_interval', 60)
    )
    sched.add_job(
        lambda: pipeline_round(cfg, agent_id, iface, whitelist),
        'interval',
        seconds=cfg.get('sniff_duration', 120)
    )
    sched.start()
    logger.info("Scheduler started (heartbeat, network scan, pipeline, whitelist reload)")

    try:
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Agent shutting down...")
        dns_mon.stop()
        dns_handler.stop()
        sched.shutdown()
```

Also update `_fetch_whitelist` to update dnsmasq:

```python
def _fetch_whitelist(cfg, wl, dns_handler=None):
    ...
    wl.reload_all(domains, None)
    if dns_handler is not None:
        dns_handler.update(domains=list(wl.set), enabled=wl.enabled)
    ...
```

And update its callers accordingly — in `run_heartbeat` pass `dns_handler`:

```python
_fetch_whitelist(cfg, wl, dns_handler)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd /home/mltrue/Documents/Repos/DATN/ShieldX && python -m pytest tests/test_orchestrator_integration.py -v
```
Expected: PASS

- [ ] **Step 6: Run all tests to verify no regressions**

```bash
cd /home/mltrue/Documents/Repos/DATN/ShieldX && python -m pytest tests/ -v
```
Expected: ALL PASS (including existing `test_pipeline.py`)

- [ ] **Step 7: Commit**

```bash
git add agent_config.yaml src/agent_orchestrator.py tests/test_orchestrator_integration.py
git commit -m "feat: integrate DNS cleanup, proxy, and monitor into orchestrator"
```

---
## Files Summary

| File | Action |
|------|--------|
| `src/domains/cleanup.py` | Create |
| `src/domains/dns_proxy.py` | Create |
| `src/domains/dns_monitor.py` | Create |
| `src/agent_orchestrator.py` | Modify |
| `agent_config.yaml` | Modify |
| `tests/test_cleanup.py` | Create |
| `tests/test_dns_proxy.py` | Create |
| `tests/test_dns_monitor.py` | Create |
| `tests/test_orchestrator_integration.py` | Create |
