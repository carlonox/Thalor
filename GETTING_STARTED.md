# Getting Started

Get Thalor running in 5 minutes.

## Prerequisites

### Required

- **Docker Desktop** (Windows 11 + WSL2, macOS, or Linux)
- **Hermes Agent image** (`nousresearch/hermes-agent:latest`)
- **API key** for your LLM provider (OpenRouter, OpenCode Go, etc.)

### Optional (for full stack)

- **Ollama** (for local vision models)
- **FreeLLMAPI** (for consult-expert skill)

## Installation

### 1. Create your repo from template

```bash
gh repo create my-agent --template carlonox/Thalor
cd my-agent
```

Or manually:
```bash
git clone https://github.com/carlonox/Thalor.git my-agent
cd my-agent
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set:

**Required:**
```bash
LLM_API_KEY=your-api-key-here
DASHBOARD_USERNAME=your-username
DASHBOARD_PASSWORD_HASH=your-scrypt-hash
DASHBOARD_PASSWORD=your-plaintext-password  # used by the dashboard proxy to log in
DASHBOARD_SECRET=your-secret
```

**Optional (for local vision):**
```bash
VISION_BASE_URL=http://host.docker.internal:11434/v1
```

**Optional (for FreeLLMAPI):**
```bash
ROUTER_ENCRYPTION_KEY=your-64-char-hex-key
FREELLMAPI_API_KEY=your-router-api-key
```

Then copy the agent config template and fill in the placeholders:

```bash
cp templates/config.template.yaml data/config.yaml
# Replace every ${VARIABLE} with the matching value from your .env
# This is REQUIRED — the gateway needs dashboard auth to start.
```

### 3. Start the agent

**Windows:**
```powershell
.\scripts\start.ps1
```

**Linux/macOS:**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

Or manually:
```bash
docker compose up -d

# One-time: install Mnemosyne memory provider
./scripts/install-mnemosyne.sh thalor-agent
```

### 4. Access dashboard

Open `http://localhost:9999` in your browser.

Login with the credentials you set in `.env`.

> **Note:** If you see "Dashboard not responding", wait 30 seconds after `install-mnemosyne.sh` completes — the container restarts to link the plugin.

## First Run

The first run takes ~5 minutes because:

1. Docker pulls the Hermes image (~2GB)
2. Mnemosyne package is installed in the container
3. Mnemosyne plugin is linked
4. Container restarts

You'll see this in the logs:
```
[install-mnemosyne] Installing Mnemosyne package...
[install-mnemosyne] Package installed
[install-mnemosyne] Plugin entry point OK
[install-mnemosyne] Restarting container to load the provider...
[install-mnemosyne] Installation complete
```

## Creating Your Agent's Identity

### 1. Copy the SOUL template

```bash
cp templates/SOUL.template.md data/SOUL.md
```

### 2. Customize it

Edit `data/SOUL.md` and fill in:
- Agent name and role
- Personality traits
- Memory rules
- Hard limits

See `templates/soul-examples/` for 3 complete examples.

### 3. Restart the agent

```bash
docker compose restart hermes
```

Your agent now has its own identity.

## Adding Skills

### 1. Copy a skill to your agent's data directory

```bash
cp -r skills/consult-expert data/skills/
```

### 2. Configure environment (if needed)

For `consult-expert`, you need FreeLLMAPI:
```bash
# In .env
FREELLMAPI_BASE_URL=http://host.docker.internal:3000/v1
FREELLMAPI_API_KEY=your-key
```

### 3. Restart the agent

```bash
docker compose restart hermes
```

Your agent can now use the skill.

## Running Multiple Agents

### 1. Start with Ops agent

```bash
docker compose -f docker-compose.yml -f docker-compose.ops.yml up -d
```

### 2. Access dashboards

- Main agent: `http://localhost:9999`
- Ops agent: `http://localhost:9219`

### 3. Share state

Both agents share:
- `shared/kanban/` — Task boards
- `shared/docs_arquitectura/` — Documentation

## Adding MCP Servers

### 1. Choose a template

```bash
ls mcp-servers/
```

### 2. Copy to your config

```bash
# Example: add n8n
cat mcp-servers/n8n.config.example.yaml >> data/config.yaml
```

### 3. Set credentials in .env

```bash
N8N_BEARER_TOKEN=your-token
N8N_URL=http://host.docker.internal:5678/mcp-server/http
```

### 4. Restart the agent

```bash
docker compose restart hermes
```

## Troubleshooting

### Dashboard not responding

```bash
# Check container status
docker ps

# Check logs
docker logs thalor-agent

# Restart
docker compose restart hermes
```

### Mnemosyne not working

```bash
# Verify plugin linked (entry point, not directory)
docker exec thalor-agent bash -c \
  "/opt/hermes/.venv/bin/python -c 'import mnemosyne_hermes; print(\"OK\")'"

# If "ModuleNotFoundError", reinstall:
docker exec -u 0 thalor-agent bash -c \
  "cd /opt/hermes && uv pip install 'mnemosyne-hermes' --python /opt/hermes/.venv/bin/python"
docker restart thalor-agent
```

### Out of memory

```bash
# Check container memory usage
docker stats thalor-agent

# Increase Docker memory limit in Docker Desktop settings
```

## Next Steps

- Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand the system
- Explore [examples/](./examples/) for real-world use cases
- Check [docs/](./docs/) for advanced topics

## Getting Help

- Open an issue on GitHub
- Check [Hermes Agent docs](https://github.com/NousResearch/hermes-agent) for underlying framework questions
- Join the Hermes community Discord for Mnemosyne-specific help
