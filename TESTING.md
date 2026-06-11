# Testing Guide

## Overview

KEDA in Action relies on local validation, shell script linting, YAML linting, and manual end-to-end scenario testing. This guide covers all testing approaches.

## Prerequisites

- Minikube running with the `keda-demo` profile
- KEDA installed and operator ready
- Demo deployed via `./scripts/03-deploy-app.sh`

## Automated Checks

### Shell Script Linting

```bash
shellcheck -x scripts/*.sh
```

All scripts must pass with zero warnings. The `.shellcheckrc` file disables `SC1091` for sourced-file resolution.

### YAML Validation

```bash
yamllint -d relaxed k8s/*.yaml
yamllint -d relaxed keda/*.yaml
```

### Python Syntax

```bash
python -m py_compile apps/producer/app.py
python -m py_compile apps/worker/app.py
python -m py_compile apps/rabbit-publisher/app.py
```

### Dockerfile Linting

```bash
hadolint apps/producer/Dockerfile
hadolint apps/worker/Dockerfile
hadolint apps/rabbit-publisher/Dockerfile
```

### Markdown Linting

```bash
npx markdownlint-cli2 "**/*.md" --config .markdownlint.json
```

## CI/CD (GitHub Actions)

The `.github/workflows/validate.yml` workflow runs on every push and PR to `main` or `develop`:

| Job | What It Checks |
|---|---|
| `shellcheck` | All `scripts/*.sh` pass shellcheck |
| `yaml-lint` | All K8s and KEDA YAML files pass yamllint |
| `docker-lint` | Dockerfiles pass hadolint |
| `docs-check` | Required documentation files exist |
| `script-syntax` | All scripts pass `bash -n` |
| `python-lint` | Python syntax, flake8, and black formatting |
| `markdown-lint` | All Markdown files pass markdownlint |

## Manual Scenario Testing

### Full Workflow Test

Run all scenarios end-to-end:

```bash
./scripts/01-install-prerequisites.sh
./scripts/02-start-cluster.sh
./scripts/03-deploy-app.sh
./scripts/04-demo-scenarios.sh
```

### Individual Scenario Tests

#### 1. Redis Queue Scaling (Threshold 5)

```bash
kubectl apply -f keda/scaledobject-queue-5.yaml
# Submit jobs via http://localhost:9090/
# Verify: workers scale up when queue > 5
kubectl get pods -n keda-demo -l app=worker -w
```

**Expected**: Workers scale from 0 to N as queue grows past 5.

#### 2. Redis Queue Scaling (Threshold 20)

```bash
kubectl apply -f keda/scaledobject-queue-20.yaml
# Submit a larger burst of jobs
# Verify: fewer workers than threshold-5 for the same load
```

**Expected**: More conservative scaling behavior.

#### 3. Fast Polling

```bash
kubectl apply -f keda/scaledobject-fast-polling.yaml
# Submit jobs and observe faster reaction time
```

**Expected**: Workers appear faster; shorter cooldown.

#### 4. Cron Pre-Warm

```bash
kubectl apply -f keda/scaledobject-cron-warm.yaml
# Check that minimum replicas are maintained during the cron window
kubectl get pods -n keda-demo -l app=worker
```

**Expected**: Minimum workers present during scheduled window.

#### 5. Scale to Zero

```bash
# Stop sending jobs, wait for cooldown
kubectl get pods -n keda-demo -l app=worker -w
```

**Expected**: Workers scale down to zero after cooldown period.

#### 6. RabbitMQ Queue Scaling

```bash
kubectl delete job rabbit-publisher -n keda-demo --ignore-not-found
kubectl apply -f keda/scaledobject-rabbitmq.yaml
kubectl apply -f k8s/rabbit-publisher-job.yaml

# Watch rabbit-worker pods
kubectl get pods -n keda-demo -l app=rabbit-worker -w
kubectl get hpa -n keda-demo -w
```

**Expected**: Rabbit-worker pods scale up to consume recap-jobs queue.

## Component Testing

### Redis Connectivity

```bash
kubectl exec -n keda-demo deploy/producer -- python -c "
import redis
r = redis.Redis(host='redis', port=6379)
print('PING:', r.ping())
print('Queue length:', r.llen('highlight-queue'))
"
```

### RabbitMQ Connectivity

```bash
kubectl port-forward svc/rabbitmq 15672:15672 -n keda-demo
# Open http://localhost:15672 — login: guest / guest
# Verify recap-jobs queue exists and message counts
```

### KEDA Operator Health

```bash
kubectl get pods -n keda
kubectl get scaledobjects -n keda-demo
kubectl get hpa -n keda-demo
```

### Producer API Health

```bash
kubectl port-forward svc/producer 9090:8080 -n keda-demo
curl -s http://localhost:9090/status | python -m json.tool
```

## Regression Testing

After any code change, verify:

1. Fresh cluster setup works: `02-start-cluster.sh` → `03-deploy-app.sh`
2. All six scenarios still behave as documented
3. Scale-to-zero works after cooldown
4. Teardown is clean: `05-teardown.sh`

## Debugging Failed Tests

### KEDA Operator Not Ready

```bash
kubectl get pods -n keda
kubectl describe deployment keda-operator -n keda
kubectl logs -n keda deploy/keda-operator --tail=50
```

### Workers Not Scaling

```bash
kubectl get scaledobjects -n keda-demo
kubectl describe scaledobject -n keda-demo
kubectl get hpa -n keda-demo
kubectl logs -n keda deploy/keda-operator --tail=50
```

### Jobs Stuck in Queue

```bash
kubectl exec -n keda-demo deploy/producer -- python -c "
import redis
r = redis.Redis(host='redis', port=6379)
print('Queue length:', r.llen('highlight-queue'))
for i in range(min(5, r.llen('highlight-queue'))):
    print(f'  Item {i}:', r.lindex('highlight-queue', i))
"
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more diagnostic guidance.

---

Questions about testing? Open an issue! ⚡
