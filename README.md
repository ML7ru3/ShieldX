# ShieldX - Hệ thống phát hiện mã độc qua DNS-over-HTTPS (DoH) sử dụng Machine Learning

**Đồ án tốt nghiệp** — Ngành An toàn thông tin, Trường Công nghệ Thông tin và Truyền thông, Đại học Bách khoa Hà Nội.

**Sinh viên:** Nguyễn Quang Trung — trung.nq225557@sis.hust.edu.vn  
**Giảng viên hướng dẫn:** TS. Nguyễn Hữu Đức

---

## Tổng quan

ShieldX là một **agent bảo mật endpoint thông minh** phát hiện giao tiếp mã độc qua **DNS-over-HTTPS (DoH)** bằng máy học. Hệ thống sử dụng pipeline 2 lớp (L1/L2) để phân loại luồng mạng và xác định hành vi độc hại.

## Kiến trúc hệ thống

```
DATN/
├── ShieldX/                 # Agent phát hiện mã độc (Python)
├── ShieldX-web/             # Web dashboard quản lý tập trung (FastAPI + React)
├── reports/                 # Luận văn tốt nghiệp (LaTeX)
└── .git/
```

```
                    +-----------------------+
                    |   ShieldX Agent       |
                    |   (Python)            |
                    |                       |   HTTPS/JSON
                    | - Packet Capture      |<---------->+-------------------+
                    |   (Scapy, TCP/443)    |             |  ShieldX-web      |
                    | - Flow Aggregation    |  heartbeat  |  (FastAPI+React)  |
                    | - Feature Extraction  |-----------> |                   |
                    |   (28 features)       |  alerts     | - Agent Manager   |
                    | - L1 Ensemble: XGBoost|-----------> | - Malware Alerts  |
                    |   RF, LGBM, SVM       |  domains    | - Domain Whitelist|
                    | - L2: XGBoost         |-----------> | - Recent Domains  |
                    |   (Malicious/Benign)  |             +-------------------+
                    | - nftables Firewall   |                    |
                    | - APScheduler         |                    | MySQL
                    +-----------------------+                    v
                                                          +-----------+
                                                          |  MySQL    |
                                                          +-----------+
```

## ShieldX — Agent phát hiện mã độc

### Cơ chế phát hiện 2 lớp

| Lớp | Chức năng | Models | Đầu ra |
|-----|-----------|--------|--------|
| **L1** | Phân loại DoH vs Non-DoH | XGBoost, Random Forest, LightGBM, SVM (biểu quyết đa số) | Label DoH/Non-DoH |
| **L2** | Phân loại Malicious vs Benign | XGBoost (huấn luyện trên CIC-DoHBrw-2020) | Label Malicious/Benign |

### Pipeline

1. **AsyncSniffer** (Scapy) bắt gói tin TCP/443
2. **FlowSession** nhóm gói tin thành luồng hai chiều
3. Trích xuất **28 đặc trưng thống kê** (bytes, packet length, timing, response time)
4. **L1 ensemble** — biểu quyết đa số 4 mô hình
5. Nếu là DoH → **L2 XGBoost** dự đoán Malicious/Benign
6. Cảnh báo mã độc gửi lên backend API
7. **nftables** chặn/cho phép domain theo whitelist

### Thành phần chính

| Thành phần | Mô tả |
|------------|-------|
| `src/agent_orchestrator.py` | Điều phối: heartbeat, whitelist, pipeline, giám sát mạng |
| `src/domains/pipeline.py` | Pipeline chính: capture → dự đoán → log |
| `src/domains/packet_processing/` | Bộ xử lý gói tin (dohlyzer, flow session, feature extraction) |
| `src/domains/firewall.py` | Quản lý nftables dựa trên whitelist |
| `src/domains/network_monitor.py` | Giám sát domain kết nối ra ngoài |
| `src/models/` | Scripts huấn luyện mô hình ML |
| `model_training/` | Huấn luyện & so sánh mô hình |
| `agent_config.yaml` | Cấu hình kết nối API backend |

## ShieldX-web — Dashboard quản lý tập trung

### Backend (FastAPI + MySQL)

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/heartbeat/` | GET/POST | Quản lý agent (đăng ký, heartbeat, phát hiện stale) |
| `/report-malware/` | GET/POST | Báo cáo & xem cảnh báo mã độc |
| `/domain/whitelist/` | GET/POST/PUT/DELETE | CRUD whitelist + bật/tắt |
| `/domain/recent/` | GET/POST | Domain gần đây của agent (có download .log) |

### Frontend (React + Chakra UI)

| Trang | Chức năng |
|-------|-----------|
| **Dashboard** | Thống kê tổng quan (agents, alerts, whitelist) |
| **Agents** | Danh sách agent + trạng thái (online/offline/stale) |
| **Agent Detail** | Chi tiết agent, domain gần đây, thêm whitelist |
| **Malware Alerts** | Danh sách cảnh báo + modal chi tiết |
| **Whitelist** | CRUD domain whitelist + bật/tắt |

### Công nghệ

| Phân hệ | Công nghệ |
|---------|-----------|
| **Agent** | Python, Scapy, XGBoost, LightGBM, scikit-learn, APScheduler, nftables |
| **Backend** | FastAPI, SQLModel, SQLAlchemy, MySQL, APScheduler |
| **Frontend** | React 19, TypeScript, Vite 8, Chakra UI 2, Framer Motion, Axios |
| **Luận văn** | LaTeX, IEEEtran |

## Tính năng chính

- Phát hiện mã độc qua DoH thời gian thực với mô hình học máy 2 lớp
- Biểu quyết đa số 4 mô hình L1 (XGBoost, RF, LightGBM, SVM)
- Quản lý agent tập trung qua web dashboard
- Cảnh báo mã độc real-time
- Domain whitelist CRUD + bật/tắt
- Tích hợp nftables firewall
- Phát hiện agent stale (offline sau 5 phút)
- Tự động chọn interface mạng thông minh
- Block DoH provider mặc định (iptables)
- Báo cáo so sánh mô hình L1 tự động
- Hỗ trợ dark mode theme

## Luận văn

Báo cáo đồ án hoàn chỉnh tại `reports/main.pdf` (LaTeX), bao gồm:
- Chương 1: Giới thiệu (động lực, mục tiêu, giải pháp)
- Chương 2: Khảo sát kiến thức và công trình liên quan
- Chương 3: Phương pháp giải quyết bài toán
- Chương 4: Thực nghiệm và đánh giá
- Chương 5: Đóng góp của giải pháp
- Chương 6: Kết luận

## Yêu cầu

- Python 3.10+
- MySQL 8.0
- Node.js 18+
- nftables (Linux)
- libpcap, Scapy

## Cài đặt & chạy

### Backend + Frontend
```bash
cd ShieldX-web
docker-compose up -d          # Khởi động MySQL
python backend/main.py        # Khởi động backend
cd frontend && npm install && npm run dev  # Khởi động frontend
```

### Agent
```bash
cd ShieldX
pip install -r requirements.txt
python src/main.py
```

---

**© 2026 Nguyễn Quang Trung — Đại học Bách khoa Hà Nội**
