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
            MagicMock(returncode=0),  # second call (systemd-resolve)
        ]
        flush_dns_cache()

        assert mock_run.call_count == 2
