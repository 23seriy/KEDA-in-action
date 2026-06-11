---
name: Bug Report
about: Report something that isn't working as expected
title: "[BUG] "
labels: bug
assignees: ''

---

## Description

<!-- A clear and concise description of what the bug is -->

## Steps to Reproduce

<!-- Exact steps to reproduce the behavior -->

1. Run `...`
2. Apply `...`
3. Observe `...`

## Expected Behavior

<!-- What should happen? -->

## Actual Behavior

<!-- What actually happens? -->

## Environment

- **OS**: <!-- e.g., macOS 14.0 -->
- **Minikube Version**: <!-- output of `minikube version` -->
- **Kubernetes Version**: <!-- output of `kubectl version --short` -->
- **KEDA Version**: <!-- output of `kubectl get deployment -n keda -o wide` -->
- **Docker Desktop Version**: <!-- if using Docker Desktop -->

## Error Messages or Logs

<!-- Paste any error messages or relevant log output -->

```
Paste logs here
```

## Additional Context

<!-- Any other context that might help us debug this? -->

## Diagnostics

<!-- Run these commands and share the output if applicable -->

```bash
kubectl get pods -n keda
kubectl get pods -n keda-demo
kubectl get scaledobjects -n keda-demo
kubectl logs -n keda deploy/keda-operator --tail=50
minikube logs -p keda-demo --tail=50
```
