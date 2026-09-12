# Multi-Agent Patterns

How to run and coordinate multiple agents with Thalor.

## Overview

Hermes supports multiple agent profiles, each with isolated:
- Configuration
- Session history
- Working memory
- Skills and tools

Agents can share:
- Kanban boards (SQLite)
- Documentation directories
- Vault (read-only access)

## Pattern 1: Main + Ops

**Use case:** User-facing agent + monitoring/maintenance agent

### Architecture

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Main Agent  │ ← User interactions, tasks, conversations
│ (default)   │
└──────┬──────┘
       │ Monitors
       ▼
┌─────────────┐
│ Ops Agent   │ ← Health checks, backups, system maintenance
│   (ops)     │
└─────────────┘
```

### Setup

**docker-compose.yml:**
```yaml
services:
  hermes:
    image: nousresearch/hermes-agent:latest
    container_name: thalor-main
    ports:
      - "9999:9999"
      - "9119:9119"
    volumes:
      - ./data:/opt/data
      - ./shared:/opt/data/shared

  hermes-ops:
    image: nousresearch/hermes-agent:latest
    container_name: thalor-ops
    ports:
      - "9250:9250"
    volumes:
      - ./data-ops:/opt/data
      - ./shared:/opt/data/shared
    depends_on:
      - hermes
```

**Main agent config:**
```yaml
agent:
  name: Atlas
  # ... standard config
```

**Ops agent config:**
```yaml
agent:
  name: Ops
  # Monitoring-focused SOUL.md
  # Tools: system-snapshot, doc-auditor
```

### Shared State

**Kanban board:**
```yaml
# Both agents mount the same database
volumes:
  - ./shared/kanban/kanban.db:/opt/data/kanban.db
  - ./shared/kanban/boards:/opt/data/kanban/boards
```

**Documentation:**
```yaml
volumes:
  - ./shared/docs:/opt/data/shared/docs
```

### Ops Responsibilities

- Monitor main agent health
- Run system snapshots
- Audit documentation
- Perform backups
- Restart failed services

## Pattern 2: Main + Specialized

**Use case:** General assistant + domain expert

### Architecture

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       ├──────────────────┐
       ▼                  ▼
┌─────────────┐   ┌─────────────┐
│ Main Agent  │   │ Legal Agent │
│ (default)   │   │  (legal)    │
└─────────────┘   └─────────────┘
```

### Setup

```yaml
services:
  hermes:
    image: nousresearch/hermes-agent:latest
    container_name: thalor-main
    # ... standard config

  hermes-legal:
    image: nousresearch/hermes-agent:latest
    container_name: thalor-legal
    volumes:
      - ./data-legal:/opt/data
      - ./shared:/opt/data/shared
```

**Legal agent config:**
```yaml
agent:
  name: Lex
  # SOUL.md: Legal expert personality
  # Skills: contract-review, legal-research
  # MCP servers: legal databases
```

### Handoff Protocol

**Main agent detects legal question:**
```
User: "Can you review this contract?"
Agent: "This requires legal expertise. Handing off to Lex..."
```

**Main agent invokes specialized agent:**
```bash
# Via shared kanban board
# Main creates task: "Review contract for user X"
# Legal agent picks up task
```

## Pattern 3: Multiple Specialized

**Use case:** Team of domain experts

### Architecture

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       ├──────────┬──────────┬──────────┐
       ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Research  │ │Writing   │ │Code      │ │Data      │
│Agent     │ │Agent     │ │Agent     │ │Agent     │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### Setup

```yaml
services:
  hermes-research:
    image: nousresearch/hermes-agent:latest
    # ... research-focused config

  hermes-writing:
    image: nousresearch/hermes-agent:latest
    # ... writing-focused config

  hermes-code:
    image: nousresearch/hermes-agent:latest
    # ... coding-focused config

  hermes-data:
    image: nousresearch/hermes-agent:latest
    # ... data science config
```

### Coordination via Kanban

