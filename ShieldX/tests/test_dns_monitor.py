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
