#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
header() { echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }

PRODUCER_URL="http://localhost:9090"

wait_for_user() {
    echo ""
    echo -e "${YELLOW}Press Enter to continue...${NC}"
    read -r
}

submit_jobs() {
    local count=${1:-10}
    curl -s -X POST "$PRODUCER_URL/enqueue" \
      -H "Content-Type: application/json" \
      -d "{\"count\": $count, \"processing_time\": 5}" | python3 -m json.tool 2>/dev/null || true
}

show_status() {
    curl -s "$PRODUCER_URL/status" | python3 -m json.tool 2>/dev/null || true
}

publish_rabbit_jobs() {
    kubectl delete job rabbit-publisher -n keda-demo 2>/dev/null || true
    kubectl apply -f "$PROJECT_DIR/k8s/rabbit-publisher-job.yaml"
}

echo "============================================"
echo "  KEDA in Action — Demo Scenarios"
echo "============================================"
echo ""
echo "Make sure port-forward is running:"
echo "  kubectl port-forward svc/producer 9090:8080 -n keda-demo"
echo ""
echo "And in another terminal, watch worker pods:"
echo "  kubectl get pods -n keda-demo -l app=worker -w"
wait_for_user

header "Scenario 1: Queue-Based Scaling (threshold 5)"
kubectl delete scaledobject --all -n keda-demo 2>/dev/null || true
kubectl apply -f "$PROJECT_DIR/keda/scaledobject-queue-5.yaml"
info "Submitting 25 jobs..."
submit_jobs 25
echo ""
info "Current status:"
show_status
wait_for_user

header "Scenario 2: Conservative Scaling (threshold 20)"
kubectl delete scaledobject --all -n keda-demo 2>/dev/null || true
kubectl apply -f "$PROJECT_DIR/keda/scaledobject-queue-20.yaml"
info "Submitting 40 jobs..."
submit_jobs 40
echo ""
info "Observe that scaling is less aggressive."
wait_for_user

header "Scenario 3: Fast Polling"
kubectl delete scaledobject --all -n keda-demo 2>/dev/null || true
kubectl apply -f "$PROJECT_DIR/keda/scaledobject-fast-polling.yaml"
info "Submitting 20 jobs..."
submit_jobs 20
echo ""
info "This profile reacts faster to bursts and cools down faster too."
wait_for_user

header "Scenario 4: Cron Pre-Warm + Queue Trigger"
kubectl delete scaledobject --all -n keda-demo 2>/dev/null || true
kubectl apply -f "$PROJECT_DIR/keda/scaledobject-cron-warm.yaml"
info "ScaledObject applied. Cron window is weekdays 08:00-18:00 UTC."
info "Redis trigger still handles real backlog outside the warm baseline."
wait_for_user

header "Scenario 5: Scale to Zero"
info "Stop submitting jobs and watch workers scale back down after cooldown."
info "Useful command: kubectl get deploy worker -n keda-demo -w"
show_status
wait_for_user

header "Scenario 6: RabbitMQ Queue Scaling + TriggerAuthentication"
info "This scenario uses a separate rabbit-worker deployment so it does not conflict with the Redis-based worker."
info "Watch RabbitMQ consumers in another terminal: kubectl get pods -n keda-demo -l app=rabbit-worker -w"
kubectl apply -f "$PROJECT_DIR/keda/scaledobject-rabbitmq.yaml"
info "Publishing 30 recap jobs to RabbitMQ..."
publish_rabbit_jobs
echo ""
info "Useful commands:"
echo "  kubectl get scaledobject rabbit-worker-queue -n keda-demo"
echo "  kubectl get hpa -n keda-demo -w"
echo "  kubectl logs -n keda-demo deployment/rabbit-worker --tail=20"

echo ""
echo "============================================"
echo "  Demo Complete!"
echo "============================================"
echo ""
echo "Try more experiments:"
echo "  - Change listLength thresholds in the ScaledObject files"
echo "  - Increase processing_time in /enqueue payloads"
echo "  - Compare cooldown behavior across profiles"
