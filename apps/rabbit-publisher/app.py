import os
import sys
import time

import pika

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")
QUEUE_NAME = os.environ.get("QUEUE_NAME", "recap-jobs")


def connect() -> pika.BlockingConnection:
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=30,
    )
    return pika.BlockingConnection(parameters)


def main() -> None:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    connection = connect()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    for index in range(1, count + 1):
        message = f"recap-job-{index}: Knicks-Celtics playoff pulse"
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=message.encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        print(f"Published {message}", flush=True)
        time.sleep(0.05)

    connection.close()
    print(f"Published {count} recap jobs to '{QUEUE_NAME}'", flush=True)


if __name__ == "__main__":
    main()
