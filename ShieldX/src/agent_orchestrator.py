"""
ShieldX Agent Orchestrator
- Reads API endpoint config from config file
- Collects system info and selects network interface
- Fetches/Refreshes domain whitelist from API
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
from domains.pipeline import load_model, capture_and_predict

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
    def reload_all(self, domlist, ver=None):
        self.set = set(domlist)
        self.version = ver
    def __contains__(self, d):
        return d in self.set


# ----- EVENT SCHEDULER ------
def run_heartbeat(cfg, agent_id, hostname, iface, wl):
    try:
        ip = get_interface_ip(iface)
        payload = {
            "agent_id": agent_id,
            "hostname": hostname,
            "ip": ip,
        }
        res = requests.post(cfg['api']['heartbeat'], json=payload, timeout=8)
        res.raise_for_status()
        _fetch_whitelist(cfg, wl)
    except Exception as e:
        logger.error("HEARTBEAT failed: %s", e)


def _fetch_whitelist(cfg, wl):
    try:
        res = requests.get(cfg['api']['get_whitelist'], timeout=8)
        res.raise_for_status()
        data = res.json()
        domains = [d['domain'] for d in data.get('domains', [])]
        wl.reload_all(domains, None)
        logger.info("Refreshed domain whitelist (%d domains)", len(wl.set))
    except Exception as e:
        logger.error("Whitelist update failed: %s", e)


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
        for features, pred in results:
            if pred == 1:
                send_malware_alert(cfg, agent_id, features)
    except Exception as e:
        logger.error("Error in pipeline round: %s", e)
    logger.info("<<< Pipeline round finished")


# ----- MAIN ENTRY POINT -----
def main():
    cfg = load_config()
    setup_file_logger(cfg.get("log_path", "shieldx.log"))
    logger.info("SHIELDX AGENT starting up...")

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

    load_model()

    sched = BackgroundScheduler()
    sched.add_job(lambda: run_heartbeat(cfg, agent_id, hostname, iface, whitelist), 'interval', seconds=cfg.get('heartbeat_interval', 90))
    sched.add_job(lambda: pipeline_round(cfg, agent_id, iface, whitelist), 'interval', seconds=cfg.get('sniff_duration', 120))
    sched.start()
    logger.info("Scheduler started (heartbeat & pipeline & whitelist reload)")

    try:
        while True:
            time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Agent shutting down...")
        sched.shutdown()


if __name__ == "__main__":
    main()
