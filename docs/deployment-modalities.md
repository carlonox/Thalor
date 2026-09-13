# Swarm deployment modalities (template)

The skeleton runs in two modalities. Each project picks one in
`config/swarm.routing.json` → `deployment.mode`. Governance
(fingerprinted issues, PRs, required checks, mandatory human approval)
is identical in both; only *where the agents sleep* and *who wakes them*
differ.

## Modality A — local profiles (interactive development)

- Agents live as runtime profiles on the same machine where development
  happens (e.g., a local container).
- Wake: `post-commit` hook → `scripts/swarm_dispatch.py <range>`, which
  enqueues under `<queue_dir>/` and wakes the profile via CLI.
- Queue: a directory of JSON files (`<queue_dir>/`). If the runtime is
  off, jobs wait; each profile drains its queue on startup.
- Best for: projects with a human developing daily.

## Modality B — cloud 24/7 (continuous watch)

- Agents live on an always-on VM (e.g., a free-tier cloud instance). No
  local models: the brain is an LLM API whose keys live in a secrets
  manager (never in the repo).
- Wake: GitHub sends webhooks (push, pull_request, issues) to
  `scripts/swarm_webhook.py` on the VM, which verifies the HMAC
  signature, enqueues the job, and responds 200 in milliseconds.
  Thinking happens later, outside the request.
- The agent comments on the issue/PR with its machine user's PAT. It
  never closes or merges: as in A, approval is human.
- Best for: repos that need watching even when the PC is off.

## What changes per file by modality

| File | Modality A | Modality B |
|---|---|---|
| `swarm.routing.json` | `deployment.mode: "local"`, local `queue_dir` | `deployment.mode: "oracle"`, `queue_dir` on the VM, `webhook_secret` (secret name, never the value) |
| `swarm_dispatch.py` | active (post-commit hook) | inactive; replaced by the webhook |
| `swarm_webhook.py` | unused | active on the VM (verifies HMAC + enqueues) |
| `swarm-ci.yml` | same | same (deterministic checks always run in CI) |
| Profiles + PATs | one profile per agent in the local runtime | one service per agent on the VM + one secret per PAT |
| `CODEOWNERS` | same | same |

## Rules that DO NOT change

1. No bot closes issues or merges without human approval.
2. Writers only propose via PR within their `allowed_globs`.
3. `path-guard` is a required check: a PR out of scope does not merge.
4. Staggered PAT rotation + alert 14 days before expiry.
