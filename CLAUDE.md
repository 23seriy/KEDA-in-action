# CLAUDE.md — KEDA in Action

## Project Overview

Hands-on demo of **KEDA (Kubernetes Event-Driven Autoscaling)** on a local Minikube cluster. Uses a basketball media ingestion service with Redis and RabbitMQ queues to demonstrate scaling from zero to many replicas based on real queue demand.

## Tech Stack

- **Apps**: Python/Flask (producer, worker, rabbit-publisher)
- **Platform**: Minikube (profile: `keda-demo`)
- **Tool**: KEDA operator
- **Queues**: Redis, RabbitMQ
- **Container**: Docker (images built inside Minikube's Docker daemon)

## Project Structure

```
apps/                  # Application source code
  producer/            # Web UI + API that pushes jobs to Redis queue
  worker/              # Consumes jobs from Redis queue
  rabbit-publisher/    # Publishes messages to RabbitMQ
k8s/                   # Base Kubernetes manifests
  redis.yaml           # Redis deployment
  rabbitmq.yaml        # RabbitMQ deployment
  producer.yaml        # Producer deployment + service
  worker-deployment.yaml       # Worker deployment (scaled by KEDA)
  rabbit-worker-deployment.yaml # RabbitMQ worker (scaled by KEDA)
  producer-rbac.yaml   # RBAC for producer to read HPA status
keda/                  # KEDA ScaledObject definitions
  scaledobject-queue-5.yaml      # Scale at 5 messages/replica
  scaledobject-queue-20.yaml     # Scale at 20 messages/replica
  scaledobject-fast-polling.yaml # Fast polling interval
  scaledobject-cron-warm.yaml    # Cron-based warm pool
  scaledobject-rabbitmq.yaml     # RabbitMQ trigger
scripts/               # Numbered automation scripts (01–05)
```

## Scripts Convention

All scripts are in `scripts/` and numbered sequentially:
- `01-install-prerequisites.sh` — Installs minikube, kubectl via Homebrew
- `02-start-cluster.sh` — Creates Minikube cluster and installs KEDA via Helm
- `03-deploy-app.sh` — Builds images, deploys Redis, RabbitMQ, producer, workers
- `04-demo-scenarios.sh` — Interactive walkthrough of scaling scenarios
- `05-teardown.sh` — Destroys cluster (has confirmation prompt)

Scripts use `#!/usr/bin/env bash` and `set -euo pipefail`.

## Key Concepts

- **ScaledObject** in `keda/` defines how KEDA scales deployments based on triggers
- **Redis trigger**: scales workers based on queue length (`myqueue` list length)
- **RabbitMQ trigger**: scales workers based on message count
- **Cron trigger**: pre-warms replicas on a schedule
- Producer web UI shows real-time queue depth and HPA status (inline HTML in `app.py`)
- Workers scale from **zero** — no idle resources when queue is empty

## Conventions

- All Kubernetes resources use the `keda-demo` namespace
- KEDA operator runs in `keda` namespace
- Emoji prefixes in script output for readability (⚡, ✅, 🗑️)
- Docker images are built locally in Minikube's Docker daemon (no registry push)
