# Doc Auditor Skill

Automatically audits and updates architecture documentation by comparing it against the actual system state.

## Overview

This skill:
1. Runs `system_snapshot.py` to get current system state
2. Reads existing documentation in `/opt/data/shared/docs_arquitectura/`
3. Compares documented state vs actual state
4. Identifies discrepancies
5. Updates documentation using `patch_file` or `write_file`

## Usage

```bash
python3 /opt/data/skills/doc-auditor/doc_auditor.py
```

## When to Use

- After major system changes (container recreation, config updates)
- Periodically (weekly) to ensure docs stay accurate
- Before sharing documentation externally
- When user asks to "audit docs" or "verify documentation"

## What It Checks

- Container status (running/stopped)
- Model availability
- MCP server configuration
- Memory provider settings
- Network configuration
- Port mappings

## Output

Generates a report at `/opt/data/shared/doc_audit_report.json`:

```json
{
  "timestamp": "2026-08-08T12:34:56Z",
  "discrepancies": [
    {
      "file": "01-arquitectura-general.md",
      "issue": "Documented Qdrant as running, but it's stopped",
      "severity": "high"
    }
  ],
  "updates_applied": 3,
  "status": "completed"
}
```

## Requirements

- `system_snapshot.py` skill installed
- Read/write access to documentation directory
- `patch_file` tool available (Hermes built-in)

## License

MIT
