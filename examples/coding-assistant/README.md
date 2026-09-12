# Coding Assistant Example

A specialized agent for pair programming, code review, and git workflows.

## Overview

This example demonstrates:
- **Code review** — Analyzing PRs and suggesting improvements
- **Git workflows** — Branching, merging, conflict resolution
- **Testing** — Writing and running tests
- **Documentation** — Generating docs from code
- **Debugging** — Systematic bug investigation

## Setup

```bash
cp -r examples/coding-assistant my-coding-agent/
cd my-coding-agent
docker compose up -d
```

## Usage Examples

### Code Review

**User:** Review the changes in the current branch

**Agent:**
```json
{"tool_calls": [
  {"function": {"name": "terminal", "arguments": "{\"command\": \"git diff main...HEAD\"}"}}
]}
```

**Tool result:** [diff output]

**Agent:** I see 3 files changed. Let me analyze each:

1. **src/api/users.py** — Added pagination to GET /users
   - Good: Using `limit` and `offset` parameters
   - Suggestion: Add validation for negative values
   
2. **tests/test_users.py** — Added tests for pagination
   - Good: Testing edge cases (limit=0, offset beyond range)
   - Good: Using fixtures for test data

3. **README.md** — Updated API documentation
   - Good: Examples for pagination parameters

Overall: Clean implementation, well-tested. Ready to merge after adding validation. `[mood: focused]`

### Git Workflow

**User:** Create a feature branch for the new authentication system

**Agent:**
```json
{"tool_calls": [
  {"function": {"name": "terminal", "arguments": "{\"command\": \"git checkout -b feature/authentication\"}"}}
]}
```

**Tool result:** Switched to a new branch 'feature/authentication'

**Agent:** Branch created. You're now on `feature/authentication`. Ready to start implementing. `[mood: neutral]`

### Debugging

**User:** The login endpoint returns 500 error

**Agent:** Let me investigate systematically.

**Step 1: Check logs**
```json
{"tool_calls": [
  {"function": {"name": "terminal", "arguments": "{\"command\": \"docker logs app-backend 2>&1 | tail -50\"}"}}
]}
```

**Tool result:** `AttributeError: 'NoneType' object has no attribute 'password'`

**Agent:** Found the issue. The user lookup is returning `None` when the user doesn't exist, but the code tries to access `.password` without checking. Fix:

```python
user = get_user_by_email(email)
if not user:
    raise HTTPException(status_code=401, detail="Invalid credentials")
if not verify_password(password, user.password):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

Want me to apply this fix? `[mood: focused]`

## Custom Skills

### code-review

```python
def review_pr(pr_number: int):
    """Review a pull request."""
    # Get PR diff
    diff = subprocess.run(
        ["gh", "pr", "diff", str(pr_number)],
        capture_output=True,
        text=True
    ).stdout
    
    # Analyze with LLM
    analysis = analyze_code(diff)
    return analysis
```

### git-workflow

```python
def create_feature_branch(feature_name: str):
    """Create a feature branch."""
    subprocess.run(["git", "checkout", "-b", f"feature/{feature_name}"])
```

## License

MIT
