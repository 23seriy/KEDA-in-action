import json
import os
import time
from datetime import datetime

import redis
from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
QUEUE_NAME = os.environ.get("QUEUE_NAME", "highlight-jobs")
DEFAULT_BURST = int(os.environ.get("DEFAULT_BURST", "10"))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>KEDA in Action - NBA Edition</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
      color: #e2e8f0;
      min-height: 100vh;
      padding: 32px 16px;
    }
    .container {
      max-width: 920px;
      margin: 0 auto;
    }
    h1 {
      margin-bottom: 8px;
      font-size: 2.4rem;
      background: linear-gradient(135deg, #a78bfa, #22d3ee);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .subtitle {
      color: #cbd5e1;
      margin-bottom: 24px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }
    .card {
      background: rgba(15, 23, 42, 0.72);
      border: 1px solid rgba(148, 163, 184, 0.18);
      border-radius: 16px;
      padding: 20px;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.25);
    }
    .metric {
      font-size: 2rem;
      font-weight: 800;
      margin-top: 8px;
      color: #f8fafc;
    }
    button {
      border: none;
      border-radius: 12px;
      padding: 12px 18px;
      cursor: pointer;
      color: white;
      font-weight: 700;
      margin-right: 10px;
      margin-bottom: 10px;
      background: linear-gradient(135deg, #8b5cf6, #06b6d4);
    }
    button.secondary {
      background: linear-gradient(135deg, #475569, #334155);
    }
    pre {
      background: #020617;
      border-radius: 12px;
      padding: 16px;
      overflow-x: auto;
      color: #cbd5e1;
    }
    .footer {
      color: #94a3b8;
      margin-top: 16px;
      font-size: 0.95rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🏀 KEDA in Action - NBA Edition</h1>
    <p class="subtitle">An NBA-flavored autoscaling playground powered by Redis, Python, and KEDA.</p>

    <div class="grid">
      <div class="card">
        <div>Current highlight queue</div>
        <div class="metric" id="queueLength">-</div>
      </div>
      <div class="card">
        <div>Basketball jobs queued</div>
        <div class="metric" id="queuedJobs">-</div>
      </div>
      <div class="card">
        <div>Suggested next step</div>
        <div style="margin-top:8px;color:#cbd5e1">Submit a game-night burst, then watch `kubectl get pods -n keda-demo -w`.</div>
      </div>
    </div>

    <div class="card">
      <button onclick="submitOne()">Submit 1 highlight job</button>
      <button onclick="submitBurst(10)">Submit 10 highlight jobs</button>
      <button onclick="submitBurst(50)">Submit 50 highlight jobs</button>
      <button class="secondary" onclick="refreshStatus()">Refresh status</button>
      <pre id="statusBox">Loading status...</pre>
    </div>

    <div class="footer">
      Queue name: <strong>highlight-jobs</strong> | Status endpoint: <code>/status</code> | Enqueue endpoint: <code>/enqueue</code>
    </div>
  </div>

  <script>
    async function refreshStatus() {
      const response = await fetch('/status');
      const data = await response.json();
      document.getElementById('queueLength').textContent = data.queue_length;
      document.getElementById('queuedJobs').textContent = data.queued_now;
      document.getElementById('statusBox').textContent = JSON.stringify(data, null, 2);
    }

    async function submitOne() {
      await fetch('/enqueue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count: 1, processing_time: 4 })
      });
      await refreshStatus();
    }

    async function submitBurst(count) {
      await fetch('/enqueue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count, processing_time: 5 })
      });
      await refreshStatus();
    }

    refreshStatus();
    setInterval(refreshStatus, 4000);
  </script>
</body>
</html>
"""


def build_job(processing_time: int) -> dict:
    now = datetime.utcnow().isoformat() + "Z"
    return {
        "job_id": f"job-{int(time.time() * 1000)}",
        "submitted_at": now,
        "processing_time": processing_time,
        "kind": "highlight-package",
        "priority": "playoff-push",
        "team": "Lakers",
        "player": "Luka Doncic",
        "moment": "fourth-quarter run",
    }


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "producer"})


@app.route("/enqueue", methods=["POST"])
def enqueue():
    payload = request.get_json(silent=True) or {}
    count = max(1, int(payload.get("count", 1)))
    processing_time = max(1, int(payload.get("processing_time", 3)))

    created = []
    for _ in range(count):
        job = build_job(processing_time)
        redis_client.lpush(QUEUE_NAME, json.dumps(job))
        created.append(job["job_id"])

    return jsonify({
        "queued": len(created),
        "job_ids": created[:5],
        "queue_name": QUEUE_NAME,
        "queue_length": redis_client.llen(QUEUE_NAME),
    })


@app.route("/status")
def status():
    queue_length = redis_client.llen(QUEUE_NAME)
    recent_jobs = redis_client.lrange(QUEUE_NAME, 0, 4)

    return jsonify({
        "service": "producer",
        "queue_name": QUEUE_NAME,
        "queue_length": queue_length,
        "recent_jobs": [json.loads(item) for item in recent_jobs],
        "queued_now": queue_length,
        "default_burst": DEFAULT_BURST,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
