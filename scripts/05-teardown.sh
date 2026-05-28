#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

PROFILE="keda-demo"

echo "============================================"
echo "  KEDA in Action — Teardown"
echo "============================================"
echo ""

read -p "This will delete the Minikube cluster '$PROFILE'. Continue? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Deleting demo namespace..."
    kubectl delete namespace keda-demo --ignore-not-found

    info "Uninstalling KEDA..."
    helm uninstall keda -n keda 2>/dev/null || true
    kubectl delete namespace keda --ignore-not-found

    info "Deleting Minikube cluster..."
    minikube delete -p "$PROFILE"

    info "Teardown complete!"
else
    warn "Teardown cancelled."
fi
