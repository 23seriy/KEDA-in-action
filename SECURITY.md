# Security Policy

## Scope

**KEDA in Action** is an educational project designed to run locally on Minikube. It is **not intended for production use**. The security considerations here focus on safe learning practices.

## Reporting a Vulnerability

If you discover a security issue:

1. **Do NOT open a public issue**
2. **Email** [sergei.olshanetski@gmail.com](mailto:sergei.olshanetski@gmail.com) with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
3. You will receive acknowledgment within **48 hours**
4. A fix will be prioritized based on severity

## What Counts as a Vulnerability

| Category | Example |
|---|---|
| **Credentials in code** | Hardcoded passwords, API keys, tokens |
| **Unsafe defaults** | Services exposed beyond localhost without warning |
| **Container issues** | Running as root unnecessarily, outdated base images |
| **Script issues** | Commands that could damage the host system |
| **Dependency issues** | Known CVEs in pinned Python packages |

## Security Best Practices — Demo Context

This project is a **local Minikube demo**. The following are intentional simplifications for learning:

- Redis runs without authentication (demo only)
- RabbitMQ uses default `guest`/`guest` credentials (demo only)
- Services use `ClusterIP` and are accessed via `kubectl port-forward`
- No TLS between internal services
- No network policies (the focus is autoscaling, not network security)

### If Adapting for Production

If you use these patterns beyond a local demo, you **must**:

1. Enable authentication on Redis and RabbitMQ
2. Use Kubernetes Secrets (or an external secret manager) for all credentials
3. Add NetworkPolicies to limit pod-to-pod traffic
4. Enable TLS for all service communication
5. Use non-root containers
6. Scan images regularly for CVEs
7. Enable RBAC with least-privilege roles
8. Use `TriggerAuthentication` with Secret-backed credentials (as demonstrated in the RabbitMQ scenario)

## Known Considerations

| Item | Status | Notes |
|---|---|---|
| Redis no-auth | By design | Demo simplification; document in README |
| RabbitMQ guest credentials | By design | Management UI accessible only via port-forward |
| Docker socket | Required | Minikube uses Docker driver |
| Host network | Not used | All traffic stays inside Minikube |

## Dependencies

Python packages are pinned in each app's `requirements.txt`. Check for updates periodically:

```bash
pip install pip-audit
pip-audit -r apps/producer/requirements.txt
pip-audit -r apps/worker/requirements.txt
pip-audit -r apps/rabbit-publisher/requirements.txt
```

## Supported Versions

| Version | Supported |
|---|---|
| Latest `main` | Yes |
| Older releases | Best effort |

---

Security questions? Email [sergei.olshanetski@gmail.com](mailto:sergei.olshanetski@gmail.com) ⚡