**Shared board structure:**
```
Project: Blog Post
├─ [Research] Gather sources (assigned: Research Agent)
├─ [Writing] Draft article (assigned: Writing Agent)
├─ [Code] Add code examples (assigned: Code Agent)
└─ [Data] Create visualizations (assigned: Data Agent)
```

### Orchestration Script

```python
# orchestrator.py
def assign_task(task, agent):
    # Create kanban card
    # Assign to agent
    # Notify via webhook
    pass

def check_progress():
    # Query kanban board
    # Report status to user
    pass
```

## Pattern 4: Hierarchical

**Use case:** Manager agent + worker agents

### Architecture

```
┌─────────────┐
│    User     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Manager     │ ← Task decomposition, coordination
│   Agent     │
└──────┬──────┘
       │ Delegates
       ├──────────┬──────────┐
       ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Worker 1  │ │Worker 2  │ │Worker 3  │
└──────────┘ └──────────┘ └──────────┘
```

### Manager Responsibilities

- Receive user requests
- Decompose into subtasks
- Assign to workers
- Aggregate results
- Report to user

### Worker Responsibilities

- Execute specific subtasks
- Report results to manager
- Request help if stucked

### Communication

**Via shared directory:**
```
/shared/
  tasks/
    task-001.json  ← Manager creates
    task-001-result.json  ← Worker writes
```

**Via MCP server:**
```python
# Manager sends message to worker
manager_agent.send_message(
    to="worker-1",
    content="Execute task X",
    priority="high"
)
```

## Shared State Patterns

### Shared Kanban Board

**Mount same database in all agents:**
```yaml
volumes:
  - ./shared/kanban/kanban.db:/opt/data/kanban.db
  - ./shared/kanban/boards:/opt/data/kanban/boards
```

**Agent A creates task:**
```python
# Agent A
kanban.create_card(
    board="project-x",
    title="Research competitors",
    assignee="agent-b"
)
```

**Agent B picks up task:**
```python
# Agent B
tasks = kanban.get_my_tasks()
for task in tasks:
    # Execute task
    kanban.update_status(task.id, "done")
```

### Shared Documentation

**Mount shared docs directory:**
```yaml
volumes:
  - ./shared/docs:/opt/data/shared/docs
```

**Agent A writes doc:**
```python
write_file("/opt/data/shared/docs/architecture.md", content)
```

**Agent B reads doc:**
```python
content = read_file("/opt/data/shared/docs/architecture.md")
```

### Shared Vault (Read-Only)

**Main agent has read-write vault:**
```yaml
volumes:
  - ./vault:/mnt/vault  # Read-write
```

**Ops agent has read-only vault:**
```yaml
volumes:
  - ./vault:/mnt/vault:ro  # Read-only
```

**Ops can read but not modify:**
```python
# Ops agent
files = list_directory("/mnt/vault")  # OK
write_file("/mnt/vault/file.txt", content)  # ERROR: Read-only
```

## Conflict Resolution

### Memory Conflicts

**Problem:** Two agents save conflicting facts

**Solution:** Use importance scoring
```python
# Agent A
mnemosyne_remember(
    content="Server IP is 192.168.1.100",
    importance=0.6
)

# Agent B (more authoritative)
mnemosyne_remember(
    content="Server IP changed to 192.168.1.200",
    importance=0.9
)

# Higher importance wins in retrieval
```

### File Conflicts

**Problem:** Two agents edit same file

**Solution:** Use locking
```python
# Agent A
lock_file("/opt/data/shared/config.yaml")
# Edit file
unlock_file("/opt/data/shared/config.yaml")

# Agent B waits for lock
```

### Task Conflicts

**Problem:** Two agents work on same task

**Solution:** Use kanban assignment
```python
# Only assigned agent can update task
if task.assignee != my_agent_id:
    return "Task assigned to another agent"
```

## Monitoring Multi-Agent Systems

### Ops Agent Pattern

**Ops agent monitors all other agents:**

