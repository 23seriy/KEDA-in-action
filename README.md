# ⚡ KEDA in Action

A hands-on project for learning **KEDA (Kubernetes Event-Driven Autoscaling)** on your laptop with Minikube. Instead of scaling on CPU alone, this project scales worker pods based on **real queue demand**.

The demo uses a small basketball media ingestion service, a Redis-backed queue, and a worker deployment that KEDA scales from **zero to many replicas** depending on backlog. Think of it like an NBA content pipeline reacting to game-night spikes: highlight clipping requests, box score updates, and social-ready stat cards.

![KEDA](https://img.shields.io/badge/KEDA-2.16-7B61FF?logo=kubernetes&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-1.30-326CE5?logo=kubernetes&logoColor=white)
![Minikube](https://img.shields.io/badge/Minikube-local-F7B93E?logo=kubernetes&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)

> 📝 **Included in this repo:** a Medium-style story draft at `docs/medium-story.md`

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
                 └──────────────────────────────────────────┘
```

## 📋 What You'll Learn

| KEDA Concept | What It Does | Demo Scenario |
|---|---|---|
| **Scale to Zero** | Runs no workers when there is no work | No live games, empty queue |
| **Redis Scaler** | Scales from queue depth | Highlight backlog after tip-off |
| **Polling Interval** | Controls how often KEDA checks the trigger | Faster vs calmer game-night reactions |
| **Cooldown Period** | Controls scale-down delay | Prevent flapping after scoring bursts |
| **Min/Max Replicas** | Bounds autoscaling | Cost vs responsiveness for fan traffic |
| **Cron Scaling** | Pre-warms capacity on schedule | Pregame warm-up before evening slate |
| **Operational Visibility** | Observe queue depth and pod count | kubectl + status endpoint |

## 🚀 Quick Start

### Prerequisites

- **macOS**
- **Docker Desktop** running
- **Homebrew** installed
- ~6 GB RAM available for Minikube

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

This creates a Minikube profile called `keda-demo`, installs KEDA with Helm, and waits for the operator to be ready.

### Step 3: Build & Deploy the Demo

```bash
./scripts/03-deploy-app.sh
```

This builds the producer and worker images directly inside Minikube's Docker daemon, deploys Redis and the app components, and applies the default KEDA scaler.

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

## 🔍 How the Demo Works

- **Producer API** receives job submissions and pushes messages to Redis.
- **Worker pods** pop jobs from Redis and simulate processing with variable durations.
- **KEDA** checks Redis list length and scales the worker deployment automatically.
- **Redis** is only the event source here; the key learning is that scaling follows business demand, not CPU averages.

## 📁 Project Structure

```text
keda-in-action/
├── apps/
│   ├── producer/
│   │   ├── app.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── worker/
│       ├── app.py
│       ├── Dockerfile
│       └── requirements.txt
├── docs/
│   └── medium-story.md
├── k8s/
│   ├── namespace.yaml
│   ├── redis.yaml
│   ├── producer.yaml
│   ├── producer-service.yaml
│   └── worker-deployment.yaml
├── keda/
│   ├── scaledobject-queue-5.yaml
│   ├── scaledobject-queue-20.yaml
│   ├── scaledobject-fast-polling.yaml
│   └── scaledobject-cron-warm.yaml
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
5. **KEDA complements Kubernetes** — it plugs into standard Deployments and HPAs instead of replacing them.

## 📚 Resources

- [KEDA Documentation](https://keda.sh/docs/latest/)
- [KEDA Scalers](https://keda.sh/docs/latest/scalers/)
- [Redis Lists](https://redis.io/docs/latest/develop/data-types/lists/)
- [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)

## 📝 License

MIT — Use freely for learning, demos, and presentations.
