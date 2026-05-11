#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

PROFILE="keda-demo"

echo "============================================"
echo "  KEDA in Action — Cluster Setup"
echo "============================================"
echo ""

if minikube status -p "$PROFILE" &> /dev/null; then
    info "Minikube cluster '$PROFILE' is already running"
else
    info "Starting Minikube cluster '$PROFILE'..."
    minikube start \
        --profile="$PROFILE" \
        --cpus=4 \
        --memory=6144 \
        --driver=docker \
        --kubernetes-version=v1.30.0
fi

info "Setting kubectl context to '$PROFILE'..."
kubectl config use-context "$PROFILE"

info "Adding KEDA Helm repository..."
helm repo add kedacore https://kedacore.github.io/charts >/dev/null 2>&1 || true
helm repo update >/dev/null

if helm list -n keda | grep -q '^keda '; then
    warn "KEDA Helm release already installed. Skipping install."
else
    info "Installing KEDA..."
    kubectl create namespace keda --dry-run=client -o yaml | kubectl apply -f -
    helm install keda kedacore/keda --namespace keda
fi

info "Waiting for KEDA operator to be ready..."
kubectl wait --for=condition=available deployment/keda-operator -n keda --timeout=180s
kubectl wait --for=condition=available deployment/keda-operator-metrics-apiserver -n keda --timeout=180s

echo ""
info "Cluster and KEDA are ready."
