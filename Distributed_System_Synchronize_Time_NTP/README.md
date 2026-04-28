# NTP Time Synchronization - Distributed System Simulation (Web Dashboard)

## 📋 Tổng quan

Hệ thống mô phỏng **NTP (Network Time Protocol)** trong môi trường Distributed Systems sử dụng Docker Compose.

**Hệ thống gồm:**
- **Server A (Stratum 1)**: Thời gian chuẩn, phút xác tuyệt đối
- **Node B (Slow)**: Chậm -100ms, drift +10ppm
- **Node C (Fast)**: Nhanh +100ms, drift -10ppm

**Mục tiêu**: Cả Node B & C đều sync về thời gian chính xác của Server A trong ~3 phút.

---

## 🏗️ Project Structure

```
project/
├── main.py                      # Entry point
├── web_visualize.py             # Web dashboard visualization
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # Container image
├── requirements.txt            # Python dependencies
│
├── src/
│   ├── __init__.py
│   ├── ntp_clock.py           # Clock simulation with offset/drift
│   ├── ntp_protocol.py        # NTP protocol (RFC 5905 simplified)
│   ├── server.py              # NTP Server implementation
│   ├── client.py              # NTP Client implementation
│   └── logger.py              # Logging & CSV export
│
├── configs/
│   ├── server_config.json     # Server A configuration
│   ├── node_b_config.json     # Node B (Slow) configuration
│   └── node_c_config.json     # Node C (Fast) configuration
│
├── logs/                       # (Generated) Log files
│   ├── server_server_a.log
│   ├── client_node_b.log
│   └── client_node_c.log
│
└── results/                    # (Generated) CSV results
    ├── server_server_a.csv
    ├── client_node_b.csv
    └── client_node_c.csv
```

---

## 🚀 Quick Start

### 1. Run with Docker Compose

```bash
docker-compose up
```

Hệ thống sẽ:
- Khởi động Server A (Stratum 1)
- Node B & C bắt đầu NTP synchronization
- Chạy trong 3 phút (180 giây)
- Tạo ra logs và CSV results

### 2. Monitor with Visualization (in another terminal)

```bash
# Start web dashboard
python3 web_visualize.py

# Open browser
# http://localhost:8080 (or next available port if busy)
```

### 3. View Raw Logs

```bash
# Terminal 1: Watch server logs
docker-compose logs -f server_a

# Terminal 2: Watch client logs
docker-compose logs -f node_b node_c
```

---

## 📊 Kỳ vọng Kết quả

### Giai đoạn 1: Đo lường (Measurement)
- Node B/C gửi NTP request, Server A phản hồi
- Tính toán offset và delay

### Giai đoạn 2: Quyết định (Decision)
- |offset| < 128ms → Chọn **Slewing** (điều chỉnh mềm)
- Nạp tham số: Clock-Adjust, Drift-Compensation

### Giai đoạn 3: Điều chỉnh (Slewing)
- **Mỗi giây**: Áp dụng phase adjustment = offset / 64
- Offset giảm exponentially: $offset \times (63/64)^n$
- **Sau 1 phút**: ~38.8ms còn lại
- **Sau 3 phút**: ~5.8ms còn lại

### CSV Output Format

```
timestamp,node,event_type,current_time_ms,offset_ms,phase_adjustment_ms,...
2026-04-21T10:00:05.123,node_b,NTP_RESPONSE,1713686405123,-100.0000,0.0000,...
2026-04-21T10:00:06.124,node_b,SLEWING_TICK,1713686406124,-98.4375,1.5625,...
...
```

---

## 🔧 Configuration

### Server Config (`server_config.json`)
```json
{
  "node_name": "server_a",
  "initial_offset_ms": 0,
  "drift_rate_ppm": 0,
  "clock_adj": 1.0,
  "clock_phase": 6,
  "clock_max": 128.0
}
```

### Client Config (`node_b_config.json` / `node_c_config.json`)
```json
{
  "node_name": "node_b",
  "initial_offset_ms": -100,
  "drift_rate_ppm": 10,
  "clock_adj": 1.0,
  "clock_phase": 6,
  "clock_max": 128.0,
  "sync_interval": 5
}
```

**Parameters:**
- `initial_offset_ms`: Initial time difference (ms)
- `drift_rate_ppm`: Natural drift rate (parts per million)
- `clock_adj`: Adjustment interval (seconds)
- `clock_phase`: Phase divisor = 2^clock_phase (64 for 6)
- `clock_max`: Max acceptable offset before step adjustment
- `sync_interval`: NTP sync request interval (seconds)

---

## 📈 Visualization (Web Dashboard)

```bash
# Start simulation
docker compose up --build

# In another terminal
python3 web_visualize.py
```

Open browser at URL shown in terminal (e.g. `http://localhost:8080`, `http://localhost:8081`).

### Features
- ✅ Line chart offset theo thời gian cho `node_b`, `node_c`, `server_a`
- ✅ Auto refresh mỗi 2 giây
- ✅ Hiển thị offset hiện tại của từng node
- ✅ Không cần thư viện ngoài

---

## 🧹 Removed Files (cleanup)

Các file cũ đã bỏ để gọn project:
- `visualize.py`
- `plot.py`
- `analyze.py`
- `FINAL_CHECKLIST.txt`
- `SETUP_SUMMARY.md`
- `QUICKSTART.sh`

