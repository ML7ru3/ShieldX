"""
ShieldX Agent Orchestrator
- Reads API endpoint config from config file
- Collects system info and selects network interface
- Fetches/Refreshes domain whitelist from API + toggle status
- Applies/flushes nftables firewall rules based on whitelist toggle
- Monitors recent outbound domains and reports to API
- Runs detection pipeline: packet capture, feature extraction, ML prediction
- Periodically sends heartbeat + updates whitelist
- Sends malware alerts to backend API
"""
import sys
import os
import time
import json
import yaml
import logging
import requests

from apscheduler.schedulers.background import BackgroundScheduler

from domains import system_info
from domains.pipeline import load_model, load_l1_model, get_l1_manager, capture_and_predict
from domains.firewall import FirewallManager
from domains.network_monitor import NetworkMonitor
from domains.cleanup import cleanup_browsers, flush_dns_cache, DEFAULT_BROWSER_PROCESSES
from domains.dns_proxy import DnsmasqHandler
from domains.dns_monitor import DNSMonitor

CONFIG_PATH = os.environ.get("SHIELDX_CONFIG", "agent_config.yaml")

logger = logging.getLogger("shieldx"); logger.setLevel(logging.INFO)


# ----- CONFIG LOADING -----
def load_config(path=CONFIG_PATH):
    with open(path, "r") as f:
        base = f.read()
        if path.endswith(".json"):
            cfg = json.loads(base)
        else:
            cfg = yaml.safe_load(base)
    return cfg


# ----- LOGGING SETUP -----
def setup_file_logger(log_path):
    handler = logging.FileHandler(log_path)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)


# ----- NETWORK INTERFACE SELECTION -----
def select_best_interface():
    import psutil
    best_iface = None
    max_bytes = -1
    for name, stats in psutil.net_if_stats().items():
        if stats.isup and not name.startswith("lo"):
            counters = psutil.net_io_counters(pernic=True).get(name, None)
            if counters:
                tot = counters.bytes_recv + counters.bytes_sent
                if tot > max_bytes:
                    best_iface = name
                    max_bytes = tot
            elif not best_iface:
                best_iface = name
    if best_iface is None:
        for name, stats in psutil.net_if_stats().items():
            if stats.isup:
                return name
    return best_iface


def get_interface_ip(iface_name):
    import psutil
    try:
        for name, addrs in psutil.net_if_addrs().items():
            if name == iface_name:
                for addr in addrs:
                    if addr.family == 2:
                        return addr.address
    except Exception:
        pass
    return "0.0.0.0"


# ----- DOMAIN WHITELIST HANDLER -----
class DomainWL:
    def __init__(self):
        self.set = set()
        self.version = None
        self.enabled = True
    def reload_all(self, domlist, ver=None):
        self.set = set(domlist)
        self.version = ver
    def __contains__(self, d):
        return d in self.set


# ----- FIREWALL APPLY/FLUSH -----
_fw = FirewallManager()

def apply_firewall_rules(wl: DomainWL):
    if wl.enabled and wl.set:
        _fw.apply_whitelist(list(wl.set))
        logger.info("Firewall whitelist APPLIED (%d domains)", len(wl.set))
    elif not wl.enabled:
        _fw.flush()
        logger.info("Firewall whitelist FLUSHED (toggle OFF)")
    else:
        _fw.flush()
        logger.info("Firewall whitelist FLUSHED (no domains)")


# ----- EVENT SCHEDULER ------
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


def _fetch_whitelist(cfg, wl, dns_handler=None):
    try:
        res = requests.get(cfg['api']['get_whitelist'], timeout=8)
        res.raise_for_status()
        data = res.json()
        domains = [d['domain'] for d in data.get('domains', [])]
        new_enabled = data.get('whitelist_enabled', True)

        if new_enabled != wl.enabled:
            logger.info("Whitelist toggle changed: %s -> %s",
                        "enabled" if wl.enabled else "disabled",
                        "enabled" if new_enabled else "disabled")
            wl.enabled = new_enabled
            apply_firewall_rules(wl)

        wl.reload_all(domains, None)
        if dns_handler is not None:
            dns_handler.update(domains=list(wl.set), enabled=wl.enabled)
        logger.info("Refreshed domain whitelist (%d domains, enabled=%s)",
                    len(wl.set), wl.enabled)
    except Exception as e:
        logger.error("Whitelist update failed: %s", e)


