import json
import os
import random
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import pika
import redis

WORKER_BACKEND = os.environ.get("WORKER_BACKEND", "redis").lower()
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")
QUEUE_NAME = os.environ.get("QUEUE_NAME", "highlight-jobs")
WORKER_NAME = os.environ.get("HOSTNAME", "worker-unknown")
IDLE_SLEEP = float(os.environ.get("IDLE_SLEEP", "2"))
PREFETCH_COUNT = int(os.environ.get("PREFETCH_COUNT", "1"))


def resolve_redis_endpoint() -> tuple[str, int]:
    host_value = os.environ.get("REDIS_QUEUE_HOST") or os.environ.get("REDIS_HOST", "redis")
    port_value = os.environ.get("REDIS_QUEUE_PORT") or os.environ.get("REDIS_PORT", "6379")

    if isinstance(port_value, str) and "://" in port_value:
        parsed = urlparse(port_value)
        if parsed.hostname and parsed.port:
            return parsed.hostname, parsed.port

    return host_value, int(port_value)


def resolve_rabbitmq_endpoint() -> tuple[str, int]:
    host_value = os.environ.get("RABBITMQ_AMQP_HOST") or os.environ.get("RABBITMQ_HOST", "rabbitmq")
    port_value = os.environ.get("RABBITMQ_AMQP_PORT") or os.environ.get("RABBITMQ_PORT", "5672")

    if isinstance(port_value, str) and "://" in port_value:
        parsed = urlparse(port_value)
        if parsed.hostname and parsed.port:
            return parsed.hostname, parsed.port

    return host_value, int(port_value)


REDIS_HOST, REDIS_PORT = resolve_redis_endpoint()
RABBITMQ_HOST, RABBITMQ_PORT = resolve_rabbitmq_endpoint()

redis_client: redis.Redis | None = None


def log(message: str) -> None:
    print(f"[{datetime.now(timezone.utc).isoformat()}] [{WORKER_NAME}] {message}", flush=True)


def process_job(job: dict) -> None:
    declared = int(job.get("processing_time", 3))
    processing_time = max(1, declared + random.randint(0, 2))
    log(
        f"Started {job.get('kind')} for {job.get('player')} / {job.get('team')} "
        f"after {job.get('moment')} - processing for {processing_time}s"
    )
    time.sleep(processing_time)
    log(f"Finished job {job.get('job_id')}")


def process_rabbit_message(body: bytes) -> None:
    text = body.decode("utf-8")
    processing_time = max(2, 3 + random.randint(0, 2))
    log(f"Started recap-batch from RabbitMQ message '{text}' - processing for {processing_time}s")
    time.sleep(processing_time)
    log(f"Finished RabbitMQ message '{text}'")


def run_redis_worker() -> None:
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

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


def create_rabbit_connection() -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=30,
    )
    return pika.BlockingConnection(parameters)


def run_rabbit_worker() -> None:
    log(f"Worker started. Listening to RabbitMQ queue '{QUEUE_NAME}' on {RABBITMQ_HOST}:{RABBITMQ_PORT}")
    while True:
        connection = None
        try:
            connection = create_rabbit_connection()
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=PREFETCH_COUNT)

            for method_frame, _, body in channel.consume(QUEUE_NAME, inactivity_timeout=10):
                if method_frame is None:
                    log("No new RabbitMQ recap job received during polling window. Staying alive.")
                    time.sleep(IDLE_SLEEP)
                    break

                process_rabbit_message(body)
                channel.basic_ack(method_frame.delivery_tag)
        except Exception as exc:
            log(f"RabbitMQ worker connection failed: {exc}")
            time.sleep(IDLE_SLEEP)
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass


def main() -> None:
    if WORKER_BACKEND == "rabbitmq":
        run_rabbit_worker()
        return

    run_redis_worker()


if __name__ == "__main__":
    main()
