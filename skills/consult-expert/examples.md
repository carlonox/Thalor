# Consult Expert — Example Conversations

## Example 1: Repeated Error Loop → Expert Invocation

### Turn 1 — User Request

**User:** The log parser fails with the same error twice: `KeyError: 'timestamp'` in the batch. I already tried a try/except and it still breaks. What do I do?

### Turn 2 — Agent Attempts (2 failures)

**Agent:** Attempt 1 — run the script and see the exact traceback:

```json
{"tool_calls": [
  {"function": {"name": "terminal", "arguments": "{\"command\": \"python3 /workspace/scripts/parse_logs.py /workspace/project/logs/app.log 2>&1 | tail -20\"}"}}
]}
```

**Tool result:** `KeyError: 'timestamp'` at `parse_logs.py:47` inside the batch loop.

**Agent:** Attempt 2 — add defensive handling and retry:

```json
{"tool_calls": [
  {"function": {"name": "terminal", "arguments": "{\"command\": \"python3 /workspace/scripts/parse_logs.py /workspace/project/logs/app.log 2>&1 | tail -20\"}"}}
]}
```

**Tool result:** Same error: `KeyError: 'timestamp'` at the same line, with the fix applied.

### Turn 3 — Expert Invocation

**Agent:** Two attempts, same error → criterion 1 met (repeated error loop). Invoking expert panel with full context:

```json
{"tool_calls": [
  {"function": {"name": "terminal", "arguments": "{\"command\": \"python3 /workspace/scripts/ask_expert.py \\\"Context: Python 3.13, Linux in Docker. Script at /workspace/scripts/parse_logs.py processes logs by batch. Error: KeyError: 'timestamp' at line 47, inside the loop, even with try/except around it. Failed attempt: dict.get('timestamp', '') doesn't work because the error occurs in nested access data['event']['timestamp']. What is the root cause and solution?\\\" 2>&1 | tail -30\"}"}}
]}
```

### Turn 4 — Expert Response

**Tool result (expert):** Root cause: the batch mixes two log formats — some events use `event.timestamp`, others use `meta.timestamp` (schema v2). The defensive fix doesn't work because the nested access explodes before. Solution: normalize with a timestamp extractor tolerant to both schemas before parsing.

### Turn 5 — Agent Adapts and Applies

**Agent:** Adapting the solution to the actual code (not applying blindly) — extracting the timestamp with a helper that checks both schemas, and verifying:

```json
{"tool_calls": [
  {"function": {"name": "terminal", "arguments": "{\"command\": \"python3 /workspace/scripts/parse_logs.py /workspace/project/logs/app.log 2>&1 | tail -5\"}"}}
]}
```

**Tool result:** `✅ 1,204 events parsed, 0 errors.`

**Agent:** Solved — it was an inconsistent schema issue between batches, not the try/except. Saving the lesson to global memory:

```json
{"tool_calls": [
  {"function": {"name": "mnemosyne_remember", "arguments": "{\"content\": \"Pipeline logs: batches mix schema v1 (event.timestamp) and v2 (meta.timestamp). Parser must normalize with tolerant extractor before parsing. Lesson learned 2026-08.\", \"importance\": 0.7, \"scope\": \"global\", \"source\": \"insight\"}"}}
]}
```

---

## Example 2: When NOT to Invoke

### Scenario: Simple Syntax Error

**User:** The script fails with `NameError: name 'pandas' is not defined`.

**Agent:** This is a missing import (syntax error category). Fixing directly:

```python
import pandas as pd
```

**NO expert invocation** — this is routine and solvable with context.

---

## Example 3: Broken Dependency

### Scenario: Library Installation Failure

**User:** Install `requests` and use it to fetch data from an API.

**Agent:** Attempt 1 — install and use:

```bash
pip install requests
python3 -c "import requests; print(requests.get('https://api.example.com').status_code)"
```

**Tool result:** `ModuleNotFoundError: No module named 'requests'`

**Agent:** Attempt 2 — search for fix:

```json
{"tool_calls": [
  {"function": {"name": "web_search", "arguments": "{\"query\": \"pip install requests module not found docker\"}"}}
]}
```

**Tool result:** Various solutions (use `python3 -m pip`, check PATH, etc.)

**Agent:** Apply fix and retry:

```bash
python3 -m pip install requests
python3 -c "import requests; print(requests.get('https://api.example.com').status_code)"
```

**Tool result:** Still `ModuleNotFoundError` — solutions don't match the environment.

**Agent:** Two attempts with web search, still failing → criterion 2 met (broken dependency). Invoking expert with full context...

---

## Key Takeaways

1. **Always attempt at least once** before invoking the expert
2. **Provide full context** (language, OS, paths, code snippets)
3. **Never execute blindly** — interpret and adapt the expert's solution
4. **Save lessons learned** to memory for future reference
5. **Use deterministic criteria** — don't invoke for routine tasks
