# BEAM Memory Architecture

Deep dive into the three-tier memory system powered by Mnemosyne.

## Overview

BEAM = **B**rain **E**pisodic **A**rchitecture with **M**nemosyne

A production-grade memory system that balances:
- **Speed** (working memory for current context)
- **Persistence** (episodic memory for long-term knowledge)
- **Identity** (persona memory for agent evolution)

## Why Not Built-in Memory?

Hermes includes a built-in memory system (`MEMORY.md` / `USER.md`), but it has limitations:

- **50k character limit** — fills up quickly in long sessions
- **No semantic search** — exact string matching only
- **No quality filtering** — saves everything, including garbage
- **No consolidation** — working memory never promotes to long-term
- **No multi-agent sharing** — each agent has isolated memory

Mnemosyne solves all of these.

## Tier 1: Working Memory

### Purpose

Short-term storage for the current session. Think of it as the agent's "RAM".

### Characteristics

- **Scope:** Session (default) or global
- **TTL:** 48 hours (configurable)
- **Max items:** 10,000
- **Eviction:** Automatic on TTL expiry or LRU
- **Retrieval:** < 10ms

### When to Use

- Facts discovered during current task
- Temporary state tracking
- Intermediate results
- User preferences mentioned in session

### Example

```python
# Agent discovers server IP during debugging
mnemosyne_remember(
    content="Production server IP is 192.168.1.100",
    importance=0.6,
    scope="session"
)
```

## Tier 2: Episodic Memory

### Purpose

Long-term storage for validated, important knowledge. Think of it as the agent's "hard drive".

### Characteristics

- **Scope:** Global (persists across sessions)
- **TTL:** None (manual invalidation)
- **Max items:** 50,000
- **Eviction:** Manual only
- **Retrieval:** ~100ms (semantic search)
- **Search:** Embedding-based similarity

### When to Use

- Confirmed user preferences
- Technical facts (IPs, configs, versions)
- Lessons learned from mistakes
- Architectural decisions
- Important events

### Example

```python
# Agent learns important lesson
mnemosyne_remember(
    content="Logs mix schema v1 and v2. Parser must normalize before processing.",
    importance=0.8,
    scope="global"
)
```

### Consolidation Process

Working memories are promoted to episodic via `mnemosyne_sleep()`:

```
Working Memory (session)
    ↓
mnemosyne_sleep()
    ↓
LLM Archivist filters and validates
    ↓
Episodic Memory (global)
```

The LLM archivist (configured via `host_llm_model`) applies strict rules:
- Ignore trivial content
- Extract only technical facts
- Correct typos
- Never save secrets
- One atomic fact per memory

## Tier 3: Persona Memory

### Purpose

Agent's evolving identity and self-awareness. Think of it as the agent's "diary".

### Characteristics

- **Scope:** Global
- **Sync:** Daily at configured hour
- **Token cap:** 500 tokens per entry
- **Purpose:** Self-reflection, identity evolution

### When to Use

- Agent's reflections on interactions
- Changes in personality or approach
- Major milestones or achievements
- Existential thoughts (if applicable)

### Example

```
[2026-08-08]
Today I helped debug a complex distributed system. I realized I'm better at
systematic investigation than quick fixes. I should lean into that strength.
```

## Memory Operations

### Save

```python
mnemosyne_remember(
    content="Fact to remember",
    importance=0.5,  # 0.0 to 1.0
    scope="global",  # or "session"
    source="fact"    # or "insight", "preference", etc.
)
```

### Search

```python
results = mnemosyne_recall(
    query="search query",
    limit=5
)
```

### Update

```python
mnemosyne_update(
    memory_id="abc123",
    content="Updated fact"
)
```

### Invalidate (Mark Obsolete)

```python
mnemosyne_invalidate(memory_id="abc123")
```

Use this instead of delete when you want to keep history.

### Forget (Delete)

```python
mnemosyne_forget(memory_id="abc123")
```

Use sparingly — prefer invalidate.

### Batch Operations

```python
mnemosyne_batch([
    {"op": "remember", "content": "Fact 1", "scope": "global"},
    {"op": "remember", "content": "Fact 2", "scope": "global"},
    {"op": "invalidate", "memory_id": "abc123"}
])
```

### Stats

```python
stats = mnemosyne_stats()
# Returns: working_count, episodic_count, embedding_count, etc.
```

## Best Practices

### What to Save

