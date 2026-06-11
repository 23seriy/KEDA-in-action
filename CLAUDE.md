# CLAUDE.md — KEDA in Action

## Project Overview

A hands-on KEDA (Kubernetes Event-Driven Autoscaling) demo running on Minikube. Demonstrates scaling worker pods based on real queue demand rather than CPU metrics, using an NBA basketball media ingestion theme.

## Tech Stack

- **Kubernetes** 1.35+ via Minikube (profile: `keda-demo`)
- **KEDA** 2.16 — event-driven autoscaler
- **Python** 3.12 — producer API, worker, rabbit-publisher
- **Redis** — highlight-queue (list-based trigger)
- **RabbitMQ** — recap-jobs queue (AMQP trigger + TriggerAuthentication)
- **Helm** — KEDA installation
- **Docker** — container builds inside Minikube's daemon

## Project Structure

```
keda-in-action/
├── apps/
│   ├── producer/         # Flask API — submits jobs to Redis
│   ├── worker/           # Shared worker — consumes Redis + RabbitMQ
│   └── rabbit-publisher/ # Job — publishes recap batches to RabbitMQ
├── k8s/                  # Kubernetes manifests (namespace, services, RBAC)
├── keda/                 # ScaledObject YAML variants
├── scripts/              # Setup, deploy, demo, teardown scripts
├── .github/              # CI workflows, issue/PR templates, governance
├── .dockerignore         # Docker build context exclusions
├── .shellcheckrc         # Shellcheck lint config
├── .markdownlint.json    # Markdown lint config
├── CONTRIBUTING.md       # Contribution guidelines
├── SECURITY.md           # Security policy
├── TESTING.md            # Testing guide
├── TROUBLESHOOTING.md    # Troubleshooting guide
├── CODE_OF_CONDUCT.md    # Contributor Covenant
├── CHANGELOG.md          # Release history
├── LICENSE               # MIT license
└── README.md             # Main documentation
```

## Scripts

| Script | Purpose |
|---|---|
| `01-install-prerequisites.sh` | Install/verify minikube, kubectl, helm, docker |
| `02-start-cluster.sh` | Create Minikube profile, install KEDA via Helm |
| `03-deploy-app.sh` | Build images in Minikube, deploy all components |
| `04-demo-scenarios.sh` | Interactive guided demo of all scaling scenarios |
| `05-teardown.sh` | Delete namespace, uninstall KEDA, remove profile |

## Key Concepts

- **ScaledObject** — KEDA CRD that binds a deployment to a trigger
- **Redis scaler** — scales based on list length (`highlight-queue`)
- **RabbitMQ scaler** — scales based on AMQP queue depth (`recap-jobs`)
- **TriggerAuthentication** — injects credentials from Kubernetes Secrets
- **Scale to zero** — workers disappear when queue is empty
- **Cron trigger** — pre-warm capacity on schedule
- **Polling interval / cooldown** — control reaction speed and flapping

## Conventions

- All Kubernetes resources use the `keda-demo` namespace; KEDA operator runs in `keda` namespace
- Docker images are built locally in Minikube's Docker daemon (no registry push)
- Shell scripts: `#!/usr/bin/env bash` + `set -euo pipefail`
- Colored output helpers: `info()`, `ok()`, `warn()`, `fail()`
- Python apps: Flask, pinned deps in requirements.txt, `os.getenv()` config
- YAML: 2-space indent, `yamllint -d relaxed` compliant
- Commit messages: `[type] description`
- CI: shellcheck, yamllint, hadolint, flake8, black, markdownlint
