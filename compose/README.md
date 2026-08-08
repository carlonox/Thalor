# Compose Service Definitions

This directory is reserved for split service definitions.

The canonical Compose files live at the repository root and are the
**source of truth**:

| File | Purpose |
|---|---|
| `../docker-compose.yml` | Base stack: agent + dashboard proxy |
| `../docker-compose.ops.yml` | Multi-agent extension (second agent) |
| `../docker-compose.router.yml` | Optional FreeLLMAPI router (expert panel) |

If you want to split services into per-service files, move the service blocks
here and reference them with:

```bash
docker compose -f docker-compose.yml -f compose/hermes.yml up -d
```

Keep the root files as the default — they are what `scripts/start.sh` and
`scripts/start.ps1` use.
