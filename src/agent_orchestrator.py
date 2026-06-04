"""
ShieldX Agent Orchestrator
- Đọc cấu hình endpoint từ config file
- Thu thập system info và select network interface
- Lấy/Reload domain whitelist từ API
- Khởi tạo pipeline: block DoH, packet sniffer, ML, logging
- Định kỳ gửi heartbeat + cập nhật whitelist + check interface
- Log mọi event ra file
- Gửi alert phát hiện malware
"""
import sys
import os
import time
import json
import yaml
import logging
import requests
import threading
from collections import defaultdict

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
    """Chọn interface UP với lưu lượng lớn nhất, fallback: interface đầu tiên UP."""
    import psutil
    import socket
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
        # TH dùng duy nhất lo hoặc máy ảo
        for name, stats in psutil.net_if_stats().items():
            if stats.isup:
                return name
    return best_iface

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
def run_heartbeat(cfg, si, iface, wl):
    # Gửi heartbeat info lên API
    try:
        info = {"system": si.to_dict(), "interface": iface, "whitelist_version": wl.version}
        res = requests.post(cfg['api']['heartbeat'], json=info, timeout=8)
        res.raise_for_status()
        res = res.json()
        # Nếu api trả về domain_whitelist mới luôn thì apply
        if 'whitelist' in res:
            wl.reload_all(res['whitelist'], res.get('version'))
            logger.info("[HEARTBEAT] Whitelist RELOADED, version=%s, %d domains", wl.version, len(wl.set))
        else:
            # Hoặc tự gọi lại lấy whitelist
            _fetch_whitelist(cfg, wl)
    except Exception as e:
        logger.error("HEARTBEAT failed: %s", e)

def _fetch_whitelist(cfg, wl):
    try:
        res = requests.get(cfg['api']['get_whitelist'], timeout=8)
        res.raise_for_status()
        data = res.json()
        wl.reload_all(data['whitelist'], data.get('version'))
        logger.info("Got/Refreshed domain whitelist (%d domains)", len(wl.set))
    except Exception as e:
        logger.error("Whitelist update failed: %s", e)

# ----- MALWARE ALERT -----
def send_malware_alert(cfg, features):
    try:
        res = requests.post(cfg['api']['malware_alert'], json={"malware": features}, timeout=10)
        res.raise_for_status()
        logger.warning("Reported malware to API: %s", features)
    except Exception as e:
        logger.error("Failed to send malware alert: %s", e)

# ----- MAIN PIPELINE RUN -----
def pipeline_round(cfg, si, iface, wl):
    logger.info(">>> Pipeline round started (iface: %s)", iface)
    try:
        results = capture_and_predict(interface=iface, sniff_duration=cfg.get("sniff_duration", 120))
        for features, pred in results:
            if pred == 1:
                send_malware_alert(cfg, features)
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
    logger.info(f"Selected network interface: {iface}")
    if iface is None:
        logger.error("NO network interface UP/available! Exiting.")
        sys.exit(1)

    # Gửi đăng ký lần đầu
    try:
        res = requests.post(cfg["api"]["register"], json={"system": si.to_dict(), "interface": iface}, timeout=10)
        res.raise_for_status()
        logger.info("Registered agent with API server.")
    except Exception as e:
        logger.error("Registration failed, but agent will continue. %s", e)

    # Lấy domain whitelist lần đầu
    whitelist = DomainWL()
    _fetch_whitelist(cfg, whitelist)

    # Khởi tạo ML model (local)
    load_model()

    sched = BackgroundScheduler()
    sched.add_job(lambda: run_heartbeat(cfg, si, iface, whitelist), 'interval', seconds=cfg.get('heartbeat_interval', 90))
    sched.add_job(lambda: pipeline_round(cfg, si, iface, whitelist), 'interval', seconds=cfg.get('sniff_duration', 120))
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
