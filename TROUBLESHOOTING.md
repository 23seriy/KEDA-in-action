# Troubleshooting Guide

## Quick Diagnostics

Run these commands to get a snapshot of the demo state:

```bash
kubectl get pods -n keda-demo
kubectl get pods -n keda
kubectl get scaledobjects -n keda-demo
kubectl get hpa -n keda-demo
minikube status -p keda-demo
```

---

## Installation Issues

### Minikube Won't Start

**Symptom**: `minikube start` fails or hangs.

**Fix**:

```bash
# Check Docker Desktop is running
docker info

# Delete stale profile and retry
minikube delete -p keda-demo
./scripts/02-start-cluster.sh
```

**Cause**: Docker daemon not running, or a leftover profile from a previous run.

### Homebrew Tools Not Found

**Symptom**: `minikube`, `kubectl`, or `helm` not found after install script.

**Fix**:

```bash
# Reload shell
exec "$SHELL"

# Or re-run install
./scripts/01-install-prerequisites.sh
```

---

## Cluster & KEDA Issues

### KEDA Operator Not Ready

**Symptom**: `02-start-cluster.sh` times out waiting for KEDA pods.

**Fix**:

```bash
kubectl get pods -n keda
kubectl describe deployment keda-operator -n keda
kubectl get events -n keda --sort-by=.metadata.creationTimestamp | tail -n 30
```

Common causes:
- Insufficient memory — increase Minikube memory: `minikube start -p keda-demo --memory=8192`
- Image pull failure — check internet connectivity and Docker Hub rate limits

### keda-operator-metrics-apiserver Not Ready

**Symptom**: The metrics API server pod stays in `CrashLoopBackOff` or `Pending`.

**Fix**:

```bash
kubectl logs -n keda deploy/keda-operator-metrics-apiserver --tail=50
kubectl describe pod -n keda -l app=keda-operator-metrics-apiserver
```

If resources are insufficient, delete and recreate the cluster with more memory.

### Kubernetes Version Mismatch

**Symptom**: KEDA Helm install fails with API compatibility errors.

**Fix**:

```bash
minikube delete -p keda-demo
# The start script uses the correct K8s version
./scripts/02-start-cluster.sh
```

---

## Application Deployment Issues

### Docker Build Fails Inside Minikube

**Symptom**: `03-deploy-app.sh` errors during `docker build`.

**Fix**:

```bash
# Ensure you're using Minikube's Docker daemon
eval $(minikube docker-env -p keda-demo)

# Retry the build
docker build -t producer:latest apps/producer/
```

### Pods Stuck in ImagePullBackOff

**Symptom**: App pods show `ImagePullBackOff` or `ErrImagePull`.

**Fix**: The images must be built inside Minikube's Docker daemon, not the host's:

```bash
eval $(minikube docker-env -p keda-demo)
./scripts/03-deploy-app.sh
```

### Redis Not Reachable

**Symptom**: Producer logs show `ConnectionError` to Redis.

**Fix**:

```bash
kubectl get pods -n keda-demo -l app=redis
kubectl logs -n keda-demo deploy/redis --tail=20
```

Ensure Redis is running and the service name resolves:

```bash
kubectl exec -n keda-demo deploy/producer -- python -c "
import redis; r = redis.Redis(host='redis', port=6379); print(r.ping())
"
```

### RabbitMQ Not Reachable

**Symptom**: Rabbit-publisher job fails or rabbit-worker can't connect.

**Fix**:

```bash
kubectl get pods -n keda-demo -l app=rabbitmq
kubectl logs -n keda-demo deploy/rabbitmq --tail=20
```

Check the management UI:

```bash
kubectl port-forward svc/rabbitmq 15672:15672 -n keda-demo
# Open http://localhost:15672 — login: guest / guest
```

---

## Scaling Issues

### Workers Not Scaling Up

**Symptom**: Jobs are in the queue but no worker pods appear.

