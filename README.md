# ShieldX Agent

Phát hiện malware DoH (DNS-over-HTTPS) dựa trên machine learning.

## Luồng xử lý chính

```
pipeline.capture_and_predict()
    │
    ├── 1. Sniff TCP 443 (AsyncSniffer + FlowCollector)
    ├── 2. Gom flow/session, trích xuất 28 đặc trưng thống kê
    ├── 3. Dự đoán bằng XGBoost model
    └── 4. Log kết quả (có TODO cho API cảnh báo)
```

## Các module chính

| Module | Vai trò |
|--------|---------|
| `src/pipeline.py` | Pipeline xử lý: capture → feature → predict → log |
| `src/agent_scheduler.py` | Scheduler APScheduler 5 phút, gọi pipeline định kỳ |
| `src/main.py` | Entry point chính, khởi tạo logging và scheduler |
| `src/domains/packet_processing/` | Capture packet, tạo flow, trích xuất đặc trưng (DoHlyzer) |
| `src/models/` | Scripts huấn luyện model (XGBoost, Random Forest, SVM, LightGBM) |

## Cấu hình scheduler

- **Interval**: 5 phút (cấu hình trong `agent_scheduler.scheduled_task()`)
- **Interface mạng**: `eth0` (sửa tham số `interface` trong `scheduled_task()`)
- **Thời gian sniff mỗi chu kỳ**: 120 giây (tham số `sniff_duration`)

## Sử dụng

```bash
# Chạy agent
python -m src.main

# Hoặc chạy trực tiếp scheduler
python -m src.agent_scheduler
```

## Mở rộng trong tương lai

- **Gửi API cảnh báo**: Tìm `TODO: Gửi cảnh báo qua API` trong `pipeline.py` để tích hợp
- **Thay model khác**: Sửa `MODEL_PATH` và `load_model()` trong `pipeline.py`
- **Lưu kết quả**: Thêm logic persist sau predict (hiện tại chỉ log, không ghi file)

## Testing

```bash
pytest tests/ -v
```

Ba kịch bản test chính:
1. **Đủ data** → sinh flow_session → predict
2. **Không đủ data** → capture rỗng → empty results
3. **Model/pipeline lỗi** → bắt exception → pipeline không dừng
