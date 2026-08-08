# Thalor

Production-grade starter kit for multi-agent AI systems built on [Hermes Agent](https://github.com/NousResearch/hermes-agent).

[![Docker](https://img.shields.io/badge/docker-required-blue)](https://www.docker.com/)
[![Hermes](https://img.shields.io/badge/hermes-v0.20.0-orange)](https://github.com/NousResearch/hermes-agent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Note:** This is a template, not a framework. You bring your own SOUL.md, credentials, and use case. We bring the architecture.

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

- **[Robot Assistant](./examples/robot-assistant/)** — Conceptual: AWS DeepRacer with live calibration and voice control (architecture pattern, no physical hardware included)
- **[Coding Assistant](./examples/coding-assistant/)** — Pair programmer with git workflows and code review
- **[Business Assistant](./examples/business-assistant/)** — Email triage, meeting scheduling, report generation

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
