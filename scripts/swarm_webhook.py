#!/usr/bin/env python3
"""swarm_webhook.py — GitHub webhook receiver for modality B.

Lives on the 24/7 VM. Verifies the webhook's HMAC signature, enqueues the
job under <queue_dir>/ and responds 200 fast. Thinking happens later,
outside the request, with the API brain configured on the VM.

Secrets: the webhook secret and the PATs are read from the ENVIRONMENT
(injected from the VM's secrets manager). They never go in the repo nor
on disk.

Usage: SWARM_WEBHOOK_SECRET=<v> QUEUE_DIR=.swarm/queue python3 swarm_webhook.py [port]
Stdlib skeleton — per-agent dispatch plugs in where the TODO says.
"""
import hashlib
import hmac
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

QUEUE = Path(os.environ.get("QUEUE_DIR", ".swarm/queue"))
SECRET = os.environ.get("SWARM_WEBHOOK_SECRET", "").encode()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silent: the VM already has its logs
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        sig = self.headers.get("X-Hub-Signature-256", "")
        if SECRET:
            want = "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(want, sig):
                self.send_response(401)
                self.end_headers()
                return
        try:
            event = self.headers.get("X-GitHub-Event", "unknown")
            payload = json.loads(body or b"{}")
            QUEUE.mkdir(parents=True, exist_ok=True)
            fid = hashlib.sha256(body).hexdigest()[:12]
            job = {"event": event, "ts": time.time(),
                   "repo": (payload.get("repository") or {}).get("full_name"),
                   "ref": payload.get("ref"),
                   "action": payload.get("action")}
            (QUEUE / f"webhook.{fid}.json").write_text(json.dumps(job),
                                                       encoding="utf-8")
            # TODO: wake the agent according to routing (dispatch.priority)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"queued": true}')
        except Exception:  # noqa: BLE001 — the webhook must never go down
            self.send_response(500)
            self.end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8099
    print(f"swarm_webhook: listening on :{port}, queue at {QUEUE}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
