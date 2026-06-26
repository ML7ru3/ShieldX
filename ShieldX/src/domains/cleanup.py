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
