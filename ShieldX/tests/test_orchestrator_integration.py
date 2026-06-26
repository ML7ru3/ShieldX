from unittest.mock import MagicMock, patch

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
