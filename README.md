# ⚡ KEDA in Action

A hands-on project for learning **KEDA (Kubernetes Event-Driven Autoscaling)** on your laptop with Minikube. Instead of scaling on CPU alone, this project scales worker pods based on **real queue demand**.

The demo uses a small basketball media ingestion service, a Redis-backed queue, a RabbitMQ recap pipeline, and worker deployments that KEDA scales from **zero to many replicas** depending on backlog. Think of it like an NBA content platform reacting to game-night spikes: highlight clipping requests, box score updates, recap batches, and social-ready stat cards.

![KEDA](https://img.shields.io/badge/KEDA-2.16-7B61FF?logo=kubernetes&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-1.30+-326CE5?logo=kubernetes&logoColor=white)
![Minikube](https://img.shields.io/badge/Minikube-local-F7B93E?logo=kubernetes&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)

> 📝 **Published article:** [KEDA in Action: Building Event-Driven Autoscaling Demos with Kubernetes, Redis, RabbitMQ, and an NBA Theme](https://medium.com/@sergeiolshanetski/keda-in-action-building-event-driven-autoscaling-demos-with-kubernetes-redis-rabbitmq-and-an-06f7dd7bd70c)

## 🏗️ Architecture

```text
                 ┌──────────────────────────────────────────┐
                 │              Minikube Cluster            │
                 │                                          │
 NBA Fan ─────►  │  Producer API ────────► Redis List       │
 localhost:9090 │      │                 highlight-queue    │
                 │      │                                   │
                 │      └──── submit game-night jobs        │
                 │                                          │
                 │               KEDA watches queue length  │
                 │                       │                  │
                 │                       ▼                  │
                 │        Highlight Worker Deployment       │
                 │        scales 0 → N based on backlog    │
                 │                                          │
                 │               KEDA watches queue length  │
                 │                       │                  │
                 │                       ▼                  │
                 │        RabbitMQ Worker Deployment       │
                 │        scales 0 → N based on backlog    │
                 └──────────────────────────────────────────┘
```

## 📋 What You'll Learn

| KEDA Concept | What It Does | Demo Scenario |
|---|---|---|
| **Scale to Zero** | Runs no workers when there is no work | No live games, empty queue |
| **Redis Scaler** | Scales from queue depth | Highlight backlog after tip-off |
| **RabbitMQ Scaler** | Scales from AMQP queue depth | Postgame recap burst after the final buzzer |
| **Polling Interval** | Controls how often KEDA checks the trigger | Faster vs calmer game-night reactions |
| **Cooldown Period** | Controls scale-down delay | Prevent flapping after scoring bursts |
| **Min/Max Replicas** | Bounds autoscaling | Cost vs responsiveness for fan traffic |
| **Cron Scaling** | Pre-warms capacity on schedule | Pregame warm-up before evening slate |
| **TriggerAuthentication** | Securely injects scaler connection details | RabbitMQ recap queue authentication |
| **Operational Visibility** | Observe queue depth and pod count | kubectl + status endpoint |

## 🚀 Quick Start

### Step 0: Clone the Repository

```bash
git clone https://github.com/23seriy/KEDA-in-action.git
cd keda-in-action
```

### Prerequisites

- **macOS**
- **Docker Desktop** running
- **Homebrew** installed
- ~6 GB RAM available for Minikube
- Minikube should run **Kubernetes 1.35+** for the current KEDA release used by this project

### Step 1: Install Tools

```bash
chmod +x scripts/*.sh
./scripts/01-install-prerequisites.sh
```

This installs or verifies `minikube`, `kubectl`, `helm`, and `docker`.

### Step 2: Start Cluster + Install KEDA

```bash
./scripts/02-start-cluster.sh
```

This creates a Minikube profile called `keda-demo` on **Kubernetes `v1.35.1`**, installs KEDA with Helm, and waits for the operator to be ready.

If you already created `keda-demo` earlier on an older Kubernetes version and see a KEDA compatibility warning, recreate the cluster:

```bash
minikube delete -p keda-demo
./scripts/02-start-cluster.sh
```

If the script times out waiting for `keda-operator-metrics-apiserver`, rerun it after checking the KEDA namespace status:

```bash
kubectl get pods -n keda
kubectl describe deployment keda-operator-metrics-apiserver -n keda
kubectl get events -n keda --sort-by=.metadata.creationTimestamp | tail -n 30
```

The setup script now prints these diagnostics automatically when that deployment does not become ready in time.

### Step 3: Build & Deploy the Demo

```bash
./scripts/03-deploy-app.sh
```

This builds the producer, shared worker, and RabbitMQ publisher images directly inside Minikube's Docker daemon, deploys Redis, RabbitMQ, and the app components, and applies the default Redis-based KEDA scaler.

If you change application code and rerun the deploy script, it now restarts the affected deployments so the rebuilt local images are picked up immediately.

### Step 4: Access the Producer API

In a separate terminal:

```bash
kubectl port-forward svc/producer 9090:8080 -n keda-demo
```

Then open:

- `http://localhost:9090/`
- `http://localhost:9090/status`

### Step 5: Run Guided Scenarios

```bash
./scripts/04-demo-scenarios.sh
```

## 🎮 Demo Scenarios

### 1. Baseline — Game-Night Queue Scaler with Threshold 5

```bash
kubectl apply -f keda/scaledobject-queue-5.yaml
```

KEDA starts workers only when backlog appears, and adds more pods as the queue grows. Imagine a close Lakers-Celtics game causing a rush of stat card and highlight requests.

### 2. More Conservative Scaling — Threshold 20

```bash
kubectl apply -f keda/scaledobject-queue-20.yaml
```

Workers scale less aggressively. Good for cost control if jobs are lightweight.

### 3. Fast Reaction Profile

```bash
kubectl apply -f keda/scaledobject-fast-polling.yaml
```

Uses tighter polling and shorter cooldown to react faster during spikes.

### 4. Cron Pre-Warm

```bash
kubectl apply -f keda/scaledobject-cron-warm.yaml
```

Keeps a minimum number of workers available during a scheduled window, useful when you know traffic patterns in advance.

### 5. Scale to Zero Verification

Stop sending jobs and watch the workers disappear after the cooldown period:

```bash
kubectl get pods -n keda-demo -l app=worker -w
```

### 6. RabbitMQ Queue Scaling + TriggerAuthentication

```bash
kubectl delete job rabbit-publisher -n keda-demo --ignore-not-found
kubectl apply -f keda/scaledobject-rabbitmq.yaml
kubectl apply -f k8s/rabbit-publisher-job.yaml
```

This independent path uses a dedicated `rabbit-worker` deployment, a RabbitMQ queue named `recap-jobs`, and a `TriggerAuthentication` backed by a Kubernetes Secret. It demonstrates how KEDA commonly integrates with authenticated external systems in production.

Helpful commands while the RabbitMQ demo is running:

```bash
kubectl get pods -n keda-demo -l app=rabbit-worker -w
kubectl get hpa -n keda-demo -w
kubectl logs -n keda-demo job/rabbit-publisher --tail=20
kubectl logs -n keda-demo deployment/rabbit-worker --tail=20
```

If you want to inspect RabbitMQ directly, open the management UI:

```bash
kubectl port-forward svc/rabbitmq 15672:15672 -n keda-demo
```

Then browse to `http://localhost:15672` and sign in with `guest` / `guest`.

## 🔍 How the Demo Works

- **Producer API** receives job submissions and pushes messages to Redis.
- **Worker pods** pop jobs from Redis and simulate processing with variable durations.
- **RabbitMQ publisher job** sends recap batches into an AMQP queue for a second demo track.
- **RabbitMQ worker pods** consume recap jobs when the RabbitMQ scaler decides more capacity is needed.
- **KEDA** checks Redis list length or RabbitMQ queue depth and scales the matching deployment automatically.
- **TriggerAuthentication** supplies RabbitMQ connection details through a Secret, mirroring a more production-like scaler setup.
- **Redis and RabbitMQ** are only event sources here; the key learning is that scaling follows business demand, not CPU averages.

## 📁 Project Structure

```text
keda-in-action/
├── apps/
│   ├── producer/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── rabbit-publisher/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── worker/
│       ├── app.py
│       ├── Dockerfile
│       └── requirements.txt
├── k8s/
│   ├── namespace.yaml
│   ├── redis.yaml
│   ├── rabbitmq.yaml
│   ├── rabbit-publisher-job.yaml
│   ├── producer.yaml
│   ├── producer-service.yaml
│   ├── producer-rbac.yaml
│   ├── worker-deployment.yaml
│   └── rabbit-worker-deployment.yaml
├── keda/
│   ├── scaledobject-queue-5.yaml
│   ├── scaledobject-queue-20.yaml
│   ├── scaledobject-fast-polling.yaml
│   ├── scaledobject-cron-warm.yaml
│   └── scaledobject-rabbitmq.yaml
└── scripts/
    ├── 01-install-prerequisites.sh
    ├── 02-start-cluster.sh
    ├── 03-deploy-app.sh
    ├── 04-demo-scenarios.sh
    └── 05-teardown.sh
```

## 🧹 Teardown

```bash
./scripts/05-teardown.sh
```

This deletes the namespace, uninstalls KEDA from the cluster, and removes the Minikube profile.

## 💡 Key Takeaways

1. **Event-driven scaling is more honest than CPU-only scaling** — backlog reflects actual user demand.
2. **Scale-to-zero reduces idle cost** — no workers needed when the queue is empty.
3. **Thresholds shape behavior** — low thresholds improve responsiveness, higher thresholds reduce churn.
4. **Cooldown and polling matter** — bad settings can cause slow reactions or noisy scaling.
5. **TriggerAuthentication matters in real systems** — external scalers often need credentials managed through Kubernetes resources.
6. **KEDA complements Kubernetes** — it plugs into standard Deployments and HPAs instead of replacing them.

## 📚 Resources

Versioning note:

- Python package versions in the demo apps are pinned for reproducibility.
- The project targets Kubernetes 1.30+ in Minikube (configurable in `02-start-cluster.sh`).
- The KEDA Helm chart and RabbitMQ container image are intentionally left easy to update — revalidate the demo flow when upgrading them.

- [KEDA Documentation](https://keda.sh/docs/latest/)
- [KEDA Scalers](https://keda.sh/docs/latest/scalers/)
- [Redis Lists](https://redis.io/docs/latest/develop/data-types/lists/)
- [RabbitMQ Scaler](https://keda.sh/docs/latest/scalers/rabbitmq-queue/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)

## 📝 License

MIT — Use freely for learning, demos, and presentations.
