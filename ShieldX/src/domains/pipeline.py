import logging
import time
import os
from collections import defaultdict

import numpy as np
import pandas as pd
import xgboost as xgb
from scapy.sendrecv import AsyncSniffer
from scapy.sessions import DefaultSession

from domains.packet_processing.flow_session import FlowSession, EXPIRED_UPDATE

logger = logging.getLogger(__name__)

DROP_FIELDS = ['SourceIP', 'SourcePort', 'DestinationIP', 'DestinationPort', 'Duration', 'TimeStamp', 'DoH']


def filter_model_features(features: dict) -> dict:
    return {k: v for k, v in features.items() if k not in DROP_FIELDS}


# ========== L1 Model (DoH vs Non-DoH) ==========

L1_MODEL_PATH = "l1_xgboost_model.json"
_l1_model = None


def load_l1_model():
    global _l1_model
    if _l1_model is None:
        _l1_model = xgb.XGBClassifier()
        _l1_model.load_model(L1_MODEL_PATH)
        logger.info("Loaded L1 model from %s", L1_MODEL_PATH)
    return _l1_model


def predict_l1(features):
    mdl = load_l1_model()
    if isinstance(features, dict):
        df = pd.DataFrame([features])
    elif isinstance(features, (list, np.ndarray)):
        df = pd.DataFrame([features])
    else:
        df = features
    pred = mdl.predict(df)
    return int(pred[0])


# ========== L2 Model (Malicious vs Benign) ==========

MODEL_PATH = "xgboost_model.json"
_model = None


def load_model():
    global _model
    if _model is None:
        _model = xgb.XGBClassifier()
        _model.load_model(MODEL_PATH)
        logger.info("Loaded XGBoost model from %s", MODEL_PATH)
    return _model


def predict(features):
    mdl = load_model()
    if isinstance(features, dict):
        df = pd.DataFrame([features])
    elif isinstance(features, (list, np.ndarray)):
        df = pd.DataFrame([features])
    else:
        df = features
    pred = mdl.predict(df)
    return int(pred[0])


# ========== Flow Collector ==========

class FlowCollector(FlowSession):
    output_mode = 'flow'
    output_file = '/dev/null'

    def __init__(self):
        self.flows = {}
        self.csv_line = 0
        self.packets_count = 0
        self.clumped_flows_per_label = defaultdict(list)
        DefaultSession.__init__(self)

    def garbage_collect(self, latest_time=None):
        keys = list(self.flows.keys())
        for k in keys:
            flow = self.flows.get(k)
            if flow is None:
                continue
            if latest_time is None or latest_time - flow.latest_timestamp > EXPIRED_UPDATE or flow.duration > 120:
                del self.flows[k]


# ========== Capture & Predict Pipeline ==========

def capture_and_predict(interface='eth0', sniff_duration=120):
    session = FlowCollector()
    sniffer = AsyncSniffer(
        iface=interface,
        filter='(ip or ip6) and tcp port 443',
        prn=session.on_packet_received,
        store=False,
    )
    sniffer.start()
    logger.info("Sniffing on %s for %d seconds...", interface, sniff_duration)
    try:
        time.sleep(sniff_duration)
    except Exception as e:
        logger.error("Error during sniffing: %s", e, exc_info=True)
    finally:
        if hasattr(sniffer, 'running') and sniffer.running:
            sniffer.stop()
            logger.info("Sniffing complete.")
        else:
            logger.warning("Sniffer was not running; skip stop().")

    flows = list(session.get_flows())
    logger.info("Captured %d flows", len(flows))

    results = []

    for flow in flows:
        try:
            features = flow.get_data()
            filtered_features = filter_model_features(features)
            assert all(key not in filtered_features for key in DROP_FIELDS), "Forbidden fields present in filtered features!"

            l1_pred = predict_l1(filtered_features)

            if l1_pred == 0:
                logger.info(
                    "Non-DoH traffic | src=%s:%d -> dst=%s:%d",
                    features.get('SourceIP'),
                    features.get('SourcePort'),
                    features.get('DestinationIP'),
                    features.get('DestinationPort'),
                )
                results.append((features, l1_pred, -1))
                continue

            l2_pred = predict(filtered_features)
            results.append((features, l1_pred, l2_pred))

            if l2_pred == 1:
                logger.warning(
                    "DoH traffic - MALWARE DETECTED | src=%s:%d -> dst=%s:%d | duration=%.2f",
                    features.get('SourceIP'),
                    features.get('SourcePort'),
                    features.get('DestinationIP'),
                    features.get('DestinationPort'),
                    features.get('Duration', 0),
                )
            else:
                logger.info(
                    "DoH traffic - Benign | src=%s:%d -> dst=%s:%d",
                    features.get('SourceIP'),
                    features.get('SourcePort'),
                    features.get('DestinationIP'),
                    features.get('DestinationPort'),
                )
        except AttributeError as exc:
            logger.error("AttributeError in packet processing (likely FORWARD/REVERSE): %s", exc, exc_info=True)
        except Exception as exc:
            logger.error("Error processing flow: %s", exc, exc_info=True)

    return results
