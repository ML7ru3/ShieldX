import os
import tempfile
from unittest.mock import patch, MagicMock
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

    @patch("domains.dns_proxy.subprocess.run")
    def test_disable_kills_dnsmasq_and_removes_iptables(self, mock_run, handler):
        mock_run.return_value = MagicMock(returncode=0)
        proc = MagicMock()
        handler.process = proc
        handler.disable()

        iptables_calls = [c for c in mock_run.call_args_list if "iptables" in str(c)]
        assert any("-D" in str(c) for c in iptables_calls)
        proc.terminate.assert_called_once()

    @patch("domains.dns_proxy.subprocess.Popen")
    @patch("domains.dns_proxy.subprocess.run")
    def test_start_calls_iptables_and_dnsmasq(self, mock_run, mock_popen, handler):
        mock_run.return_value = MagicMock(returncode=0)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        handler.start(domains=["example.com"], enabled=True)

        iptables_calls = [c for c in mock_run.call_args_list if "iptables" in str(c)]
        dnsmasq_calls = [c for c in mock_popen.call_args_list if "dnsmasq" in str(c)]
        assert len(iptables_calls) == 1
        assert len(dnsmasq_calls) == 1

    @patch("domains.dns_proxy.subprocess.Popen")
    @patch("domains.dns_proxy.subprocess.run")
    def test_stop_flushes_iptables_and_kills_dnsmasq(self, mock_run, mock_popen, handler):
        mock_run.return_value = MagicMock(returncode=0)
        proc = MagicMock()
        handler.process = proc
        handler.stop()

        iptables_calls = [c for c in mock_run.call_args_list if "iptables" in str(c)]
        assert any("-D" in str(c) for c in iptables_calls)
        proc.terminate.assert_called_once()

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

    @patch("domains.dns_proxy.subprocess.Popen")
    @patch("domains.dns_proxy.subprocess.run")
    def test_start_disabled_does_nothing(self, mock_run, mock_popen, handler):
        mock_run.return_value = MagicMock(returncode=0)
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        handler.start(domains=[], enabled=False)
        iptables_calls = [c for c in mock_run.call_args_list if "iptables" in str(c)]
        dnsmasq_calls = [c for c in mock_popen.call_args_list if "dnsmasq" in str(c)]
        assert len(iptables_calls) == 0
        assert len(dnsmasq_calls) == 0
