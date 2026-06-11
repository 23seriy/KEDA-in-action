# Contributing to KEDA in Action

Thank you for your interest in improving this project! Whether you're fixing a bug, adding a new KEDA scenario, or improving documentation, this guide will help you get started.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:

   ```bash
   git clone https://github.com/<your-user>/KEDA-in-action.git
   cd KEDA-in-action
   ```

3. **Create a branch** from `main`:

   ```bash
   git checkout -b feature/my-change
   ```

4. **Install prerequisites** — see [README.md](README.md) Quick Start.

## Development Workflow

### 1. Make Changes

- Edit scripts, YAML manifests, or Python application code
- Keep changes focused — one logical change per PR

### 2. Test Locally

```bash
# Start cluster and deploy
./scripts/02-start-cluster.sh
./scripts/03-deploy-app.sh

# Run through scenarios
./scripts/04-demo-scenarios.sh
```

See [TESTING.md](TESTING.md) for the full testing guide.

### 3. Validate

```bash
# Lint shell scripts
shellcheck -x scripts/*.sh

# Lint YAML
yamllint -d relaxed k8s/*.yaml keda/*.yaml

# Check Python syntax
python -m py_compile apps/producer/app.py
python -m py_compile apps/worker/app.py
python -m py_compile apps/rabbit-publisher/app.py
```

### 4. Commit and Push

```bash
git add .
git commit -m "[type] description of change"
git push origin feature/my-change
```

### 5. Open a Pull Request

- Use the PR template
- Reference any related issues
- Describe what changed and why

## Commit Message Conventions

Use the format `[type] description`:

| Prefix | Usage |
|---|---|
| `[feat]` | New feature, scenario, or scaler |
| `[fix]` | Bug fix |
| `[docs]` | Documentation only |
| `[refactor]` | Code change with no behavior change |
| `[ci]` | CI/CD changes |
| `[deps]` | Dependency updates |
| `[improve]` | General improvement |

## Shell Script Standards

All scripts in `scripts/` must:

1. **Use** `#!/usr/bin/env bash` as the shebang
2. **Set** `set -euo pipefail` immediately after
3. **Pass** `shellcheck -x` with no errors
4. **Use helper functions** for colored output:

   ```bash
   info()  { printf '\033[0;34m[INFO]\033[0m  %s\n' "$*"; }
   ok()    { printf '\033[0;32m[OK]\033[0m    %s\n' "$*"; }
   warn()  { printf '\033[0;33m[WARN]\033[0m  %s\n' "$*"; }
   fail()  { printf '\033[0;31m[FAIL]\033[0m  %s\n' "$*"; }
   ```

5. **Include a header comment** describing what the script does

## YAML Manifest Standards

- All Kubernetes manifests must pass `yamllint -d relaxed`
- Use consistent indentation (2 spaces)
- Include comments for non-obvious settings
- KEDA ScaledObject YAML files should document the scaling trigger and thresholds

## Python Application Standards

- Use Python 3.12+
- Pin dependencies in `requirements.txt`
- Use `os.getenv()` for configuration
- Include basic error handling

## Documentation Standards

When adding a feature or scenario:

1. Update `README.md` if the user-facing flow changes
2. Update `CLAUDE.md` if the project structure or conventions change
3. Add troubleshooting entries in `TROUBLESHOOTING.md` if relevant
4. Record the change in `CHANGELOG.md`

## Pull Request Process

1. Ensure CI checks pass
2. At least one maintainer approval is required
3. Squash commits if needed for a clean history
4. The maintainer will merge using the project's merge strategy

## Questions?

Open an issue or discussion — we're happy to help!

---

Thank you for contributing! ⚡
