#!/usr/bin/env python3
"""swarm_dispatch.py — dispatcher post-commit del enjambre (stdlib only).

Modelo: el hook escribe SIEMPRE en shared/ops_queue/ (persistencia primero);
el wake al container es best-effort. Cada perfil drena su cola al arrancar.
Locks atómicos O_EXCL en shared/ops_locks/ con TTL anti-huérfanos.

Uso: python scripts/swarm_dispatch.py HEAD~1..HEAD [--dry-run]
"""
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.environ.get("HERMES_SHARED", os.path.join(REPO, ".swarm"))
QUEUE = os.path.join(SHARED, "ops_queue")
LOCKS = os.path.join(SHARED, "ops_locks")
CFG_PATH = os.path.join(REPO, "config", "swarm.routing.json")
LOCK_TTL = 30 * 60


def seg_match(pat, path):
    ps, qs = pat.split("/"), path.split("/")
    return _m(ps, qs)


def _m(ps, qs):
    if not ps:
        return not qs
    if ps[0] == "**":
        return any(_m(ps[1:], qs[i:]) for i in range(len(qs) + 1))
    if not qs:
        return False
    return fnmatch.fnmatchcase(qs[0], ps[0]) and _m(ps[1:], qs[1:])


def match(path, globs):
    return any(seg_match(g, path) for g in globs)


def acquire(name):
    os.makedirs(LOCKS, exist_ok=True)
    p = os.path.join(LOCKS, name)
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        try:
            if time.time() - os.path.getmtime(p) > LOCK_TTL:
                os.remove(p)
                return acquire(name)
        except OSError:
            pass
        return False


def log(msg):
    try:
        with open(os.path.join(SHARED, "ops-dispatch.log"), "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass
    print(msg)


def run(agent, job):
    if not acquire(agent + ".lock"):
        return False
    try:
        subprocess.Popen(
            ["hermes", "-p", agent, "chat", "-q", job["brief"]],
            stdout=open(os.path.join(SHARED, f"ops-{agent}.log"), "ab"),
            stderr=subprocess.STDOUT, start_new_session=True)
        return True
    except Exception as e:  # noqa: BLE001 — wake best-effort
        log(f"wake {agent} falló (queda encolado): {e}")
        try:
            os.remove(os.path.join(LOCKS, agent + ".lock"))
        except OSError:
            pass
        return False


def main():
    if len(sys.argv) < 2:
        print("uso: swarm_dispatch.py <rango> [--dry-run]")
        return 2
    rng, dry = sys.argv[1], "--dry-run" in sys.argv
    os.makedirs(QUEUE, exist_ok=True)
    with open(CFG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    out = subprocess.run(["git", "diff", "--name-only", rng],
                         capture_output=True, text=True, cwd=REPO)
    files = [l.strip() for l in out.stdout.splitlines() if l.strip()]
    agents = cfg.get("agents", {})
    hits = {a: [p for p in files if match(p, c.get("dispatch_globs", []))]
            for a, c in agents.items() if c.get("dispatch_globs")}
    eligible = [a for a, ps in hits.items() if ps]
    if len(eligible) >= 3:
        log(f"commit multi-dominio ({len(eligible)}) -> solo ops-watch")
        eligible = ["ops-watch"] if "ops-watch" in hits else []
    else:
        prio = cfg.get("dispatch", {}).get("priority", eligible)
        mx = cfg.get("dispatch", {}).get("max_agents_per_commit", 2)
        eligible = [a for a in prio if a in eligible][:mx]
    if not eligible:
        log(f"dispatch {rng}: sin agentes ({len(files)} archivos)")
        return 0
    for a in eligible:
        job = {"files": hits.get(a, []), "range": rng, "ts": time.time(),
               "brief": f"review post-commit {rng}; files: "
                        f"{', '.join(hits.get(a, [])[:20])}"}
        fid = hashlib.sha256(json.dumps(job, sort_keys=True).encode()).hexdigest()[:12]
        path = os.path.join(QUEUE, f"{a}.{fid}.json")
        if not dry:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(job, f)
        log(f"dispatch {rng}: {a} <- {len(hits.get(a, []))} archivos"
            f"{' (dry-run)' if dry else ''}")
        if not dry:
            run(a, job)
    return 0


if __name__ == "__main__":
    sys.exit(main())
