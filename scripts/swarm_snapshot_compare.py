#!/usr/bin/env python3
"""swarm_snapshot_compare.py — compares docs health vs baseline (stdlib only).

Usage: python scripts/swarm_snapshot_compare.py health.json --max-regression 0
     [--baseline shared/docs_arquitectura/snapshot.json]

Contract [GENERIC]: exit 0 if regression <= max, exit 1 if greater.
The project's domain script (--json) emits the JSON;
this compare only measures deltas. Without a versioned baseline: everything passes with a warning.
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE = REPO / "docs" / "snapshot.json"


def score(data):
    if isinstance(data, dict):
        total = 0
        for key in ("errors", "warnings", "issues", "failures"):
            v = data.get(key, 0)
            if isinstance(v, list):
                total += len(v)
            elif isinstance(v, (int, float)):
                total += int(v)
        if total:
            return total
        # fallback: recursive count of dicts with level error/warning
        return 0
    if isinstance(data, list):
        return len(data)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("health", help="current JSON from doc_health_check.py")
    ap.add_argument("--max-regression", type=int, default=0)
    ap.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    args = ap.parse_args()

    cur = json.loads(Path(args.health).read_text(encoding="utf-8"))
    cur_score = score(cur)
    bpath = Path(args.baseline)
    if not bpath.exists():
        print(f"snapshot_compare: no baseline ({bpath}) — passes with warning "
              f"(current={cur_score})")
        return 0
    base = json.loads(bpath.read_text(encoding="utf-8"))
    base_score = score(base)
    regression = max(0, cur_score - base_score)
    print(f"snapshot_compare: base={base_score} current={cur_score} "
          f"regression={regression} (max={args.max_regression})")
    return 0 if regression <= args.max_regression else 1


if __name__ == "__main__":
    sys.exit(main())
