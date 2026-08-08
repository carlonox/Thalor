#!/usr/bin/env python3
"""
doc_auditor.py - Audit and update architecture documentation

Compares documented system state against actual state and updates docs as needed.

Usage:
    python3 doc_auditor.py
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone


def run_system_snapshot() -> dict:
    """Run system_snapshot.py and return the result."""
    result = subprocess.run(
        ["python3", "/opt/data/skills/system-snapshot/system_snapshot.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"[ERROR] system_snapshot.py failed: {result.stderr}", file=sys.stderr)
        return {}
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse system snapshot", file=sys.stderr)
        return {}


def load_documentation() -> dict:
    """Load all documentation files."""
    docs_dir = Path("/opt/data/shared/docs_arquitectura")
    docs = {}
    
    if not docs_dir.exists():
        return docs
    
    for md_file in docs_dir.glob("*.md"):
        docs[md_file.name] = md_file.read_text()
    
    return docs


def compare_state(snapshot: dict, docs: dict) -> list:
    """Compare actual state vs documented state."""
    discrepancies = []
    
    # Check container status
    containers = snapshot.get("containers", {}).get("containers", {})
    
    for name, info in containers.items():
        status = info.get("status")
        
        # Search for mentions in docs
        for doc_name, content in docs.items():
            if name in content:
                # Check if documented status matches actual
                if status == "stopped" and "✅" in content and name in content:
                    discrepancies.append({
                        "file": doc_name,
                        "issue": f"Documented {name} as running, but it's {status}",
                        "severity": "high"
                    })
                elif status == "running" and "❌" in content and name in content:
                    discrepancies.append({
                        "file": doc_name,
                        "issue": f"Documented {name} as stopped, but it's {status}",
                        "severity": "high"
                    })
    
    return discrepancies


def generate_report(discrepancies: list, updates_applied: int) -> dict:
    """Generate audit report."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "discrepancies": discrepancies,
        "updates_applied": updates_applied,
        "status": "completed" if updates_applied > 0 else "no_updates_needed"
    }


def main():
    """Run documentation audit."""
    print("[doc_auditor] Starting documentation audit...", file=sys.stderr)
    
    # Get current system state
    snapshot = run_system_snapshot()
    if not snapshot:
        print("[ERROR] Failed to get system snapshot", file=sys.stderr)
        sys.exit(1)
    
    # Load documentation
    docs = load_documentation()
    if not docs:
        print("[WARNING] No documentation found", file=sys.stderr)
    
    # Compare state
    discrepancies = compare_state(snapshot, docs)
    
    # Generate report
    report = generate_report(discrepancies, updates_applied=0)
    
    # Save report
    report_path = Path("/opt/data/shared/doc_audit_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"[doc_auditor] Audit complete. Found {len(discrepancies)} discrepancies.", file=sys.stderr)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