```python
# system-snapshot skill
def check_all_agents():
    containers = get_docker_containers()
    
    for container in containers:
        if "hermes" in container.name:
            health = check_health(container)
            memory = get_memory_stats(container)
            
            if health != "healthy":
                alert(f"{container.name} is unhealthy")
            
            if memory.working > 9000:
                alert(f"{container.name} memory nearly full")
```

### Dashboard Aggregation

**Custom dashboard shows all agents:**

```javascript
// Fetch status from all agents
const agents = [
  { name: "Main", url: "http://localhost:9999" },
  { name: "Ops", url: "http://localhost:9250" },
  { name: "Legal", url: "http://localhost:9350" }
];

agents.forEach(agent => {
  fetch(`${agent.url}/api/health`)
    .then(resp => resp.json())
    .then(data => updateAgentStatus(agent.name, data));
});
```

## Best Practices

### 1. Clear Boundaries

Each agent should have:
- Specific domain/responsibility
- Own SOUL.md (personality)
- Own config.yaml (model, tools)
- Own session history

### 2. Minimal Sharing

Share only what's necessary:
- Kanban boards (coordination)
- Documentation (knowledge)
- Session history (privacy)
- Working memory (isolation)

### 3. Explicit Communication

Don't assume agents know each other's state:
- Use kanban for task handoff
- Use shared files for data exchange
- Use MCP for real-time messaging

### 4. Ops Agent Always

Always run an Ops agent for:
- Health monitoring
- Backup automation
- Documentation auditing
- System maintenance

### 5. Test Isolation

Before deploying multi-agent:
- Test each agent independently
- Verify no resource conflicts
- Check port availability
- Validate shared state access

## Troubleshooting

### Agents Can't See Each Other

**Check:**
1. Same Docker network: `docker network inspect thalor-net`
2. Ports published: `docker ps`
3. Firewall rules: `sudo ufw status`

**Fix:**
```bash
# Ensure all agents on same network
docker compose up -d
```

### Shared State Not Syncing

**Check:**
1. Same mount path in all agents
2. File permissions: `ls -la /opt/data/shared/`
3. SQLite locking: Only one writer at a time

**Fix:**
```bash
# Check mounts
docker inspect thalor-main | grep -A5 Mounts
docker inspect thalor-ops | grep -A5 Mounts
```

### Memory Conflicts

**Check:**
1. Importance scores
2. Timestamp of memories
3. Scope (session vs global)

**Fix:**
```python
# Invalidate conflicting memory
mnemosyne_invalidate(memory_id="abc123")

# Re-save with correct importance
mnemosyne_remember(content="corrected fact", importance=0.9)
```

## Further Reading

- [Memory (BEAM)](./memory-beam.md)
- [Production Deploy](./production-deploy.md)
- [Hermes Multi-Profile Docs](https://github.com/NousResearch/hermes-agent/blob/main/docs/profiles.md)

---

## Swarm Roles — Domain Specialists

Instead of one all-purpose agent, grow a **swarm**: one specialist profile per domain
(documentation, memory hygiene, code review, security, inventory…). Each specialist:

- **Owns a hard lane** — a narrow set of paths it may *write*. The lane itself is the security boundary.
- **Has its own SOUL, config, and skills** — specialized context beats a bloated generalist.
- **Verifies against reality** — numbers come from commands/DBs, never from memory.
- **Reports, never closes** — humans (or a designated orchestrator agent) review and merge.
  No specialist makes final decisions outside its lane.

Coordination options (pick per scale, combine at will):

- **Peer messaging** (bot-to-bot) for direct specialist↔specialist handoffs.
- **A work queue / kanban board** when multiple specialists consume and produce tasks.
- **Event hooks** (e.g., post-commit) so specialists run only when their domain changed.
- **Change-gated scheduled sentinels** (cron jobs that skip the LLM entirely when nothing
  changed) for continuous monitoring at ~zero cost while idle.

Ready-to-adapt role SOULs live in `templates/soul-examples/`: `quill-docs-sentinel.md`
(documentation consistency) and `moss-memory-gardener.md` (memory hygiene).
