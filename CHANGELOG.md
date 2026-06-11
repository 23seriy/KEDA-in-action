# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `CONTRIBUTING.md` — contribution guidelines and development workflow
- `SECURITY.md` — security policy and responsible disclosure process
- `TESTING.md` — comprehensive testing guide with automated and manual tests
- `TROUBLESHOOTING.md` — troubleshooting guide for common issues
- `CODE_OF_CONDUCT.md` — Contributor Covenant code of conduct
- `CHANGELOG.md` — this changelog
- `.shellcheckrc` — shellcheck configuration
- `.markdownlint.json` — markdown linting configuration
- `.github/workflows/validate.yml` — CI validation workflow
- `.github/ISSUE_TEMPLATE/` — bug report and feature request templates
- `.github/PULL_REQUEST_TEMPLATE.md` — PR template
- `.github/GOVERNANCE.md` — project governance document
- `.github/dependabot.yml` — automated dependency updates

### Changed

- Upgraded `.gitignore` to comprehensive format with sections for Python, IDE, OS, and Kubernetes

## [1.0.0] — 2025-06-01

### Added

- Initial release with full KEDA demo
- Producer API with Redis queue integration
- Shared worker consuming from Redis highlight-queue
- RabbitMQ publisher and rabbit-worker for recap pipeline
- Six demo scenarios: threshold-5, threshold-20, fast-polling, cron-warm, scale-to-zero, RabbitMQ
- TriggerAuthentication for RabbitMQ scaler
- Guided demo scenario script (`04-demo-scenarios.sh`)
- Complete Minikube setup and teardown scripts
- NBA basketball media ingestion theme
- Published Medium article walkthrough
