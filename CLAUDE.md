# CLAUDE.md — KEDA in Action

## Project Overview

Hands-on demo of **KEDA (Kubernetes Event-Driven Autoscaling)** on a local Minikube cluster. Uses a basketball media ingestion service with Redis and RabbitMQ queues to demonstrate scaling from zero to many replicas based on real queue demand.

## Tech Stack

- **Apps**: Python 3.12 / Flask (producer, worker, rabbit-publisher)
- **Platform**: Minikube (profile: `keda-demo`, Kubernetes 1.35+)
- **Tool**: KEDA 2.16 operator (installed via Helm)
- **Queues**: Redis (highlight-queue), RabbitMQ (recap-jobs)
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
.github/               # CI workflows, issue/PR templates, governance, dependabot
CONTRIBUTING.md        # Contribution guidelines and development workflow
SECURITY.md            # Security policy and responsible disclosure
TESTING.md             # Automated and manual testing guide
TROUBLESHOOTING.md     # Common issues and diagnostic commands
CODE_OF_CONDUCT.md     # Contributor Covenant
CHANGELOG.md           # Release history (Keep a Changelog format)
```

## Scripts Convention

All scripts are in `scripts/` and numbered sequentially:

| Script | Purpose |
|---|---|
| `01-install-prerequisites.sh` | Install minikube, kubectl, helm via Homebrew |
| `02-start-cluster.sh` | Create Minikube cluster, install KEDA via Helm |
| `03-deploy-app.sh` | Build images, deploy Redis, RabbitMQ, producer, workers |
| `04-demo-scenarios.sh` | Interactive walkthrough of scaling scenarios |
| `05-teardown.sh` | Destroy cluster (has confirmation prompt) |

Scripts use `#!/usr/bin/env bash` and `set -euo pipefail`.

## Key Concepts

- **ScaledObject** in `keda/` defines how KEDA scales deployments based on triggers
- **Redis trigger**: scales workers based on list length (`highlight-queue`)
- **RabbitMQ trigger**: scales workers based on AMQP queue depth (`recap-jobs`)
- **TriggerAuthentication**: injects credentials from Kubernetes Secrets
- **Cron trigger**: pre-warms replicas on a schedule
- **Scale to zero**: no idle resources when queue is empty
- **Polling interval / cooldown**: control reaction speed and flapping
- Producer web UI shows real-time queue depth and HPA status (inline HTML in `app.py`)

## Conventions

- All Kubernetes resources use the `keda-demo` namespace; KEDA operator runs in `keda` namespace
- Shell scripts: `#!/usr/bin/env bash` + `set -euo pipefail`
- Colored output helpers: `info()`, `ok()`, `warn()`, `fail()`
- Emoji prefixes in script output for readability (⚡, ✅, 🗑️)
- Python apps: Flask, pinned deps in requirements.txt, `os.getenv()` config
- Docker images are built locally in Minikube's Docker daemon (no registry push)
- YAML: 2-space indent, `yamllint -d relaxed` compliant
- Commit messages: `[type] description`
- CI: shellcheck, yamllint, hadolint, flake8, black, markdownlint
