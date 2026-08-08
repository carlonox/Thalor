# Consult Expert Skill

A deterministic skill that escalates complex problems to a panel of AI experts when the agent is stuck.

## Overview

This skill implements a **multi-model synthesis** approach: when the agent encounters a problem it cannot solve after multiple attempts, it consults a panel of expert models in parallel, then a judge model synthesizes the best response.

## When to Invoke

The skill uses **deterministic criteria** — invoke IMMEDIATELY if ANY of these conditions are met:

### 1. Repeated Error Loop
You've executed the same tool (e.g., `terminal`, `edit_file`) **2+ times consecutively** and received the same or very similar error.

**Example:**
```
Attempt 1: terminal("python3 script.py") → KeyError: 'timestamp'
Attempt 2: terminal("python3 script.py") → KeyError: 'timestamp'
→ INVOKE EXPERT
```

### 2. Broken Dependency
You attempt to use a library/function/API, it fails, you search for a fix online, apply it, and it **still fails** because the solutions don't match your code.

### 3. Detected Hallucination
You're writing code and the compiler/interpreter returns an error indicating that a function you invented doesn't exist, and you don't know the real one.

### 4. High Architectural Complexity
The user asks you to design a system involving:
- Concurrency synchronization (deadlocks, race conditions)
- Distributed consensus algorithms (Raft, Paxos)
- Complex mathematical optimization
- Decision trees with 3+ mutually exclusive trade-off variables

## When NOT to Invoke

**Do NOT invoke** for routine tasks (even if you fail the first time):

- **Syntax errors or typos** → Use context + `web_search`
- **Information lookup** → Use `web_search` (expert has no internet access)
- **Sequential/CRUD code** → Solve directly
- **Boilerplate and configuration** → Solve directly

## Mandatory Pre-Invoke Flow

Before invoking the expert, you MUST have made **at least ONE real attempt** to solve it yourself (either by writing code or using `web_search`). If that attempt fails AND you meet the criteria above, invoke the expert with the exact error and your failed attempt.

## Golden Rule: Context Injection

When invoking the expert, your prompt MUST include:

1. **Programming language + version** (e.g., Python 3.13)
2. **Operating system/environment** (e.g., Linux in Docker)
3. **Relevant absolute paths** (e.g., `/opt/data/scripts/script.py`)
4. **Exact code snippets or error logs**

**Example:**
```
Context: Python 3.13 on Linux in Docker. Script at /opt/data/scripts/parse_logs.py 
processes logs in batches. Error: KeyError: 'timestamp' at line 47 inside the batch 
loop, even with try/except around it. Failed attempt: dict.get('timestamp', '') 
doesn't work because the error occurs in nested access data['event']['timestamp']. 
What is the root cause and solution?
```

## Golden Rule: Adaptation

**NEVER execute the expert's solution blindly.** Their response is generic.

You MUST:
1. **INTERPRET** the expert's solution
2. **ADAPT** it to your actual context (correct paths, verify variables exist)
3. **VERIFY** it works before applying

If you're unsure about the adaptation, show it to the user first.

## Usage

```bash
python3 /opt/data/skills/consult-expert/ask_expert.py "Your problem description with full context"
```

## Requirements

- **FreeLLMAPI router** running with `fusion` model configured
- **OpenAI-compatible endpoint** at `${FREELLMAPI_BASE_URL}`

## Configuration

Set these environment variables:

```bash
FREELLMAPI_BASE_URL=http://host.docker.internal:3000/v1
FREELLMAPI_API_KEY=[REDACTED]
```

## How It Works

1. Agent detects it meets invocation criteria
2. Agent prepares context-rich prompt
3. `ask_expert.py` calls FreeLLMAPI with `model="fusion"`
4. FreeLLMAPI fans out the prompt to multiple expert models in parallel
5. A judge model synthesizes the best response
6. Agent receives synthesized answer
7. Agent **interprets and adapts** the solution to their context
8. Agent verifies and applies the adapted solution

## Example

See `examples.md` for a complete multi-turn conversation showing this skill in action.

## License

MIT
