# Changelog

All notable changes to Thalor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Two new soul examples — domain-specialist roles for a swarm:
  `quill-docs-sentinel` (documentation consistency) and `moss-memory-gardener` (memory hygiene).
- **Swarm Roles** section in `docs/multi-agent-patterns.md`: hard lanes, specialist profiles,
  coordination via peer messaging / work queues / event hooks / change-gated cron sentinels.
- Consult Expert skill: panel-seat selection guidance + shared-pool troubleshooting
  (flaky seats, retries, live router key lookup, per-seat observability).
- **Security Hardening** section in ARCHITECTURE.md: Bitwarden Secrets Manager pattern (bootstrap token, never credentials in repos), Gitleaks pre-commit + CI scanning, red-team agent pattern (VIGÍA), Conventional Commits 1.0.0 convention.
- **Multi-VM / Cloud Deployment** section: Oracle ARM Always Free 24/7 pattern, Tailscale-only exposure (no public ports, `tailscale serve`), sister-bridge agent↔agent HTTP pattern, dot-agent portable remote-machine client.
- **Hardened backup pattern**: flat directory backups (not tarballs), secret verification before commit, placeholders in configs, history purge on contamination.
- **Deployment modalities template** (`docs/deployment-modalities.md`): local profiles vs cloud 24/7,
  plus `config/swarm.routing.json` v1.1 with the `deployment` block (`mode`, `queue_dir`, `webhook_secret_name`).
- `scripts/swarm_webhook.py` — HMAC-verified GitHub webhook receiver for the cloud modality
  (enqueue + immediate 200; per-agent dispatch is a documented TODO).
- Pre-built Docker image for the dashboard proxy published to GitHub Container Registry:
  `ghcr.io/carlonox/thalor/proxy:latest` (auto-built on every push to `main` via
  GitHub Actions).
- `Dockerfile.proxy` — multi-stage, non-root, pinned deps, multi-arch (amd64 + arm64).
- GitHub Actions workflow that publishes the image and validates template integrity
  (YAML parsing, Python syntax, secret scanning) on every push.
- CI badges in README.
- Initial template release
- BEAM memory architecture with Mnemosyne integration
- Multi-gateway pattern with s6-overlay supervision
- WebSocket relay proxy with custom branding
- Consult Expert skill (multi-model synthesis via FreeLLMAPI)
- System Snapshot skill for auditing
- Doc Auditor skill for documentation maintenance
- Three example implementations:
  - Robot Assistant (AWS DeepRacer — conceptual)
  - Coding Assistant (pair programming)
  - Business Assistant (email triage, scheduling)
- Multi-OS support (Windows, Linux, macOS)
- Comprehensive documentation

### Changed
- N/A (initial release)

### Deprecated
- N/A (initial release)

### Removed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- Template includes placeholder credentials marked as `[REDACTED]`
- `.env.example` uses environment variable placeholders
- No hardcoded secrets in template files

## [0.1.0] - 2026-08-08

### Added
- Initial public release
- Based on Hermes Agent v0.20.0
- Mnemosyne memory provider integration
- FreeLLMAPI router support
- Production-ready Docker Compose setup
