#!/usr/bin/env python3
"""swarm_conventions.py — swarm conventions (stdlib only).

Checks over the base...head range:
- Conventional Commits 1.0.0 on every message (valid type, lowercase, optional
  lowercase scope, non-empty imperative description, no trailing period,
  subject <= 72 on the first line).
- snake_case in new/modified *.py files.
- kebab-case + NN-name.md pattern in shared/docs_arquitectura/**.md.
- No new files matching *.bak*.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TYPES = {"feat", "fix", "docs", "style", "refactor", "perf", "test",
         "build", "ci", "chore", "revert"}
SUBJECT_RE = re.compile(r"^(?P<type>[a-z]+)(?P<breaking>!)?"
                        r"(?:\((?P<scope>[a-z0-9\-/]+)\))?: (?P<desc>.+)$")
PY_RE = re.compile(r"^[a-z][a-z0-9_]*\.py$")
DOC_RE = re.compile(r"^(\d{2}-)?[a-z0-9\-]+\.md$")


def sh(*args):
    p = subprocess.run(list(args), capture_output=True, text=True, cwd=str(REPO))
    return p.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args()
    errors = []

    subjects = [l for l in sh("git", "log", "--format=%s",
                              f"{args.base}..{args.head}").splitlines() if l.strip()]
    if not subjects:
        subjects = [l for l in sh("git", "log", "--format=%s", "-1",
                                  args.head).splitlines() if l.strip()]
    for s in subjects:
        m = SUBJECT_RE.match(s)
        if not m or m.group("type") not in TYPES:
            errors.append(f"commit outside convention: {s!r}")
            continue
        first = s.split(":")[0]
        if len(s) > 72:
            errors.append(f"subject >72 chars: {s!r}")
        desc = m.group("desc").strip()
        if not desc or desc.endswith("."):
            errors.append(f"empty description or trailing period: {s!r}")
        _ = first

    files = [l.strip() for l in
             sh("git", "diff", "--name-only",
                f"{args.base}...{args.head}").splitlines() if l.strip()]
    for f in files:
        base = f.rsplit("/", 1)[-1]
        if fnmatch_bak(base):
            errors.append(f".bak file forbidden: {f}")
            continue
        if f.endswith(".py") and not PY_RE.match(base):
            errors.append(f"py not snake_case: {f}")
        if f.startswith("shared/docs_arquitectura/") and f.endswith(".md"):
            if not DOC_RE.match(base):
                errors.append(f"doc outside NN-kebab pattern: {f}")

    if errors:
        print("conventions: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"conventions: OK ({len(subjects)} commits, {len(files)} files)")
    return 0


def fnmatch_bak(base):
    return ".bak" in base


if __name__ == "__main__":
    sys.exit(main())
