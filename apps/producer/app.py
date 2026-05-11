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
      background:
        radial-gradient(circle at top, rgba(249, 115, 22, 0.16), transparent 32%),
        linear-gradient(180deg, #1f2937 0%, #111827 55%, #0f172a 100%);
      color: #f8fafc;
      min-height: 100vh;
      padding: 32px 16px;
    }
    .container {
      max-width: 920px;
      margin: 0 auto;
    }
    .hero {
      position: relative;
      overflow: hidden;
      background: linear-gradient(135deg, rgba(30, 41, 59, 0.92), rgba(88, 28, 135, 0.72));
      border: 1px solid rgba(251, 146, 60, 0.28);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
      margin-bottom: 18px;
    }
    .hero::before {
      content: "";
      position: absolute;
      inset: auto -80px -80px auto;
      width: 240px;
      height: 240px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(249, 115, 22, 0.32), transparent 70%);
    }
    .eyebrow {
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(249, 115, 22, 0.12);
      border: 1px solid rgba(251, 146, 60, 0.28);
      color: #fdba74;
      font-size: 0.8rem;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 14px;
    }
    h1 {
      position: relative;
      margin: 0 0 8px;
      font-size: 2.6rem;
      background: linear-gradient(135deg, #fb923c, #facc15 45%, #38bdf8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .subtitle {
      position: relative;
      color: #dbeafe;
      margin: 0;
      max-width: 720px;
      line-height: 1.6;
    }
    .hero-grid {
      position: relative;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 18px;
    }
    .hero-stat {
      background: rgba(15, 23, 42, 0.72);
      border: 1px solid rgba(148, 163, 184, 0.2);
      border-radius: 16px;
      padding: 14px 16px;
    }
    .hero-stat-label {
      color: #94a3b8;
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      font-weight: 700;
    }
    .hero-stat-value {
      margin-top: 6px;
      color: #fef3c7;
      font-size: 1.1rem;
      font-weight: 800;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }
    .card {
      background: linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(17, 24, 39, 0.88));
      border: 1px solid rgba(148, 163, 184, 0.16);
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.28);
    }
    .card-title {
      color: #cbd5e1;
      font-size: 0.92rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      font-weight: 700;
    }
    .metric {
      font-size: 2.3rem;
      font-weight: 800;
      margin-top: 8px;
      color: #f8fafc;
    }
    .metric-note {
      margin-top: 8px;
      color: #94a3b8;
      line-height: 1.5;
    }
    .accent-orange {
      border-color: rgba(249, 115, 22, 0.28);
    }
    .accent-blue {
      border-color: rgba(56, 189, 248, 0.28);
    }
    .accent-gold {
      border-color: rgba(250, 204, 21, 0.28);
    }
    .controls {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 16px;
    }
    button {
      border: none;
      border-radius: 12px;
      padding: 12px 18px;
      cursor: pointer;
      color: white;
      font-weight: 700;
      box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
      transition: transform 0.15s ease, box-shadow 0.15s ease;
      background: linear-gradient(135deg, #f97316, #ea580c);
    }
    button:hover {
      transform: translateY(-1px);
      box-shadow: 0 14px 28px rgba(0, 0, 0, 0.32);
    }
    button.gold {
      background: linear-gradient(135deg, #f59e0b, #eab308);
      color: #111827;
    }
    button.blue {
      background: linear-gradient(135deg, #2563eb, #06b6d4);
    }
    button.secondary {
      background: linear-gradient(135deg, #475569, #334155);
    }
    pre {
      background: #020617;
      border: 1px solid rgba(148, 163, 184, 0.16);
      border-radius: 16px;
      padding: 16px;
      overflow-x: auto;
      color: #cbd5e1;
    }
    .footer {
      color: #94a3b8;
      margin-top: 16px;
      font-size: 0.95rem;
    }
    .section-title {
      margin: 0 0 14px;
      color: #f8fafc;
      font-size: 1.1rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="hero">
      <div class="eyebrow">Game Night Control Room</div>
      <h1>🏀 KEDA in Action - NBA Edition</h1>
      <p class="subtitle">Run a basketball-themed autoscaling demo where highlight requests hit Redis, KEDA watches the queue, and worker pods come off the bench exactly when the game gets hot.</p>
      <div class="hero-grid">
        <div class="hero-stat">
          <div class="hero-stat-label">Primary Queue</div>
          <div class="hero-stat-value">highlight-jobs</div>
        </div>
        <div class="hero-stat">
          <div class="hero-stat-label">Signal</div>
          <div class="hero-stat-value">Redis backlog</div>
        </div>
        <div class="hero-stat">
          <div class="hero-stat-label">Game Script</div>
          <div class="hero-stat-value">Luka + Lakers burst</div>
        </div>
      </div>
    </div>

    <div class="grid">
      <div class="card accent-orange">
        <div class="card-title">Current Highlight Queue</div>
        <div class="metric" id="queueLength">-</div>
        <div class="metric-note">Live scoreboard for pending highlight packages waiting to be processed.</div>
      </div>
      <div class="card accent-blue">
        <div class="card-title">Jobs in the Paint</div>
        <div class="metric" id="queuedJobs">-</div>
        <div class="metric-note">How much basketball content is stacked up for the worker rotation.</div>
      </div>
      <div class="card accent-gold">
        <div class="card-title">Coach's Call</div>
        <div style="margin-top:10px;color:#e2e8f0;line-height:1.6">Launch a 10 or 50 job scoring run, then watch <code>kubectl get pods -n keda-demo -w</code> as the worker bench checks into the game.</div>
      </div>
    </div>

    <div class="card">
      <h2 class="section-title">Send Basketball Workloads</h2>
      <div class="controls">
        <button onclick="submitOne()">🏀 Single fast-break job</button>
        <button class="gold" onclick="submitBurst(10)">🔥 10-job scoring run</button>
        <button class="blue" onclick="submitBurst(50)">🚨 50-job playoff surge</button>
        <button class="secondary" onclick="refreshStatus()">Refresh scoreboard</button>
      </div>
      <pre id="statusBox">Loading status...</pre>
    </div>

    <div class="footer">
      Queue name: <strong>highlight-jobs</strong> | Status endpoint: <code>/status</code> | Enqueue endpoint: <code>/enqueue</code> | Theme: <strong>NBA game-night autoscaling</strong>
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