---

## 📈 (Legacy section kept for history)

> Legacy terminal/ascii visualization đã được loại bỏ.

### Option 1️⃣: Real-time Terminal Visualization (Deprecated)
```bash
# Start simulation
docker-compose up &

# In another terminal - live monitoring (no dependencies!)
python3 web_visualize.py

# Or just summary after simulation ends
open http://localhost:8080
```

**Output:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              NTP TIME SYNCHRONIZATION VISUALIZATION                         ║
║            (Real-time monitoring of offset convergence)                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

⏱️  Elapsed: 45s / 180s

┌─ NODES STATUS ────────────────────────────────────────────────────────────┐
│ server_a   │  ────────────────●────────────────  +0.00ms │ ✓ SYNCED      │
│            │ Drift: +0.00ppm | Syncs:  126 | Slew: ✗
│                                                                            │
│ node_b     │  ●──────────────────────────────   -50.00ms │ ◑ ADJUSTING   │
│            │ Drift: +10.00ppm | Syncs:   10 | Slew: ✓
│                                                                            │
│ node_c     │  ──────────────────────────────●   +50.00ms │ ◑ ADJUSTING   │
│            │ Drift: -10.00ppm | Syncs:   10 | Slew: ✓
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Real-time progress bars
- ✅ Offset visualization
- ✅ No dependencies needed
- ✅ Live updates every 2 seconds
- ✅ Color-coded status (SYNCED, CONVERGING, ADJUSTING, SLEWING)

---

### Option 2️⃣: ASCII Chart Plot
```bash
# After simulation completes
echo "removed"
```

**Output:**
```
NODE_B:
────────────────────────────────────────────────────────────
 -100.00ms │█████████████████████████│
  -98.44ms │████████████████████████ │
  -96.90ms │████████████████████████ │
  ...
   -5.80ms │█                        │
────────────────────────────────────────────────────────────
Range: -100.00ms to -0.10ms
Samples: 180 (60 displayed)
```

---

### Option 3️⃣: Professional PNG Plot (with Matplotlib)
```bash
# Install matplotlib (optional)
pip install matplotlib

# Generate PNG plot
echo "removed"

# Or just ASCII fallback (no matplotlib needed)
echo "removed"
```

**Generates:**
- 📊 `results/ntp_synchronization_plot.png` (2 graphs)
  - Graph 1: Offset over time (convergence curve)
  - Graph 2: Adjustment count vs time

---

### Option 4️⃣: Detailed Statistics
```bash
echo "removed"
```

**Output:**
```
📊 NODE_B
   Initial offset:        -100.0000ms
   Final offset:          -5.8000ms
   Max offset:            -100.0000ms
   Min offset:            -0.0100ms
   Average adjustment:    1.5625ms
   Total slewing ticks:   180
   Convergence:           94.2%
   Time to <10ms:         ~60s
```

---

## 🔍 Key Concepts

### NTP 4-Timestamp Algorithm
```
t1 = Client send time
t2 = Server receive time
t3 = Server transmit time
t4 = Client receive time

delay = (t4 - t1) - (t3 - t2)
offset = ((t2 - t1) + (t3 - t4)) / 2
```

### Slewing vs Stepping
- **Slewing**: Smooth adjustment over time (offset < 128ms)
- **Stepping**: Immediate jump (offset > 128ms)

### Drift Compensation
- **Drift Rate**: Natural clock oscillation (ppm)
- **Compensation**: Apply negative drift to counteract
- Formula: `compensation_ppm = -drift_rate_ppm`

---

## 🧪 Troubleshooting

### Containers not connecting?
```bash
# Check network
docker network ls
docker network inspect <ntp_network>

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Empty logs?
```bash
# Check if containers are running
docker-compose ps

# View container logs
docker-compose logs server_a
```

### Sync failures?
- Increase `sync_interval` in config (default: 5s)
- Check network connectivity between containers
- Verify server is accepting connections on port 123

---

## 📝 Implementation Details

### Clock Simulation
- Uses `time.time()` for reference
- Applies offset in milliseconds
- Applies drift in ppm (parts per million)
- Each cycle: `current_time = reference + elapsed + offset + drift_effect`

### Network Layer
- `socket.AF_INET, socket.SOCK_DGRAM` (UDP)
- Custom NTP packet format (binary)
- Timeout: 3 seconds per request

### Threading
- **Main thread**: CLI interface
- **Server sync thread**: Listen for requests
- **Slewing thread**: Periodic adjustments every `clock_adj` seconds

---

## 📚 References

- [RFC 5905 - Network Time Protocol](https://tools.ietf.org/html/rfc5905)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [NTP Time Synchronization](https://en.wikipedia.org/wiki/Network_Time_Protocol)

---

## ✅ Validation Checklist

- [ ] Docker containers start successfully
- [ ] Server A accepts connections on port 123
- [ ] Node B/C send NTP requests every 5 seconds
- [ ] Offset decreases over time (exponential decay)
- [ ] CSV logs are generated for analysis
- [ ] After 3 minutes, offset < 10ms
- [ ] Slewing completes successfully

---

## 🔄 Next Steps

1. Run simulation: `docker-compose up`
2. Start web dashboard: `python3 web_visualize.py`
3. Open browser URL printed by script
4. Customize parameters in `configs/` for different scenarios

---

Generated: 2026-04-21 | Version: 1.0.0
