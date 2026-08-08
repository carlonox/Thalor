# Research Assistant Example

A specialized agent for academic research, literature review, and knowledge
synthesis.

## Overview

This example demonstrates:
- **Literature search** — Finding and evaluating papers and sources
- **Knowledge synthesis** — Connecting findings across works
- **Research notes** — Organized, structured note-taking
- **Citation handling** — Proper attribution and reference management

## Setup

```bash
cp -r examples/research-assistant my-research-agent/
cd my-research-agent
docker compose up -d
```

## Customizing

This example is intentionally minimal — the real value is in the SOUL
definition. Use the template:

```bash
cp templates/soul-examples/sage-research.md data/SOUL.md
```

Then restart:

```bash
docker compose restart hermes
```

See `templates/soul-examples/sage-research.md` for the full research-assistant
persona (scholarly tone, citation discipline, hypothesis vs. fact
distinction, and memory rules for key findings).

## License

MIT
