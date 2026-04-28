"""
Simple web dashboard for NTP sync visualization.
Run: python3 web_visualize.py
Open: http://localhost:8080
"""

import csv
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

RESULTS_DIR = Path("results")


def read_node_series(csv_path: Path):
    if not csv_path.exists():
        return []

    points = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        idx = 0
        for row in reader:
            if row.get("event_type") != "SLEWING_TICK":
                continue
            try:
                points.append({
                    "x": idx,
                    "offset": float(row.get("offset_ms", 0.0)),
                    "slew": int(row.get("is_slewing", "0")),
                    "events": int(row.get("adjustment_count", "0")),
                })
                idx += 1
            except ValueError:
                continue
    return points


def build_payload():
    node_b = read_node_series(RESULTS_DIR / "client_node_b.csv")
    node_c = read_node_series(RESULTS_DIR / "client_node_c.csv")
    server = read_node_series(RESULTS_DIR / "server_server_a.csv")

    latest = {
        "node_b": node_b[-1]["offset"] if node_b else None,
        "node_c": node_c[-1]["offset"] if node_c else None,
        "server_a": server[-1]["offset"] if server else 0.0,
    }

    return {
        "node_b": node_b,
        "node_c": node_c,
        "server_a": server,
        "latest": latest,
    }


HTML = """<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>NTP Simple Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    .row { display: flex; gap: 12px; margin-bottom: 16px; }
    .card { padding: 10px 14px; border: 1px solid #ddd; border-radius: 8px; min-width: 180px; }
    .title { font-weight: 700; margin-bottom: 6px; }
    #chart { border: 1px solid #ddd; border-radius: 8px; width: 100%; max-width: 980px; height: 420px; }
    .note { margin-top: 8px; color: #666; }
  </style>
</head>
<body>
  <h2>NTP Synchronization Dashboard</h2>
  <div class=\"row\">
    <div class=\"card\"><div class=\"title\">Node B offset</div><div id=\"b\">-</div></div>
    <div class=\"card\"><div class=\"title\">Node C offset</div><div id=\"c\">-</div></div>
    <div class=\"card\"><div class=\"title\">Server offset</div><div id=\"s\">-</div></div>
  </div>
  <canvas id=\"chart\" width=\"980\" height=\"420\"></canvas>
  <div class=\"note\">Auto refresh every 2s. Y axis: offset (ms), X axis: tick.</div>

<script>
const canvas = document.getElementById('chart');
const ctx = canvas.getContext('2d');

function drawAxes(minY, maxY) {
  ctx.strokeStyle = '#bbb';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(50, 20); ctx.lineTo(50, 380); ctx.lineTo(940, 380); ctx.stroke();

  const zeroY = mapY(0, minY, maxY);
  ctx.strokeStyle = '#ddd';
  ctx.beginPath();
  ctx.moveTo(50, zeroY); ctx.lineTo(940, zeroY); ctx.stroke();

  ctx.fillStyle = '#666';
  ctx.fillText('0 ms', 10, zeroY + 4);
}

function mapX(x, maxX) {
  if (maxX <= 0) return 50;
  return 50 + (x / maxX) * 890;
}

function mapY(y, minY, maxY) {
  if (maxY === minY) return 200;
  return 380 - ((y - minY) / (maxY - minY)) * 360;
}

function drawSeries(series, color, minY, maxY, maxX) {
  if (!series || series.length === 0) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  series.forEach((p, i) => {
    const x = mapX(p.x, maxX);
    const y = mapY(p.offset, minY, maxY);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
}

function render(data) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const all = [...data.node_b, ...data.node_c, ...data.server_a].map(p => p.offset);
  let minY = all.length ? Math.min(...all) : -100;
  let maxY = all.length ? Math.max(...all) : 100;
  if (Math.abs(minY - maxY) < 1) { minY -= 5; maxY += 5; }
  minY -= 5; maxY += 5;

  const maxX = Math.max(
    data.node_b.length - 1,
    data.node_c.length - 1,
    data.server_a.length - 1,
    1
  );

  drawAxes(minY, maxY);
  drawSeries(data.server_a, '#666', minY, maxY, maxX);
  drawSeries(data.node_b, '#1f77b4', minY, maxY, maxX);
  drawSeries(data.node_c, '#d62728', minY, maxY, maxX);

  ctx.fillStyle = '#1f77b4'; ctx.fillText('Node B', 860, 30);
  ctx.fillStyle = '#d62728'; ctx.fillText('Node C', 860, 50);
  ctx.fillStyle = '#666'; ctx.fillText('Server', 860, 70);

  document.getElementById('b').textContent = data.latest.node_b == null ? '-' : data.latest.node_b.toFixed(2) + ' ms';
  document.getElementById('c').textContent = data.latest.node_c == null ? '-' : data.latest.node_c.toFixed(2) + ' ms';
  document.getElementById('s').textContent = data.latest.server_a == null ? '-' : data.latest.server_a.toFixed(2) + ' ms';
}

async function refresh() {
  const res = await fetch('/data');
  const data = await res.json();
  render(data);
}

refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/data":
            payload = json.dumps(build_payload()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        self.send_response(404)
        self.end_headers()


def main():
  base_port = 8080
  if len(sys.argv) > 1:
    try:
      base_port = int(sys.argv[1])
    except ValueError:
      print("Invalid port. Using default 8080.")

  for port in range(base_port, base_port + 20):
    try:
      server = HTTPServer(("0.0.0.0", port), Handler)
      print(f"Web dashboard: http://localhost:{port}")
      server.serve_forever()
      return
    except OSError as e:
      if e.errno == 98:
        continue
      raise

  raise RuntimeError(
    f"No available port found in range {base_port}-{base_port + 19}."
  )


if __name__ == "__main__":
    main()
