# NTP Time Synchronization - Flow Diagram

## 1. Hệ thống & Tham số

### Nodes
- **Server A (Stratum 1)**: Thời gian chuẩn = 10:00:00.000
- **Node B (Slow)**: Đồng hồ = 09:59:59.900 (chậm -100ms), Drift = +10 ppm
- **Node C (Fast)**: *Cần thêm thông tin*

### Tham số Demo
| Tham số | Giá trị | Mô tả |
|--------|--------|-------|
| CLOCK.ADJ | 1 giây | Cập nhật mỗi giây |
| CLOCK.PHASE | 6 | Hệ số chia = 2^6 = 64 |
| CLOCK.MAX | 128ms | Ngưỡng chấp nhận |

---

## 2. Giai đoạn xử lý (Timeline)

```
┌─────────────────────────────────────────────────────┐
│ Giai đoạn 1: Đo lường (Measurement)                 │
│ Node B gửi NTP request → Server A phản hồi          │
└─────────────────────────────────────────────────────┘
           ↓
   t1=09:59:59.900 (B gửi)
   t2=10:00:00.010  (A nhận)
   t3=10:00:00.012  (A gửi)
   t4=09:59:59.922  (B nhận)
           ↓
┌─────────────────────────────────────────────────────┐
│ Giai đoạn 2: Tính toán                              │
│ Delay d = (t4-t1) - (t3-t2) = 20ms                  │
│ Offset c = ((t2-t1) + (t3-t4))/2 = +100ms           │
└─────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────┐
│ Giai đoạn 3: Quyết định (Decision)                  │
│ |c| = 100ms < 128ms → Chấp nhận Slewing             │
│ Nạp: Clock-Adjust = +100ms                          │
│      Drift-Comp = -10 ppm                           │
└─────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────┐
│ Giai đoạn 4: Điều chỉnh (Slewing) - Lặp mỗi 1s      │
│ Nhịp 1:   Adj = 100/64 = 1.5625ms (Còn 98.4375ms)   │
│ Nhịp 2:   Adj = 98.4375/64 = 1.5381ms (Còn 96.8994) │
│ ...                                                  │
│ Nhịp 60:  Còn 38.8ms (Sau 1 phút)                   │
│ Nhịp 180: Còn 5.8ms (Sau 3 phút)                    │
└─────────────────────────────────────────────────────┘
           ↓
         Sync hoàn tất
```

---

## 3. Docker Architecture

```
┌──────────────────────────────────────────┐
│         Docker Network (Bridge)          │
├──────────────────────────────────────────┤
│                                          │
│  ┌─────────────┐  ┌─────────────┐       │
│  │  Server A   │  │  Node B     │       │
│  │  (Port 123) │  │  (NTP)      │       │
│  └─────────────┘  └─────────────┘       │
│        ↑                ↑                │
│        └────────┬───────┘                │
│                 │                        │
│        ┌─────────────────┐               │
│        │  NTP Requests   │               │
│        └─────────────────┘               │
│                                          │
│  ┌─────────────────────────────────┐    │
│  │  Node C (Faster)                │    │
│  │  (Tham số cần thêm)             │    │
│  └─────────────────────────────────┘    │
│                                          │
└──────────────────────────────────────────┘
```

---

## 4. Output & Visualization

### Logging Format (Console)
```
[2026-04-21 10:00:05] Node B - Sync Status
├─ Current Time: 09:59:59.950
├─ Expected Time: 10:00:00.000
├─ Offset: -50ms (giảm từ -100ms)
├─ Adjustment: 1.5625ms
└─ Status: Slewing (Nhịp 5/180)
```

### Visualization
- **Console Output**: Real-time status mỗi giây
- **File Log**: CSV format để plot sau
- **Dashboard**: (Optional) Simple HTTP server hiển thị graph

---

## 5. Best Practice Stack

- **Language**: Python 3.10+
- **Networking**: `socket` (NTP protocol)
- **Containerization**: Docker Compose
- **Clock Simulation**: Custom clock class
- **Logging**: Python `logging`
- **Visualization**: Matplotlib hoặc terminal-based chart

---

## 6. Cấu trúc Project

```
project/
├── docker-compose.yml
├── src/
│   ├── server.py          (Server A - Stratum 1)
│   ├── client.py          (Generic NTP client)
│   ├── ntp_clock.py       (Clock simulation)
│   ├── ntp_protocol.py    (NTP message handling)
│   └── logger.py          (Logging config)
├── configs/
│   ├── server_config.json
│   ├── node_b_config.json (Slow: -100ms, +10ppm)
│   └── node_c_config.json (Fast: +Xms, -Yppm)
├── logs/
│   ├── server.log
│   ├── node_b.log
│   └── node_c.log
└── results/
    └── sync_history.csv
```

---

## 7. Node C Configuration (Best Practice)

**Node C (Fast)** - Symmetrical setup với Node B:
- **Initial offset**: +100ms (chạy nhanh, đối lập Node B)
- **Drift rate**: -10 ppm (tự chạy nhanh thêm)
- **Test duration**: 3 phút (để thấy rõ convergence)

### Rationale:
- Symmetrical setup kiểm chứng thuật toán hoạt động đúng với cả Fast/Slow
- 3 phút đủ để thấy: Slewing phase → Convergence
- Khác offset nhưng drift cùng dấu giống Node B

---

## 8. Tóm tắt Setup Cuối cùng

| Node | Initial Offset | Drift Rate | Ghi chú |
|------|--------|--------|---------|
| **Server A** | 10:00:00.000 | 0 ppm | Stratum 1 (Master) |
| **Node B** | -100ms | +10 ppm | Slow + Positive drift |
| **Node C** | +100ms | -10 ppm | Fast + Negative drift |

**Mục tiêu**: Sau ~3 phút, cả Node B & C đều sync về 10:00:00.000
