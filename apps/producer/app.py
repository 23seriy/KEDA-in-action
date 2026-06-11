import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import redis
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

def resolve_redis_endpoint() -> tuple[str, int]:
    host_value = os.environ.get("REDIS_QUEUE_HOST") or os.environ.get("REDIS_HOST", "redis")
    port_value = os.environ.get("REDIS_QUEUE_PORT") or os.environ.get("REDIS_PORT", "6379")

    if isinstance(port_value, str) and "://" in port_value:
        parsed = urlparse(port_value)
        if parsed.hostname and parsed.port:
            return parsed.hostname, parsed.port

    return host_value, int(port_value)

REDIS_HOST, REDIS_PORT = resolve_redis_endpoint()
QUEUE_NAME = os.environ.get("QUEUE_NAME", "highlight-jobs")
DEFAULT_BURST = int(os.environ.get("DEFAULT_BURST", "10"))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def build_job(processing_time: int) -> dict:
    now = datetime.now(timezone.utc).isoformat()
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
    return render_template("index.html")


@app.route("/health")
def health():
    try:
        redis_client.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    status = "healthy" if redis_ok else "degraded"
    code = 200 if redis_ok else 503
    return jsonify({"status": status, "service": "producer", "redis": redis_ok}), code


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


def get_worker_pod_count() -> int | None:
    """Query the Kubernetes API for running worker pods (works inside the cluster)."""
    try:
        import urllib.request
        import ssl

        token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
        ca_path = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        ns_path = "/var/run/secrets/kubernetes.io/serviceaccount/namespace"

        with open(token_path) as f:
            token = f.read().strip()
        with open(ns_path) as f:
            namespace = f.read().strip()

        ctx = ssl.create_default_context(cafile=ca_path)
        url = f"https://kubernetes.default.svc/apis/apps/v1/namespaces/{namespace}/deployments/worker"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, context=ctx, timeout=3) as resp:
            data = json.loads(resp.read())
            return data.get("status", {}).get("readyReplicas", 0)
    except Exception:
        return None


@app.route("/drain", methods=["POST"])
def drain():
    removed = redis_client.llen(QUEUE_NAME)
    redis_client.delete(QUEUE_NAME)
    return jsonify({"drained": True, "removed": removed, "queue_name": QUEUE_NAME})


@app.route("/status")
def status():
    queue_length = redis_client.llen(QUEUE_NAME)
    recent_jobs = redis_client.lrange(QUEUE_NAME, 0, 4)
    worker_pods = get_worker_pod_count()

    result = {
        "service": "producer",
        "queue_name": QUEUE_NAME,
        "queue_length": queue_length,
        "recent_jobs": [json.loads(item) for item in recent_jobs],
        "queued_now": queue_length,
        "default_burst": DEFAULT_BURST,
    }
    if worker_pods is not None:
        result["worker_pods"] = worker_pods
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