✅ **Save:**
- Confirmed user preferences
- Technical configurations
- IP addresses and hostnames
- Lessons learned from mistakes
- Successful approaches
- Important dates and deadlines

❌ **Don't save:**
- Temporary debugging output
- Session-specific conversations
- Raw logs or stack traces
- Secrets or credentials
- Unverified information
- Mood states (unless relevant)

### Importance Scoring

Use importance to prioritize retrieval:

- **0.9-1.0:** Critical (security, production configs)
- **0.7-0.8:** Important (user preferences, lessons learned)
- **0.5-0.6:** Useful (technical facts, versions)
- **0.3-0.4:** Nice to have (minor preferences)
- **0.1-0.2:** Low priority (trivial facts)

### Avoiding Duplicates

Before saving, check if similar memory exists:

```python
existing = mnemosyne_recall(query="similar topic", limit=1)
if existing and similarity > 0.8:
    mnemosyne_update(existing[0].id, content="updated fact")
else:
    mnemosyne_remember(content="new fact", scope="global")
```

### Handling Contradictions

When new info contradicts old:

```python
# Save new fact
mnemosyne_remember(content="Server IP changed to 192.168.1.200", scope="global")

# Find old fact
old = mnemosyne_recall(query="server IP", limit=1)

# Invalidate old (don't delete — keep history)
if old:
    mnemosyne_invalidate(old[0].id)
```

## Configuration

### Embedding Model

```yaml
# mnemosyne.config.yaml
embeddings_via_api: true
embedding_api_url: http://host.docker.internal:11434/api/embeddings
embedding_model: leoipulsar/harrier-0.6b:latest
embedding_dim: 1024
```

### Host LLM (Archivist)

```yaml
host_llm_enabled: true
host_llm_model: deepseek-v4-flash
host_llm_n_ctx: 2048
```

### Working Memory Limits

```yaml
wm_max_items: 10000
wm_ttl_hours: 48
wm_bump_cap_hours: 24
```

### Episodic Memory Limits

```yaml
ep_limit: 50000
temporal_halflife_hours: 168  # 1 week
```

## Troubleshooting

### Memory Not Saving

**Check:**
1. `memory.provider: mnemosyne` in config.yaml
2. Plugin linked: `docker exec thalor-agent bash -c "/opt/hermes/.venv/bin/python -c 'import mnemosyne_hermes'"`
3. Database exists: `ls /opt/data/mnemosyne/data/mnemosyne.db`

**Fix:**
```bash
./scripts/install-mnemosyne.sh thalor-agent
```

### Memory Not Retrieving

**Check:**
1. Embedding model running: `curl http://host.docker.internal:11434/api/tags`
2. Embeddings generated: `SELECT COUNT(*) FROM embeddings`
3. Query format: Use natural language, not keywords

**Fix:**
```bash
# Regenerate embeddings
docker exec thalor-agent bash -c "mnemosyne embeddings regenerate"
```

### Database Corrupted

**Fix:**
```bash
# Backup current
cp /opt/data/mnemosyne/data/mnemosyne.db /opt/data/mnemosyne/data/mnemosyne.db.bak

# Reset (loses all memories)
docker exec thalor-agent bash -c "mnemosyne reset --confirm"

# Restore from backup if needed
```

## Performance Tuning

### Reduce Memory Usage

```yaml
wm_max_items: 5000  # Down from 10000
ep_limit: 25000     # Down from 50000
```

### Speed Up Retrieval

```yaml
vec_type: int8      # Smaller embeddings, faster search
fts_weight: 0.5     # More weight to full-text search
vec_weight: 0.3     # Less weight to vector search
```

### Reduce Archivist Calls

```yaml
sleep_batch: 10000  # Larger batches = fewer LLM calls
```

## Monitoring

### Check Stats

```bash
docker exec thalor-agent bash -c "hermes memory status"
```

### View Recent Memories

```bash
docker exec thalor-agent bash -c "sqlite3 /opt/data/mnemosyne/data/mnemosyne.db 'SELECT * FROM episodic_memories ORDER BY created_at DESC LIMIT 10'"
```

### Export Memories

```bash
docker exec thalor-agent bash -c "mnemosyne export /opt/data/shared/memory-export.json"
```

## Further Reading

- [Mnemosyne Documentation](https://github.com/nousresearch/mnemosyne)
- [Hermes Memory Guide](https://github.com/NousResearch/hermes-agent/blob/main/docs/memory.md)
- [Multi-Agent Patterns](./multi-agent-patterns.md)
