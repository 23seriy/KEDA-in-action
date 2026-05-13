#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }

PROFILE="keda-demo"

echo "============================================"
echo "  KEDA in Action — Deploy Application"
echo "============================================"
echo ""

info "Configuring Docker to use Minikube's daemon..."
eval $(minikube -p "$PROFILE" docker-env)

info "Building producer image..."
docker build -t keda-demo/producer:latest "$PROJECT_DIR/apps/producer"

info "Building worker image..."
docker build -t keda-demo/worker:latest "$PROJECT_DIR/apps/worker"

info "Building RabbitMQ publisher image..."
docker build -t keda-demo/rabbit-publisher:latest "$PROJECT_DIR/apps/rabbit-publisher"

info "Creating namespace..."
kubectl apply -f "$PROJECT_DIR/k8s/namespace.yaml"

info "Deploying Redis..."
kubectl apply -f "$PROJECT_DIR/k8s/redis.yaml"

info "Deploying RabbitMQ..."
kubectl apply -f "$PROJECT_DIR/k8s/rabbitmq.yaml"

info "Deploying producer RBAC..."
kubectl apply -f "$PROJECT_DIR/k8s/producer-rbac.yaml"

info "Deploying producer..."
kubectl apply -f "$PROJECT_DIR/k8s/producer.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/producer-service.yaml"

info "Deploying worker deployment..."
kubectl apply -f "$PROJECT_DIR/k8s/worker-deployment.yaml"

info "Deploying RabbitMQ worker deployment..."
kubectl apply -f "$PROJECT_DIR/k8s/rabbit-worker-deployment.yaml"

info "Restarting deployments so rebuilt images are picked up..."
kubectl rollout restart deployment/producer -n keda-demo
kubectl rollout restart deployment/worker -n keda-demo
kubectl rollout restart deployment/rabbit-worker -n keda-demo

info "Applying default KEDA scaler..."
kubectl delete scaledobject --all -n keda-demo 2>/dev/null || true
kubectl apply -f "$PROJECT_DIR/keda/scaledobject-queue-5.yaml"

info "Waiting for Redis, RabbitMQ, and producer to be ready..."
kubectl wait --for=condition=available deployment/redis -n keda-demo --timeout=180s
kubectl wait --for=condition=available deployment/rabbitmq -n keda-demo --timeout=180s
kubectl wait --for=condition=available deployment/producer -n keda-demo --timeout=180s
kubectl rollout status deployment/producer -n keda-demo --timeout=180s
kubectl rollout status deployment/worker -n keda-demo --timeout=180s || true
kubectl rollout status deployment/rabbit-worker -n keda-demo --timeout=180s || true

echo ""
info "Application deployed successfully!"
echo ""
kubectl get pods -n keda-demo
echo ""
echo "Access the producer API with:"
echo "  kubectl port-forward svc/producer 9090:8080 -n keda-demo"
echo ""
echo "Next step: ./scripts/04-demo-scenarios.sh"
