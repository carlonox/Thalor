# Changelog

All notable changes to Thalor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