def _send_recent_domains(cfg, agent_id, monitor: NetworkMonitor):
    try:
        entries = monitor.get_domains()
        if not entries:
            return
        domains_payload = [
            {"agent_id": agent_id, "domain": e.domain, "ip": e.ip}
            for e in entries[-50:]
        ]
        res = requests.post(
            cfg['api']['report_recent_domains'],
            json={"domains": domains_payload},
            timeout=10,
        )
        res.raise_for_status()
        logger.debug("Reported %d recent domains", len(domains_payload))
    except Exception as e:
        logger.debug("Failed to report recent domains: %s", e)


# ----- MALWARE ALERT -----
def send_malware_alert(cfg, agent_id, features):
    try:
        dst_ip = features.get('DestinationIP', 'unknown')
        dst_port = features.get('DestinationPort', 'unknown')
        payload = {
            "agent_id": agent_id,
            "malware_type": "doh_malware",
            "details": json.dumps({
                "src_ip": features.get('SourceIP'),
                "dst_ip": dst_ip,
                "dst_port": dst_port,
                "duration": features.get('Duration'),
                "flow_bytes_sent": features.get('FlowBytesSent'),
                "flow_bytes_received": features.get('FlowBytesReceived'),
            }),
        }
        res = requests.post(cfg['api']['malware_alert'], json=payload, timeout=10)
        res.raise_for_status()
        logger.warning("Reported malware to API: %s -> %s:%s", features.get('SourceIP'), dst_ip, dst_port)
    except Exception as e:
        logger.error("Failed to send malware alert: %s", e)


# ----- MAIN PIPELINE RUN -----
def pipeline_round(cfg, agent_id, iface, wl):
    logger.info(">>> Pipeline round started (iface: %s)", iface)
    try:
        results = capture_and_predict(interface=iface, sniff_duration=cfg.get("sniff_duration", 120))
        for item in results:
            features, l1_pred, l2_pred = item[0], item[1], item[2]
            if l1_pred == 1 and l2_pred == 1:
                send_malware_alert(cfg, agent_id, features)
    except Exception as e:
        logger.error("Error in pipeline round: %s", e)
    logger.info("<<< Pipeline round finished")


# ----- MAIN ENTRY POINT -----
def main():
    cfg = load_config()
    setup_file_logger(cfg.get("log_path", "shieldx.log"))
    logger.info("SHIELDX AGENT starting up...")

    # Pre-startup cleanup
    browser_procs = cfg.get("pre_startup", {}).get("browser_processes", DEFAULT_BROWSER_PROCESSES)
    # cleanup_browsers(browser_procs)
    flush_dns_cache()

    si = system_info.collect_system_info()
    iface = select_best_interface()
    logger.info("Selected network interface: %s", iface)
    if iface is None:
        logger.error("NO network interface UP/available! Exiting.")
        sys.exit(1)

    agent_id = si.hostname
    hostname = si.hostname
    ip = get_interface_ip(iface)

    payload = {
        "agent_id": agent_id,
        "hostname": hostname,
        "ip": ip,
    }

    try:
        res = requests.post(cfg["api"]["register"], json=payload, timeout=10)
        res.raise_for_status()
        logger.info("Registered agent %s with API server.", agent_id)
    except Exception as e:
        logger.error("Registration failed, but agent will continue. %s", e)

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
    dns_log_path = dns_mon_cfg.get("log_path")
    dns_mon = DNSMonitor(interface=iface, maxlen=dns_mon_cfg.get("max_buffer", 200), log_path=dns_log_path)
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


if __name__ == "__main__":
    main()
