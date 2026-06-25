# ShieldX Agent

Phát hiện malware DoH (DNS-over-HTTPS) dựa trên machine learning với kiến trúc 2-layer ensemble.

## Kiến trúc phát hiện

```
packet capture (TCP/443)
    │
    ▼
Layer 1 — DoH vs Non-DoH (4 models ensemble)
    ├── XGBoost
    ├── Random Forest
    ├── LightGBM
    └── SVM
    │
    ▼ (nếu là DoH)
Layer 2 — Malicious vs Benign (XGBoost)
    │
    ▼
Alert nếu phát hiện malware
```

## Luồng xử lý chính

```
pipeline.capture_and_predict()
    │
    ├── 1. Sniff TCP 443 (AsyncSniffer + FlowCollector)
    ├── 2. Gom flow/session, trích xuất 28 đặc trưng thống kê
    ├── 3. Layer 1: 4 models đều dự đoán → majority vote
    ├── 4. Layer 2: XGBoost dự đoán Malicious/Benign
    ├── 5. Log kết quả (có API cảnh báo)
    └── 6. Lưu báo cáo so sánh L1 models (l1_comparison_report.json)
```

## Các module chính

| Module | Vai trò |
|--------|---------|
| `src/agent_orchestrator.py` | Entry point chính, scheduler, heartbeat, whitelist, pipeline orchestration |
| `src/domains/pipeline.py` | Pipeline xử lý: capture → feature → predict → log + L1 ensemble |
| `src/domains/packet_processing/` | Capture packet, tạo flow, trích xuất 28 đặc trưng thống kê |
| `src/domains/firewall.py` | Quản lý nftables whitelist firewall rules |
| `src/models/` | Scripts huấn luyện model cho Layer 1 và Layer 2 |

## Model files

### Layer 1 (DoH vs Non-DoH)

| Model | File | Training Script |
|-------|------|----------------|
| XGBoost | `l1_xgboost_model.json` | `src/models/l1_xgboost.py` |
| Random Forest | `l1_random_forest_model.joblib` | `src/models/l1_random_forest.py` |
| LightGBM | `l1_lightgbm_model.txt` | `src/models/l1_lightgbm.py` |
| SVM | `l1_svm_model.joblib` | `src/models/l1_svm.py` |

### Layer 2 (Malicious vs Benign)

| Model | File | Training Script |
|-------|------|----------------|
| XGBoost | `xgboost_model.json` | `src/models/xgboost_model.py` |

## Training

```bash
# Train tất cả L1 models + sinh báo cáo so sánh
python3 model_training/train_all_l1_models.py

# Train từng model riêng lẻ
python3 -m src.models.l1_xgboost
python3 -m src.models.l1_random_forest
python3 -m src.models.l1_lightgbm
python3 -m src.models.l1_svm

# Train L2 model
python3 -m src.models.xgboost_model
```

## Sử dụng

```bash
# Kích hoạt virtual environment
source .venv/bin/activate

# Chạy agent
python3 src/main.py

# Hoặc set config tùy chỉnh
SHIELDX_CONFIG=agent_config.yaml python3 src/main.py
```

## Cấu hình (agent_config.yaml)

```yaml
api:
  register: "http://localhost:8000/heartbeat/"
  heartbeat: "http://localhost:8000/heartbeat/"
  malware_alert: "http://localhost:8000/report-malware/"
  get_whitelist: "http://localhost:8000/domain/whitelist/"
  report_recent_domains: "http://localhost:8000/domain/recent/"

heartbeat_interval: 90         # giây
sniff_duration: 120            # giây mỗi pipeline round
network_scan_interval: 60      # giây
interface_scan_interval: 30
log_path: "agent.log"
```

## Báo cáo so sánh L1 models

Sau mỗi pipeline round, file `l1_comparison_report.json` được tạo ra với nội dung:

```json
{
  "total_flows": 10,
  "full_agreement_count": 8,
  "full_agreement_pct": 80.0,
  "model_predictions": {
    "xgboost": { "non_doh_predicted": 7, "doh_predicted": 3 },
    "random_forest": { "non_doh_predicted": 6, "doh_predicted": 4 },
    "lightgbm": { "non_doh_predicted": 6, "doh_predicted": 4 },
    "svm": { "non_doh_predicted": 8, "doh_predicted": 2 }
  }
}
```

## Testing

```bash
pytest tests/ -v
```

Ba kịch bản test chính:
1. **Đủ data** → sinh flow_session → predict
2. **Không đủ data** → capture rỗng → empty results
3. **Model/pipeline lỗi** → bắt exception → pipeline không dừng
