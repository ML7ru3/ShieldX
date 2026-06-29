import logging
import time
import json
import os
from collections import defaultdict, Counter

import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
import lightgbm as lgb
from scapy.sendrecv import AsyncSniffer
from scapy.sessions import DefaultSession

from domains.packet_processing.flow_session import FlowSession, EXPIRED_UPDATE

logger = logging.getLogger(__name__)

DROP_FIELDS = ['SourceIP', 'SourcePort', 'DestinationIP', 'DestinationPort', 'Duration', 'TimeStamp', 'DoH']

L1_REPORT_FILE = "l1_comparison_report.json"


def filter_model_features(features: dict) -> dict:
    return {k: v for k, v in features.items() if k not in DROP_FIELDS}


# ========== L1 Model Ensemble (DoH vs Non-DoH) ==========

class L1ModelManager:
    L1_MODELS = {
        'xgboost': ('l1_xgboost_model.json', 'xgboost'),
        'random_forest': ('l1_random_forest_model.joblib', 'joblib'),
        'lightgbm': ('l1_lightgbm_model.txt', 'lightgbm'),
    }

    def __init__(self, model_dir="."):
        self.models = {}
        self._load_all(model_dir)

    def _load_all(self, model_dir):
        for name, (path, kind) in self.L1_MODELS.items():
            full_path = os.path.join(model_dir, path)
            if kind == 'xgboost':
                mdl = xgb.XGBClassifier()
                mdl.load_model(full_path)
            elif kind == 'joblib':
                mdl = joblib.load(full_path)
            elif kind == 'lightgbm':
                mdl = lgb.Booster(model_file=full_path)
            self.models[name] = mdl
            logger.info("Loaded L1 model '%s' from %s", name, full_path)

    def predict(self, features):
        df = pd.DataFrame([features])
        results = {}
        for name, mdl in self.models.items():
            if isinstance(mdl, lgb.Booster):
                pred = mdl.predict(df)
                pred = int((pred[0] > 0.5))
            else:
                pred = int(mdl.predict(df)[0])
            results[name] = pred
        return results

    def majority_vote(self, predictions):
        votes = list(predictions.values())
        return Counter(votes).most_common(1)[0][0]


_l1_manager = None


def get_l1_manager():
    global _l1_manager
    if _l1_manager is None:
        _l1_manager = L1ModelManager()
    return _l1_manager


def load_l1_model():
    return get_l1_manager()


def predict_l1_ensemble(features):
    m = get_l1_manager()
    preds = m.predict(features)
    return m.majority_vote(preds), preds


# Old predict_l1 kept for backward compatibility (single XGBoost model in ensemble)
def predict_l1(features):
    pred, _ = predict_l1_ensemble(features)
    return pred


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

def save_l1_comparison_report(all_l1_details, output_path=L1_REPORT_FILE):
    if not all_l1_details:
        return

    model_names = list(all_l1_details[0].keys())
    total = len(all_l1_details)

    counts = {name: Counter() for name in model_names}
    agreement_count = 0

    for details in all_l1_details:
        votes = list(details.values())
        if len(set(votes)) == 1:
            agreement_count += 1
        for name, pred in details.items():
            counts[name][pred] += 1

    report = {
        'total_flows': total,
        'full_agreement_count': agreement_count,
        'full_agreement_pct': round(agreement_count / total * 100, 2) if total else 0,
        'model_predictions': {}
    }

    for name in model_names:
        c = counts[name]
        report['model_predictions'][name] = {
            'non_doh_predicted': c.get(0, 0),
            'doh_predicted': c.get(1, 0),
        }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info("L1 comparison report saved to %s", output_path)

    logger.info("L1 Model Comparison (from %d flows):", total)
    logger.info("  Full agreement: %d/%d (%.1f%%)", agreement_count, total,
                agreement_count / total * 100 if total else 0)
    for name in model_names:
        c = counts[name]
        logger.info("  %s: Non-DoH=%d  DoH=%d", name, c.get(0, 0), c.get(1, 0))


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
    all_l1_details = []

    for flow in flows:
        try:
            features = flow.get_data()
            filtered_features = filter_model_features(features)
            assert all(key not in filtered_features for key in DROP_FIELDS), "Forbidden fields present in filtered features!"

            l1_pred, l1_details = predict_l1_ensemble(filtered_features)
            all_l1_details.append(l1_details)

            if l1_pred == 0:
                logger.info(
                    "Non-DoH traffic | src=%s:%d -> dst=%s:%d",
                    features.get('SourceIP'),
                    features.get('SourcePort'),
                    features.get('DestinationIP'),
                    features.get('DestinationPort'),
                )
                results.append((features, l1_pred, -1, l1_details))
                continue

            l2_pred = predict(filtered_features)
            results.append((features, l1_pred, l2_pred, l1_details))

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

    if all_l1_details:
        save_l1_comparison_report(all_l1_details)

    return results
