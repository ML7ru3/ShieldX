# Phân tích lỗi RuntimeWarning (Mean of empty slice & invalid value in scalar divide)

## 1. Mô tả lỗi

Khi chạy pipeline phát hiện DoH, xuất hiện 2 cảnh báo:

```
RuntimeWarning: Mean of empty slice
  return _methods._mean(a, axis=axis, dtype=dtype,

RuntimeWarning: invalid value encountered in scalar divide
  ret = ret.dtype.type(ret / rcount)
```

Kèm theo log:
```
INFO domains.pipeline: Non-DoH traffic | src=192.168.1.13:33561 -> dst=103.28.54.102:443
```

---

## 2. Nguyên nhân gốc rễ

### 2.1 Bug logic kiểm tra list rỗng (`!= 0` thay vì `len() != 0`)

Trong Python, `[] != 0` luôn trả về `True` (so sánh list với int). Điều này khiến guard không bao giờ ngăn được việc gọi numpy functions trên list rỗng.

| File | Dòng | Code hiện tại | Code đúng |
|------|------|---------------|-----------|
| `packet_length.py` | 64 | `if self.get_packet_length() != 0:` | `if len(self.get_packet_length()) != 0:` |
| `packet_time.py` | 91 | `if self._get_packet_times() != 0:` | `if len(self._get_packet_times()) != 0:` |

### 2.2 Thiếu kiểm tra empty-list hoàn toàn

| File | Dòng | Hàm | Vấn đề |
|------|------|------|--------|
| `src/domains/packet_processing/features/packet_length.py` | 45 | `get_var()` | Gọi `numpy.var()` không guard |
| `src/domains/packet_processing/features/packet_length.py` | 76 | `get_median()` | Gọi `numpy.median()` không guard |
| `src/domains/packet_processing/features/packet_time.py` | 72 | `get_var()` | Gọi `numpy.var()` không guard |
| `src/domains/packet_processing/features/packet_time.py` | 103 | `get_median()` | Gọi `numpy.median()` không guard |
| `src/domains/packet_processing/features/response_time.py` | 66 | `get_median()` | Gọi `numpy.median()` không guard |

### 2.3 Lỗi "invalid value in scalar divide" là hệ quả

Khi `mean()` / `var()` trả về `NaN` (do list rỗng), `NaN` lan truyền:

```
mean([]) = NaN
var([])  = NaN
std = sqrt(var) = sqrt(NaN) = NaN
dif = 3 * (mean - median) = 3 * (NaN - NaN) = NaN
→ dif / std = NaN / NaN → RuntimeWarning: invalid value in scalar divide
```

Các vị trí bị ảnh hưởng:

| File | Dòng | Phép tính |
|------|------|-----------|
| `packet_length.py` | 105 | `skew = dif / std` |
| `packet_length.py` | 123 | `skew2 = dif / std` |
| `packet_length.py` | 136 | `cov = self.get_std() / self.get_mean()` |
| `packet_time.py` | 132 | `skew = dif / std` |
| `packet_time.py` | 150 | `skew2 = dif / float(std)` |
| `packet_time.py` | 163 | `cov = self.get_std() / self.get_mean()` |
| `response_time.py` | 97 | `skew = dif / std` |
| `response_time.py` | 117 | `skew2 = dif / float(std)` |

### 2.4 Kịch bản kích hoạt thực tế

- **`response_time.py`**: Một flow TCP chỉ có gói FORWARD (SYN) mà không có REVERSE (SYN-ACK) → `get_dif()` trả về `[]`.
- **`packet_length.py` / `packet_time.py`**: Flow có 0 packet (hiếm nhưng cần phòng ngừa).

---

## 3. Hướng giải quyết

### 3.1 Sửa guard `!= 0` thành `len() != 0`

**File:** `src/domains/packet_processing/features/packet_length.py`

```python
# Dòng 64: sửa
- if self.get_packet_length() != 0:
+ if len(self.get_packet_length()) != 0:
```

**File:** `src/domains/packet_processing/features/packet_time.py`

```python
# Dòng 91: sửa
- if self._get_packet_times() != 0:
+ if len(self._get_packet_times()) != 0:
```

### 3.2 Thêm guard cho `get_var()` và `get_median()`

**Mẫu code áp dụng cho cả 3 file (`packet_length.py`, `packet_time.py`, `response_time.py`):**

```python
def get_var(self) -> float:
    data = self.get_packet_length()  # hoặc _get_packet_times(), get_dif()
    if len(data) == 0:
        return 0.0
    return numpy.var(data)

def get_median(self) -> float:
    data = self.get_packet_length()  # hoặc _get_packet_times(), get_dif()
    if len(data) == 0:
        return 0.0
    return numpy.median(data)
```

### 3.3 Guard NaN trong phép chia

Thêm kiểm tra `std != 0` kết hợp với `not numpy.isnan(dif)`:

```python
if std != 0 and not numpy.isnan(dif):
    skew = dif / std
else:
    skew = -10  # giá trị mặc định
```

Tương tự cho `get_cov()`:

```python
mean = self.get_mean()
if mean != 0 and not numpy.isnan(mean) and not numpy.isnan(self.get_std()):
    cov = self.get_std() / mean
```

### 3.4 Giảm log level "Non-DoH traffic"

**File:** `src/domains/pipeline.py` (dòng 129-136)

Đổi `logger.info` thành `logger.debug` để tránh spam console khi chạy production.

```python
logger.debug(
    "Non-DoH traffic | src=%s:%d -> dst=%s:%d",
    ...
)
```

---

## 4. Tổng quan các file cần sửa

| File (đường dẫn đầy đủ) | Dòng cần sửa | Mô tả |
|------------------------|-------------|-------|
| `src/domains/packet_processing/features/packet_length.py` | 45, 64, 65, 76, 105, 123, 136 | Guard empty + NaN |
| `src/domains/packet_processing/features/packet_time.py` | 72, 91, 92, 103, 132, 150, 163 | Guard empty + NaN |
| `src/domains/packet_processing/features/response_time.py` | 66, 97, 117 | Guard empty + NaN |
| `src/domains/pipeline.py` | 129 | Đổi INFO → DEBUG (tùy chọn) |

---

*Tài liệu được tạo ngày 2026-06-26 dựa trên phân tích runtime logs.*
