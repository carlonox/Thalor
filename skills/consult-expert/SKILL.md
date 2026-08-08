# Consult Expert — Deterministic Invocation Criteria

## WHEN TO INVOKE (Strict, Measurable Criteria)

Invoke `ask_expert.py` IMMEDIATELY if **AT LEAST ONE** of these scenarios is met:

### 1. Repeated Error Loop
You have executed the same tool (e.g., `terminal`, `edit_file`) **2 times in a row** to solve a problem and received **exactly the same error** or a very similar error. Do NOT attempt a third time on your own.

### 2. Broken/Non-existent Dependency
You attempt to use a library, function, or API, it fails, you do a web search to fix it, and after applying the fix it **still fails** because the solutions you found don't match your code.

### 3. Context-Detected Hallucination
You're writing code and suddenly the compiler or system returns an error indicating that a function you invented doesn't exist, and you don't know what the real one is.

### 4. High Architectural Complexity
The user asks you to design a system involving:
- Concurrent synchronization (deadlocks, race conditions)
- Distributed consensus algorithms (Raft, Paxos)
- Complex mathematical optimization
- Decision trees with more than 3 mutually exclusive trade-off variables

## WHEN NOT TO INVOKE (Routine Tasks)

Do NOT invoke the expert if the problem fits these categories (even if you fail the first time, try to fix it yourself):

### 1. Syntax Errors or Typos
If the error is syntax, missing imports, or misspelled variables, use your context or `web_search`.

### 2. Information Lookup
If you don't know how to use a library, use `web_search`. The expert has no internet access, only internal reasoning.

### 3. Sequential/CRUD Code
Creating simple endpoints, formatting data, modifying basic UI, or writing linear scripts.

### 4. Boilerplate and Configuration
Creating standard configuration files, simple Dockerfiles, or folder structures.

## MANDATORY PRE-INVOKE FLOW

Before executing `python3 /opt/data/skills/consult-expert/ask_expert.py`, you must have made **at least ONE real attempt** to solve it yourself (either by writing code or using `web_search`). If that attempt fails and you meet the criteria above, invoke the expert with the exact error and your failed attempt.

## GOLDEN RULE: Context Injection

When invoking `ask_expert.py`, your prompt MUST include:

1. **Programming language and version** (e.g., Python 3.13)
2. **Operating system or environment** (e.g., Linux in Docker)
3. **Relevant absolute paths** (e.g., `/opt/data/scripts/`)
4. **Fragments of current code or exact error logs**

## GOLDEN RULE: No Blind Execution

**NEVER directly execute** (`terminal`) or apply (`edit_file`) the exact code or commands the expert returns. Their response is generic.

## MANDATORY ADAPTATION

You must **INTERPRET** the expert's solution and **ADAPT** it to your current context before acting. If the expert says "run this script in `/tmp/script.py`", you must adapt it to the correct path, verify that variables exist in your environment, and only then execute. If you have doubts about the adaptation, show it to the user first.

## ERROR HANDLING

If the expert panel is unavailable or returns an error:
```
[ERROR] The expert panel is not available at this time. Error: <error message>
ESCALATE TO USER: ask your operator to consult this question directly with another AI.
```

## EXAMPLE INVOCATION

```bash
python3 /opt/data/skills/consult-expert/ask_expert.py \
  "Context: Python 3.13, Linux in Docker. Script at /opt/data/scripts/parse_logs.py \
   processes logs by batch. Error: KeyError: 'timestamp' at line 47, inside the loop, \
   even with try/except around it. Failed attempt: dict.get('timestamp', '') doesn't \
   work because the error occurs in nested access data['event']['timestamp']. \
   What is the root cause and solution?"
```