**Checklist**:

1. **KEDA operator running?**

   ```bash
   kubectl get pods -n keda
   ```

2. **ScaledObject applied?**

   ```bash
   kubectl get scaledobjects -n keda-demo
   kubectl describe scaledobject -n keda-demo
   ```

3. **HPA created?**

   ```bash
   kubectl get hpa -n keda-demo
   ```

4. **Queue has items?**

   ```bash
   kubectl exec -n keda-demo deploy/producer -- python -c "
   import redis; r = redis.Redis(host='redis', port=6379); print(r.llen('highlight-queue'))
   "
   ```

5. **KEDA operator logs**:

   ```bash
   kubectl logs -n keda deploy/keda-operator --tail=50
   ```

### Workers Not Scaling Down to Zero

**Symptom**: Workers stay running even with an empty queue.

**Cause**: Cooldown period hasn't elapsed, or jobs are still being processed.

**Fix**: Wait for the configured `cooldownPeriod` (check your ScaledObject YAML). Then:

```bash
kubectl get pods -n keda-demo -l app=worker
kubectl exec -n keda-demo deploy/producer -- python -c "
import redis; r = redis.Redis(host='redis', port=6379); print('Queue:', r.llen('highlight-queue'))
"
```

### HPA Shows Unknown Metrics

**Symptom**: `kubectl get hpa` shows `<unknown>` for current metrics.

**Fix**:

```bash
kubectl describe hpa -n keda-demo
kubectl logs -n keda deploy/keda-operator-metrics-apiserver --tail=50
```

Common cause: The KEDA metrics server hasn't scraped the trigger source yet. Wait 30-60 seconds and check again.

---

## Demo Scenario Issues

### Port-Forward Drops

**Symptom**: `localhost:9090` stops responding.

**Fix**: Restart port-forward:

```bash
kubectl port-forward svc/producer 9090:8080 -n keda-demo
```

Port-forwards can drop if the pod restarts or the connection is idle too long.

### Cron Scaler Not Activating

**Symptom**: Minimum replicas not maintained during the cron window.

**Fix**: Check that the timezone and schedule in `keda/scaledobject-cron-warm.yaml` match your current time:

```bash
date
kubectl describe scaledobject -n keda-demo
```

### Multiple ScaledObjects Conflicting

**Symptom**: Unexpected scaling behavior after switching scenarios.

**Fix**: Delete the previous ScaledObject before applying a new one:

```bash
kubectl delete scaledobjects --all -n keda-demo
kubectl apply -f keda/scaledobject-queue-5.yaml
```

---

## Teardown Issues

### Teardown Script Hangs

**Symptom**: `05-teardown.sh` hangs during namespace deletion.

**Fix**: Finalizers may block deletion:

```bash
kubectl get namespace keda-demo -o json | jq '.spec.finalizers = []' | kubectl replace --raw "/api/v1/namespaces/keda-demo/finalize" -f -
```

### Minikube Profile Not Deleted

**Symptom**: `minikube delete -p keda-demo` fails.

**Fix**:

```bash
minikube delete -p keda-demo --purge
```

---

## Collecting Diagnostics

If you need to file a bug report, collect:

```bash
echo "=== Minikube Status ==="
minikube status -p keda-demo

echo "=== KEDA Namespace ==="
kubectl get all -n keda

echo "=== Demo Namespace ==="
kubectl get all -n keda-demo

echo "=== ScaledObjects ==="
kubectl describe scaledobjects -n keda-demo

echo "=== HPAs ==="
kubectl describe hpa -n keda-demo

echo "=== KEDA Operator Logs ==="
kubectl logs -n keda deploy/keda-operator --tail=100

echo "=== Events ==="
kubectl get events -n keda-demo --sort-by=.metadata.creationTimestamp | tail -n 50
```

---

Still stuck? Open an [issue](https://github.com/23seriy/KEDA-in-action/issues) with your diagnostics output! ⚡
