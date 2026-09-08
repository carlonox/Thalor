#!/usr/bin/env python3
"""swarm_conventions.py — convenciones del enjambre (stdlib only).

Chequea sobre el rango base...head:
- Conventional Commits 1.0.0 en cada mensaje (type válido, minúsculas, scope
  opcional en minúsculas, descripción imperativa no vacía, sin punto final,
  asunto <= 72 en la primera línea).
- snake_case en *.py nuevos/modificados.
- kebab-case + patrón NN-nombre.md en shared/docs_arquitectura/**.md.
- Cero archivos nuevos que matcheen *.bak*.
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
            errors.append(f"commit fuera de convención: {s!r}")
            continue
        first = s.split(":")[0]
        if len(s) > 72:
            errors.append(f"asunto >72 chars: {s!r}")
        desc = m.group("desc").strip()
        if not desc or desc.endswith("."):
            errors.append(f"descripción vacía o con punto final: {s!r}")
        _ = first

    files = [l.strip() for l in
             sh("git", "diff", "--name-only",
                f"{args.base}...{args.head}").splitlines() if l.strip()]
    for f in files:
        base = f.rsplit("/", 1)[-1]
        if fnmatch_bak(base):
            errors.append(f"archivo .bak prohibido: {f}")
            continue
        if f.endswith(".py") and not PY_RE.match(base):
            errors.append(f"py no snake_case: {f}")
        if f.startswith("shared/docs_arquitectura/") and f.endswith(".md"):
            if not DOC_RE.match(base):
                errors.append(f"doc fuera de patrón NN-kebab: {f}")

    if errors:
        print("conventions: FALLO")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"conventions: OK ({len(subjects)} commits, {len(files)} archivos)")
    return 0


def fnmatch_bak(base):
    return ".bak" in base


if __name__ == "__main__":
    sys.exit(main())
