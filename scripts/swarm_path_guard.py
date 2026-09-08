#!/usr/bin/env python3
"""swarm_path_guard.py — jaula de CI del enjambre (stdlib only).

Lee config/swarm.routing.json; en pull_request calcula git diff --name-only
base...head y verifica que el actor (github.actor) solo toque sus
allowed_globs. En push a main: no-op exit 0 con log (D14: sin if: en el job).

Regla global P-13: shared/** denegado salvo shared/PENDIENTES.md y
shared/docs_arquitectura/** — los allowed_globs de cada bot ya lo reflejan;
aquí se chequea como defensa en profundidad.
"""
import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO / "config" / "swarm.routing.json"


def match_segments(pat_segs, path_segs):
    """Matcher recursivo: '**' consume 0..N segmentos, '*' por segmento."""
    if not pat_segs:
        return not path_segs
    if pat_segs[0] == "**":
        for i in range(len(path_segs) + 1):
            if match_segments(pat_segs[1:], path_segs[i:]):
                return True
        return False
    if not path_segs:
        return False
    if fnmatch.fnmatchcase(path_segs[0], pat_segs[0]):
        return match_segments(pat_segs[1:], path_segs[1:])
    return False


def match_any(path, globs):
    psegs = path.split("/")
    return any(match_segments(g.split("/"), psegs) for g in globs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--actor", default="")
    ap.add_argument("--event", default="pull_request")
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    args = ap.parse_args()

    if args.event == "push":
        print("path-guard: push event — no-op exit 0 (auditoria)")
        return 0

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    agents = cfg.get("agents", {})
    agent = next(
        (a for a, c in agents.items() if c.get("github") == args.actor), None
    )
    if agent is None:
        print(f"path-guard: actor humano '{args.actor}' — sin jaula, exit 0")
        return 0

    allowed = agents[agent].get("allowed_globs", [])
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{args.base}...{args.head}"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    files = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
    if not files:
        print(f"path-guard: sin archivos en el rango — {agent} OK")
        return 0

    glob_cfg = cfg.get("global", {})
    deny = glob_cfg.get("deny", [])
    allow = glob_cfg.get("allow", [])

    violations = []
    for f in files:
        if deny and match_any(f, deny) and not match_any(f, allow):
            if not match_any(f, allowed):
                violations.append(f + " (global deny shared/**)")
                continue
        if not match_any(f, allowed):
            violations.append(f)

    if violations:
        print(f"path-guard: INFRACCION — {args.actor} ({agent}) fuera de scope:")
        for v in violations:
            print(f"  - {v}")
        print(f"  allowed: {allowed}")
        return 1
    print(f"path-guard: OK — {args.actor} ({agent}), {len(files)} archivos en scope")
    return 0


if __name__ == "__main__":
    sys.exit(main())
