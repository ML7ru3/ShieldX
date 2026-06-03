KẾ HOẠCH TRIỂN KHAI (READ-ONLY)
1. Xác định entrypoint pipeline
- Sử dụng module/hàm trong @src/domains/packet_processing/ để:
- Capture gói tin tự động (không viết lại).
- Tạo flow/session, trích xuất đặc trưng đúng chuẩn (feature vector) đầu vào của AI model.
- Thu thập/mapping kết quả trả về là list các flow_session đã sẵn sàng dự đoán.
2. Load AI model XGBoost
- Loader XGBoost model từ file xgboost_model.json.
- Đảm bảo đúng interface predict (input là vector hoặc object như pipeline chuẩn hóa đã cài sẵn trong packet_processing).
3. Scheduler định kỳ
- Dùng APScheduler (hoặc tương đương) kiểu interval 5 phút cho tác vụ chính.
- Hàm tác vụ chính trong scheduler:
- Gọi pipeline capture packet và gom session.
- Duyệt từng flow_session, lấy đặc trưng truyền sang hàm dự đoán model AI.
- Lấy kết quả predict: nếu malware thì log chi tiết và để block TODO cho gửi API cảnh báo sau này; nếu benign thì log ngắn gọn.
4. Xử lý ngoại lệ, ghi log
- Toàn bộ pipeline bọc try/except, mọi exception đều log lại, pipeline không dừng đột ngột.
- Chỉ log/ghi thông tin liên quan đến cảnh báo (không lưu payload hay raw packet).
5. Block TODO dành cho gửi API cảnh báo (tạm thời comment lại), giúp mở rộng dễ dàng về sau.
6. Khuyến cáo testing
- Test 3 trường hợp tối thiểu:
- Đủ data sinh ra flow_session.
- Không đủ data.
- Model hoặc pipeline lỗi.
- Test với dữ liệu thật và dữ liệu mẫu nếu có.
7. Lưu ý integration
- Không được can thiệp logic xử lý nội bộ trong packet_processing — chỉ dùng API function/class có sẵn.
- Không ghi bất kỳ dữ liệu packet/flow/session xuống file cục bộ hay database.
8. Hướng dẫn sử dụng/Tài liệu
- Cập nhật README/docs: Mô tả entrypoint, luồng xử lý, các module chính, hướng dẫn cấu hình scheduler.
- Đánh dấu rõ vị trí TODO (cảnh báo), các vị trí có thể mở rộng thêm trong tương lai.
TODO Checklist thực hiện hóa
- [ ] Xác định hàm entrypoint từ packet_processing để gom session + đặc trưng
- [ ] Viết hàm/wrapper toàn pipeline gom -> đặc trưng -> predict -> log kết quả
- [ ] Load đúng model XGBoost (file xgboost_model.json)
- [ ] Tích hợp vào hàm chính chạy theo scheduler APScheduler (5 phút)
- [ ] Log kết quả, bắt/log lỗi ngoại lệ pipeline hoặc model
- [ ] Đặt block TODO/API khi có malware (không thực thi bước này ở phase đầu)
- [ ] Test các tình huống chính
- [ ] Cập nhật README mô tả pipeline & sử dụng
