# Thalor

Production-grade starter kit for multi-agent AI systems built on [Hermes Agent](https://github.com/NousResearch/hermes-agent).

[![Docker](https://img.shields.io/badge/docker-required-blue)](https://www.docker.com/)
[![Hermes](https://img.shields.io/badge/hermes-v0.21.1-orange)](https://github.com/NousResearch/hermes-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/carlonox/Thalor/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/carlonox/Thalor/actions/workflows/docker-publish.yml)
[![GHCR](https://ghcr-badge.egpl.dev/carlonox/thalor/proxy/latest_tag?trim=major&label=ghcr&color=blue)](https://github.com/carlonox/Thalor/pkgs/container/thalor%2Fproxy)

> **Note:** This is a template, not a framework. You bring your own SOUL.md, credentials, and use case. We bring the architecture.
>
> **Updated:** September 2026 — validated against Hermes Agent **v0.21.1**; includes guardian-swarm patterns (docs sentinel, memory gardener, ops-watch) and multi-gateway routing examples.

Named after the **thalamus** — the brain structure that connects and coordinates neural regions. Just as the thalamus orchestrates neural activity, Thalor orchestrates AI agents.

## Quick Start

```bash
# Clone with template
gh repo create my-agent --template carlonox/Thalor
cd my-agent

# Configure
cp .env.example .env
# Edit .env with your API keys and credentials

# Start
docker compose up -d

# Install Mnemosyne memory provider (one-time setup)
./scripts/install-mnemosyne.sh thalor-agent

# Access dashboard
open http://localhost:9999
```

First run takes ~5 minutes:
- Docker pulls images (~2 min)
- Mnemosyne installation (~2 min)
- Plugin linking and container restart (~1 min)

## Docker Image

The dashboard proxy is published as a pre-built Docker image on GitHub Container Registry.
The `docker-compose.yml` pulls it automatically on `docker compose up -d`.

```bash
# Pull directly
docker pull ghcr.io/carlonox/thalor/proxy:latest

# Run standalone (without the full stack)
docker run -d \
  -e HERMES_HOST=host.docker.internal \
  -e HERMES_PORT=9119 \
  -e DASHBOARD_USERNAME=agent \
  -e DASHBOARD_PASSWORD=your-secret \
  -p 9999:9999 \
  ghcr.io/carlonox/thalor/proxy:latest
```

The image is rebuilt automatically on every push to `main` that touches `proxies/`,
`assets/`, or `Dockerfile.proxy` (plus a monthly scheduled refresh for base-image security patches; manual runs via `workflow_dispatch`). It is multi-arch (`linux/amd64` + `linux/arm64`),
runs as a non-root user, and pins its dependencies. To build locally instead,
uncomment the `build:` block in `docker-compose.yml` and comment out the `image:` line.

## What's Included

Things Hermes doesn't ship with out of the box:

| Layer | What we add |
|---|---|
| **Memory** | BEAM architecture via Mnemosyne (working → episodic → persona) with LLM archivist |
| **Orchestration** | Multi-gateway pattern (default + ops + api) with shared state |
| **Routing** | FreeLLMAPI integration with `fusion` model for expert panel |
| **Dashboard** | WebSocket relay proxy with custom branding and mood avatars |
| **Supervision** | s6-overlay patterns for production deployments |
| **Hardening** | Production patterns (Delivery Obligation Ledger from Hermes v0.19+ auto-redelivery, s6 supervision, auto-backup) |
| **Security** | Bitwarden Secrets Manager vault, Gitleaks pre-commit + CI, red-team agent (VIGÍA), Conventional Commits convention |
| **Cloud** | Multi-VM deployment (Oracle ARM Always Free), Tailscale-only exposure, sister-bridge (agent↔agent HTTP), dot-agent (remote machine access) |

## When to Use This

**Use Thalor if you:**
- Need persistent memory across sessions (Hermes' built-in memory caps at 50k chars)
- Want to run 2+ agents that share state (kanban, docs, configs)
- Need a custom dashboard beyond the default Hermes UI
- Want to integrate MCP servers like n8n, GNS3, or Packet Tracer
- Are deploying to production and need supervision + healthchecks

**Stick with vanilla Hermes if you:**
- Just need a single agent with basic tools
- Are doing quick prototypes or experiments
- Don't care about persistent memory
- Don't need multi-agent coordination

## Architecture

```
┌─────────────────────────────────────────┐
│           USER (Browser)                │
└─────────────┬───────────────────────────┘
              │ WebSocket
              ▼
┌─────────────────────────────────────────┐
│     Dashboard Proxy (9999)              │
│     • Auth relay                        │
│     • Custom branding                   │
│     • Mood-based avatars                │
└─────────────┬───────────────────────────┘
              │ HTTP
              ▼
┌─────────────────────────────────────────┐
│     Hermes Gateway (9119)               │
│     • default profile                   │
│     • ops profile (monitoring)          │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│     Agent                               │
│     • SOUL.md (identity)                │
│     • config.yaml (model, tools)        │
│     • Mnemosyne (3-tier memory)         │
│     • Skills (consult-expert, etc.)     │
└─────────────────────────────────────────┘
```

Full diagram: [ARCHITECTURE.md](./ARCHITECTURE.md)

## Example Implementations

- **[Specialist Role Souls](./templates/soul-examples/)** — Five ready-to-adapt personas for swarm-style setups: sysadmin, data scientist, research, **docs sentinel** and **memory gardener**, with coordination patterns in [Multi-Agent Patterns](./docs/multi-agent-patterns.md)
- **[Robot Assistant](./examples/robot-assistant/)** — Conceptual: AWS DeepRacer with live calibration and voice control (architecture pattern, no physical hardware included)
- **[Coding Assistant](./examples/coding-assistant/)** — Pair programmer with git workflows and code review
- **[Business Assistant](./examples/business-assistant/)** — Email triage, meeting scheduling, report generation

## Security & Cloud Patterns

- **Secrets**: all credentials in Bitwarden Secrets Manager — never in repo files. Single bootstrap token in `.env`.
- **Scanning**: Gitleaks pre-commit hook + CI workflow; optional red-team agent (VIGÍA) for weekly audits.
- **Commits**: Conventional Commits 1.0.0 enforced across all agents (skill `conventional-commits-valentinaos`).
- **Cloud**: add a 24/7 VM (Oracle ARM Always Free verified); expose services ONLY via Tailscale (no public ports).
- **Agent-to-agent**: sister-bridge HTTP pattern for cross-host Hermes agents.
- **Remote machines**: dot-agent portable Python client for machines where Tailscale can't be installed.

## Documentation

- [Getting Started](./GETTING_STARTED.md) — 5-minute setup guide
- [Architecture](./ARCHITECTURE.md) — Detailed system diagram
- [Memory (BEAM)](./docs/memory-beam.md) — How the 3-tier memory works
- [Multi-Agent Patterns](./docs/multi-agent-patterns.md) — Running 2+ agents
- [Production Deploy](./docs/production-deploy.md) — Docker, s6, backups

## Different from Hermes?

Hermes is an excellent single-agent framework. Thalor is what you need when:

```
Hermes                    Thalor
─────────────────────────────────────────────────────
Single agent         →    Multi-agent orchestration
Built-in memory      →    BEAM memory (3 tiers, LLM archivist)
Basic dashboard      →    Custom WebSocket relay proxy
Single gateway       →    Multiple gateways (default, ops, api)
No supervision       →    s6-overlay patterns
No auto-backup       →    Git-based backup hooks
```

Think of it this way: Hermes is the engine. Thalor is the chassis, transmission, and body.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

MIT © [Carlos Javier Cuervo Baracaldo](https://github.com/carlonox)
