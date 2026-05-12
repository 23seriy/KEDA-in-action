#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

print_keda_diagnostics() {
    warn "KEDA metrics apiserver did not become ready in time. Collecting diagnostics..."
    echo ""
    kubectl get deployments -n keda || true
    echo ""
    kubectl get pods -n keda -o wide || true
    echo ""
    kubectl describe deployment keda-operator-metrics-apiserver -n keda || true
    echo ""
    kubectl get events -n keda --sort-by=.metadata.creationTimestamp | tail -n 30 || true
}

PROFILE="keda-demo"
TARGET_K8S_VERSION="v1.35.1"

echo "============================================"
echo "  KEDA in Action — Cluster Setup"
echo "============================================"
echo ""

if minikube status -p "$PROFILE" &> /dev/null; then
    info "Minikube cluster '$PROFILE' is already running"
    warn "This script expects Kubernetes ${TARGET_K8S_VERSION}. If this cluster was created earlier with an older version, recreate it with: minikube delete -p $PROFILE"
else
    info "Starting Minikube cluster '$PROFILE'..."
    minikube start \
        --profile="$PROFILE" \
        --cpus=4 \
        --memory=6144 \
        --driver=docker \
        --kubernetes-version="$TARGET_K8S_VERSION"
fi

info "Setting kubectl context to '$PROFILE'..."
kubectl config use-context "$PROFILE"

info "Adding KEDA Helm repository..."
helm repo add kedacore https://kedacore.github.io/charts >/dev/null 2>&1 || true
helm repo update >/dev/null

kubectl create namespace keda --dry-run=client -o yaml | kubectl apply -f -

if helm status keda -n keda >/dev/null 2>&1; then
    info "KEDA Helm release already exists. Reconciling with upgrade --install..."
else
    info "Installing KEDA..."
fi

helm upgrade --install keda kedacore/keda --namespace keda

info "Waiting for KEDA operator to be ready..."
kubectl wait --for=condition=available deployment/keda-operator -n keda --timeout=180s
if ! kubectl wait --for=condition=available deployment/keda-operator-metrics-apiserver -n keda --timeout=300s; then
    print_keda_diagnostics
    exit 1
fi

echo ""
info "Cluster and KEDA are ready."
