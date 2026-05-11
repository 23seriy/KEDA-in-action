import json
import os
import random
import time
from datetime import datetime

import redis

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
QUEUE_NAME = os.environ.get("QUEUE_NAME", "highlight-jobs")
WORKER_NAME = os.environ.get("HOSTNAME", "worker-unknown")
IDLE_SLEEP = float(os.environ.get("IDLE_SLEEP", "2"))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def log(message: str) -> None:
    print(f"[{datetime.utcnow().isoformat()}Z] [{WORKER_NAME}] {message}", flush=True)


def process_job(job: dict) -> None:
    declared = int(job.get("processing_time", 3))
    processing_time = max(1, declared + random.randint(0, 2))
    log(
        f"Started {job.get('kind')} for {job.get('player')} / {job.get('team')} "
        f"after {job.get('moment')} - processing for {processing_time}s"
    )
    time.sleep(processing_time)
    log(f"Finished job {job.get('job_id')}")


def main() -> None:
    log(f"Worker started. Listening to basketball queue '{QUEUE_NAME}' on {REDIS_HOST}:{REDIS_PORT}")
    while True:
        item = redis_client.brpop(QUEUE_NAME, timeout=10)
        if item is None:
            log("No new basketball content job received during blocking wait. Staying alive.")
            time.sleep(IDLE_SLEEP)
            continue

        _, raw_job = item
        try:
            job = json.loads(raw_job)
            process_job(job)
        except Exception as exc:
            log(f"Failed to process message: {exc}")


if __name__ == "__main__":
    main()
