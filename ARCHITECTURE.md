# Architecture

Detailed system architecture for Thalor.

## High-Level Overview

Thalor extends Hermes Agent with production-grade patterns for multi-agent systems. The architecture is built on 5 pillars:

1. **BEAM Memory** — Three-tier persistent memory (working → episodic → persona)
2. **Multi-Gateway** — Multiple agent profiles with isolated contexts
3. **WebSocket Relay** — Custom dashboard proxy with branding and moods
4. **Expert Panel** — Deterministic escalation to multi-model synthesis
5. **Production Hardening** — Supervision, healthchecks, auto-backup

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER (Browser / CLI)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP / WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              DASHBOARD PROXY (Port 9999)                         │
│                                                                  │
│  • Authentication relay to Hermes gateway                        │
│  • Custom HTML/CSS branding                                     │
│  • Mood-based avatar switching (11 states)                       │
│  • WebSocket relay (bidirectional)                               │
│  • API aggregation (/api/*, /v1/*, /mcp-servers)                 │
│                                                                  │
│  Implementation: proxies/dashboard-proxy.template.py             │
│  Pattern: Passive relay — no server-side reconnect               │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP (authenticated)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              HERMES GATEWAY (Port 9119)                           │
│                                                                  │
│  Multiple profiles supervised by s6-overlay:                     │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │ gateway-default  │  │ gateway-secondary│  (or any profile)   │
│  │ (main agent)     │  │ (second agent)   │                     │
│  └──────────────────┘  └──────────────────┘                     │
│                                                                  │
│  Features:                                                       │
│  • Delivery Obligation Ledger (auto-redelivery on crash)         │
│  • Approval system (smart policy, escalation)                    │
│  • Tool execution (terminal, web_search, file, etc.)             │
│  • Streaming responses                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT (Inside Container)                       │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │   SOUL.md       │  │  config.yaml    │  │  Mnemosyne     │  │
│  │   (Identity)    │  │  (Model, tools) │  │  (3-tier mem)  │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    SKILLS                                │    │
│  │  • consult-expert (multi-model synthesis)               │    │
│  │  • system-snapshot (state extraction)                   │    │
│  │  • doc-auditor (documentation maintenance)              │    │
│  │  • [Your custom skills here]                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  MCP SERVERS                             │    │
│  │  • n8n (workflow automation)                             │    │
│  │  • GNS3 (network simulation)                             │    │
│  │  • Packet Tracer (Cisco simulation)                      │    │
│  │  • AgentMail (email management)                          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Memory Architecture (BEAM)

BEAM = **B**rain **E**pisodic **A**rchitecture with **M**nemosyne

### Three Tiers

```
┌─────────────────────────────────────────────────────────┐
│  TIER 1: Working Memory (Session-scoped)                │
│  • Recent facts from current session                     │
│  • TTL: 48 hours                                        │
│  • Max items: 10,000                                    │
│  • Auto-evicted on expiry                               │
│  • Fast retrieval (< 10ms)                              │
└────────────────────────┬────────────────────────────────┘
                         │ mnemosyne_sleep()
                         ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 2: Episodic Memory (Global, persistent)           │
│  • Consolidated facts, lessons, preferences             │
│  • LLM archivist filters quality                        │
│  • No expiry (manual invalidation)                      │
│  • Semantic search via embeddings                       │
│  • Slower retrieval (~100ms)                            │
└────────────────────────┬────────────────────────────────┘
                         │ persona sync (optional)
                         ▼
┌─────────────────────────────────────────────────────────┐
│  TIER 3: Persona Memory (Daily sync)                    │
│  • Agent's evolving identity                            │
│  • Daily consolidation at configured hour                │
│  • Token-capped summaries                               │
│  • Used for self-awareness                              │
└─────────────────────────────────────────────────────────┘
```

### LLM Archivist

During `mnemosyne_sleep()`, the host LLM (configured via `host_llm_model`) acts as an archivist:

**Input:** Working memory from the session

**Output:** Filtered, validated episodic memories

**Rules enforced:**
1. Ignore trivial conversation, greetings, debugging
2. Extract ONLY technical facts and confirmed preferences
3. Correct typos before saving
4. NEVER consolidate secrets or credentials
5. NEVER include internal reasoning (`<think>`, "I need to", etc.)
6. Each fact = 1 atomic proposition (subject > 3 chars, object > 2 words)
7. If confidence < 0.6 → discard

### Memory Operations

| Operation | Tool | Use Case |
|-----------|------|----------|
| Save fact | `mnemosyne_remember()` | New technical fact, preference, lesson |
| Search | `mnemosyne_recall()` | Find relevant facts by semantic similarity |
| Consolidate | `mnemosyne_sleep()` | Promote working → episodic |
| Update | `mnemosyne_update()` | Modify existing fact |
| Invalidate | `mnemosyne_invalidate()` | Mark as obsolete (keep history) |
| Forget | `mnemosyne_forget()` | Delete completely |
| Batch | `mnemosyne_batch()` | Atomic multi-operation |
| Stats | `mnemosyne_stats()` | View memory statistics |

## Multi-Gateway Pattern

Hermes supports multiple agent profiles, each with its own:
- Configuration (`config.yaml` overrides)
- Session history
- Working memory
- Skills and tools

### How It Works

The Hermes container image registers gateways dynamically at boot: the boot
reconciler reads `gateway_state.json` and registers one s6 service per profile
in `/run/service/`. Do NOT override the container CMD — the image handles this.

```bash
# Start default gateway
hermes gateway run

# Start additional gateway with profile "secondary"
hermes -p secondary gateway run
```

Each gateway is supervised as a separate s6 service:
- `gateway-default`
- `gateway-secondary`

### Shared State

Multiple agents can share:
- **Kanban boards** (SQLite database mounted in both)
- **Documentation** (shared directory)
- **Vault** (read-only access from ops to main)

### Use Cases

**Main + Ops:**
- Main agent: User-facing tasks
- Ops agent: Monitoring, health checks, system maintenance

**Main + Specialized:**
- Main agent: General assistant
- Specialized agent: Domain expert (legal, medical, financial)

**Multiple Specialized:**
- Agent 1: Research
- Agent 2: Writing
- Agent 3: Code review

## WebSocket Relay Proxy

### Why a Proxy?

The default Hermes dashboard is functional but limited:
- Basic styling
- No custom branding
- Single authentication method
- No mood visualization

The proxy adds:
- Custom HTML/CSS/JS
- Mood-based avatars (11 states)
- Simplified authentication
- API aggregation

### Architecture

```
Browser (User)
    ↓ HTTP/WS
Dashboard Proxy (9999)
    ↓ HTTP/WS (authenticated)
Hermes Gateway (9119)
```

### Authentication Flow

1. Proxy starts and logs into Hermes gateway once
2. Session cookies stored in aiohttp CookieJar
3. All subsequent requests forwarded with cookies
4. WebSocket connections use ticket-based auth

### WebSocket Relay

```python
# Browser connects to proxy
ws_browser ←→ Dashboard Proxy

# Proxy gets ticket from Hermes
ticket = POST /api/auth/ws-ticket

# Proxy connects to Hermes internally
ws_hermes ←→ Hermes Gateway

# Bidirectional relay
asyncio.gather(
    browser_to_hermes(),  # ws_browser → ws_hermes
    hermes_to_browser()   # ws_hermes → ws_browser
)
```

### Edge Cases

**Proxy behavior (passive):**
- No server-side reconnect
- No retry logic
- No backoff

**Browser behavior (active):**
- Exponential backoff: `base * 2^attempts`, capped at 30s
- Jitter: ±30% randomization
- Max attempts: 15
- Cooldown: 120s after exhaustion

**What happens when gateway crashes?**
1. Internal WebSocket drops
2. Proxy closes browser WebSocket
3. Browser detects disconnection
4. Browser schedules reconnect with backoff
5. If gateway recovers within ~30s, connection restored
6. If not, browser gives up after 15 attempts

## Expert Panel (Consult Expert Skill)

### When to Invoke

**Deterministic criteria:**
1. Repeated error loop (same tool, same error, 2+ times)
2. Broken dependency (web search fix doesn't work)
3. Detected hallucination (invented function)
4. High architectural complexity (concurrency, consensus, optimization)

**NOT for:**
- Syntax errors
- Information lookup
- CRUD code
- Boilerplate

### How It Works

```
Agent stuck
    ↓
Prepare context-rich prompt
    ↓
Call FreeLLMAPI with model="fusion"
    ↓
FreeLLMAPI fans out to panel of models in parallel
    ↓
Judge model synthesizes best response
    ↓
Agent receives synthesized answer
    ↓
Agent interprets and adapts to context
    ↓
Agent verifies and applies
```

### FreeLLMAPI Fusion

FreeLLMAPI is an OpenAI-compatible router that aggregates free tiers from 28+ LLM providers.

**Fusion mode:**
- Prompt sent to multiple expert models in parallel
- Each model generates a draft response
- Judge model synthesizes the best answer
- Panel, judge, and strategy configurable via dashboard

**Configuration:**
- Set up via FreeLLMAPI dashboard's Fusion page
- Agent only needs endpoint + `model="fusion"`

## Production Hardening

### Delivery Obligation Ledger

Hermes v0.19+ includes a SQLite-based ledger for tracking message delivery:

```
State machine:
pending → attempting → delivered
                  ↓
                failed → (auto-redelivery)
```

**Benefits:**
- Auto-redelivery if gateway crashes mid-response
- Persistent across container restarts
- Audit trail for all interactions

### s6-overlay Supervision

All critical services supervised by s6:
- `main-hermes` — Core agent process
- `dashboard` — Web UI
- `gateway-default` — Default profile gateway
- `gateway-secondary` — Secondary profile gateway

**Benefits:**
- Automatic restart on crash
- Dependency management
- Graceful shutdown
- Log aggregation

### Healthchecks

Docker Compose healthchecks for all services:

```yaml
healthcheck:
  test: ["CMD", "bash", "-c", "curl -sf http://localhost:9119/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Auto-Backup

Git-based backup on shutdown:
1. Stage all changes
2. Commit with timestamp
3. Push if upstream exists
4. Exclude binaries, secrets, runtime state

**Hardened pattern (verified 2026-08-13):**
- **Flat directory backup, not tarballs** — copy readable files into `current/` so backups are diff-able and inspectable (tarballs hide secrets and make restore harder).
- **Secret verification BEFORE commit** — grep the backup dir for credential patterns (`ghp_`, `sk-`, `tskey-`, `token=`) and abort if found. Never trust the exclude list alone.
- **Secrets never in backup**: `.env` files, session dumps, gateway state, channel directory, logs. Store secrets in the environment (Bitwarden SM or local `EnvironmentFile` with `chmod 600`) — not in the unit files or configs that get backed up.
- **Placeholders in configs**: configs that need tokens use `${VAR}` placeholders; the real value lives in `.env` (excluded).
- **Purge history if contaminated**: if a secret ever lands in the backup repo, force-push a clean history immediately (only safe on private backup repos with no collaborators).

## Security Hardening

### Secret Management (Bitwarden Secrets Manager)

Production pattern (verified 2026-08-12): centralize all credentials in Bitwarden Secrets Manager (BWS):

```bash
# Bootstrap: single token in .env, everything else in BWS
bws secret list <project-id>
bws secret get <secret-id>        # values never printed to logs
```

**Rules:**
- Never store credentials in repo files, `.env` (tracked), or configs — BWS is the vault.
- `.env` on disk holds only the BWS access token + non-secret vars.
- SSH keys stored in BWS (base64) + `restore-ssh.sh` restores them on boot — survives container recreates and history purges.
- Every new credential → BWS first.

### Secret Scanning (Gitleaks)

- Pre-commit hook: `gitleaks protect --staged` (via `pre-commit` in `/tmp/git-home` with clean `GIT_CONFIG_GLOBAL`).
- CI: GitHub Actions workflow `secret-scan.yml` (gitleaks + trufflehog) on every push.
- `.gitleaksignore` for verified false positives.
- **Red team agent (VIGÍA)**: dedicated profile with deny-by-default policy, 10 scanners, weekly reports with masked values. Hybrid: remote cron (cloud VM) + local catch-up on boot.

### Commit Conventions

All agents MUST follow Conventional Commits 1.0.0 (verified rule 2026-08-13):
- `type(scope): description` — type lowercase, description imperative, ≤72 chars.
- No emojis attached to type, no auto-attributions (`Co-authored-by`, "Generated by").
- Atomic commits: one logical purpose per commit.
- Breaking changes: `feat!:` and/or `BREAKING CHANGE:` footer (uppercase).
- Skill: `conventional-commits-valentinaos` ships with the stack (Valentina + Dot both use it).

## Multi-VM / Cloud Deployment

Thalor's local Docker stack is the base. For 24/7 operation, add a cloud VM (verified pattern: Oracle Cloud Always Free ARM 2 OCPU/12GB):

### Tailscale-only Exposure

- All services bind to the tailnet, never to the public internet:
  - `tailscale up --authkey=<key>` on each node (PC, phone, VMs).
  - `tailscale serve --bg --set-path /<svc> http://localhost:<port>` to expose local dashboards via MagicDNS HTTPS.
  - Cloud VMs: bind services to `0.0.0.0` but keep cloud firewall closed — Tailscale traffic enters via the tailnet interface, not the public port.
- **No port forwarding, no firewall hole-punching** — that's the point of the tailnet.

### Remote Agent Pattern (Sister-Bridge)

Two Hermes agents on different hosts communicate via a small HTTP bridge (systemd, tailnet-only, token-authenticated):

```
POST /api/msg {"token": "...", "to": "agent", "text": "..."}
  → local `hermes -p <profile> chat` → reply JSON
GET  /health → {"ok": true, "agent": "dot", "status": "nominal"}
```

- Token lives in `EnvironmentFile` (chmod 600), never in the unit or backups.
- Inbox JSONL for async messages.
- Verified: Valentina (PC) ↔ Dot (Oracle ARM) chatting end-to-end.

### Remote Machine Access (dot-agent)

Portable Python agent for machines where you CANNOT install Tailscale (university labs):
- Runs with plain `python3`, no install: `python3 dot-agent.py --host <bridge-url> --token <secret>`.
- Polls the bridge every 15s for tasks (works through NAT — outbound HTTPS only).
- Operations: `command` (allowlist), `read`/`write` (workspace allowlist), `list`.
- Hard allowlists — never escapes the workspace, never runs arbitrary commands.
- Alternative: SSH reverse tunnel `ssh -R <port>:localhost:22 <vm>` when SSH is available.

## Directory Structure

```
Thalor/
├── docker-compose.yml              # Base stack
├── docker-compose.ops.yml          # Multi-agent extension
├── docker-compose.router.yml       # FreeLLMAPI extension
├── .env.example                    # Environment template
│
├── compose/                        # Service definitions
│   └── README.md                   # Split-service guidance
│
├── templates/                      # Reusable templates
│   ├── SOUL.template.md
│   ├── config.template.yaml
│   ├── mnemosyne.template.yaml
│   └── soul-examples/
│
├── skills/                         # Agent skills
│   ├── consult-expert/
│   ├── system-snapshot/
│   └── doc-auditor/
│
├── proxies/                        # Dashboard proxy
│   ├── README.md
│   └── dashboard-proxy.template.py
│
├── assets/                         # Custom dashboard assets
│   └── index.html
│
├── mcp-servers/                    # MCP server configs
│
├── examples/                       # Example implementations
│   ├── robot-assistant/
│   ├── coding-assistant/
│   ├── business-assistant/
│   └── research-assistant/
│
├── scripts/                        # Management scripts
│   ├── start.sh (Linux/macOS)
│   ├── start.ps1 (Windows)
│   ├── install-mnemosyne.sh
│   └── backup.sh
│
└── docs/                           # Documentation
    ├── memory-beam.md
    ├── multi-agent-patterns.md
    └── production-deploy.md
```

## Security Considerations

### Credentials

- **Never commit** `.env`, `config.yaml` with real keys
- Use `${VARIABLE}` placeholders
- Generate strong secrets: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### Dashboard Auth

- Use scrypt password hashing
- Generate with: `hermes auth`
- Never hardcode in proxy scripts

### MCP Servers

- Use environment variables for tokens
- Store in `.env` (git-ignored)
- Rotate keys periodically

### Network

- Use Docker network isolation
- Don't expose ports unnecessarily
- Use HTTPS in production (reverse proxy)

## Performance

### Memory Usage

Typical resource usage:
- Hermes container: 2-4 GB RAM
- FreeLLMAPI: 200-500 MB RAM
- Ollama (host): Varies by model (3-10 GB VRAM)

### Optimization

- Enable prompt caching (`prompt_caching.cache_ttl: 5m`)
- Use compression for long contexts
- Limit working memory items (`wm_max_items: 10000`)
- Use local models for vision/embeddings

## Extending Thalor

### Adding a New Skill

1. Create `skills/your-skill/` directory
2. Add `README.md` with usage instructions
3. Add `SKILL.md` with deterministic criteria (if applicable)
4. Implement skill logic (Python script, tool, etc.)
5. Add examples in `examples.md`

### Adding a New MCP Server

1. Find or create MCP server implementation
2. Add config template to `mcp-servers/`
3. Document setup in README
4. Add to `config.template.yaml` (commented)

### Creating a New Agent Profile

1. Create profile: `hermes -p newprofile`
2. Customize `config.yaml` for profile
3. Add to `docker-compose.yml` or create extension
4. Update startup scripts

## License

MIT © Carlos Javier Cuervo Baracaldo
