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

info "Creating namespace..."
kubectl apply -f "$PROJECT_DIR/k8s/namespace.yaml"

info "Deploying Redis..."
kubectl apply -f "$PROJECT_DIR/k8s/redis.yaml"

info "Deploying producer..."
kubectl apply -f "$PROJECT_DIR/k8s/producer.yaml"
kubectl apply -f "$PROJECT_DIR/k8s/producer-service.yaml"

info "Deploying worker deployment..."
kubectl apply -f "$PROJECT_DIR/k8s/worker-deployment.yaml"

info "Applying default KEDA scaler..."
kubectl apply -f "$PROJECT_DIR/keda/scaledobject-queue-5.yaml"

info "Waiting for Redis and producer to be ready..."
kubectl wait --for=condition=available deployment/redis -n keda-demo --timeout=180s
kubectl wait --for=condition=available deployment/producer -n keda-demo --timeout=180s

echo ""
info "Application deployed successfully!"
echo ""
kubectl get pods -n keda-demo
echo ""
echo "Access the producer API with:"
echo "  kubectl port-forward svc/producer 9090:8080 -n keda-demo"
echo "Then open: http://localhost:9090"
echo ""
echo "Next step: ./scripts/04-demo-scenarios.sh"
