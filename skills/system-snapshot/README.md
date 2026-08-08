# System Snapshot Skill

Extracts the current state of the Thalor system for auditing, documentation, and health monitoring.

## Overview

This skill generates a comprehensive JSON snapshot of:
- Docker container status
- Available LLM models (Ollama)
- MCP server configuration
- Mnemosyne memory statistics
- Image versions and digests
- Network configuration

## Usage

```bash
python3 /opt/data/skills/system-snapshot/system_snapshot.py
```

## Output

Generates `/opt/data/shared/system_snapshot.json` with the following structure:

```json
{
  "timestamp": "2026-08-08T12:34:56Z",
  "containers": {
    "hermes": {"status": "running", "health": "healthy", "image": "nousresearch/hermes-agent:latest"},
    "hermes-ops": {"status": "running", "health": "healthy", "image": "nousresearch/hermes-agent:latest"},
    "freellmapi": {"status": "running", "health": "healthy", "image": "ghcr.io/tashfeenahmed/freellmapi:latest"}
  },
  "models": {
    "ollama": [
      {"name": "qwen3.5:4b", "size": "3.39GB", "capabilities": ["vision", "tools"]},
      {"name": "qwen3:8b", "size": "5.23GB", "capabilities": ["completion", "tools"]}
    ]
  },
  "mcp_servers": {
    "n8n": {"enabled": true, "url": "http://host.docker.internal:5678/mcp-server/http"},
    "gns3-mcp": {"enabled": true, "host": "${GNS3_HOST}", "port": 3080}
  },
  "memory": {
    "provider": "mnemosyne",
    "working": 933,
    "episodic": 26,
    "embeddings": 1165
  },
  "network": {
    "bridge": "thalor-net",
    "subnet": "${THALOR_NET_SUBNET}"
  }
}
```

## Use Cases

- **Health monitoring:** Check if all services are running
- **Documentation:** Auto-generate architecture docs
- **Debugging:** Identify misconfigurations
- **Backups:** Include in backup metadata

## Requirements

- Docker socket access (optional, for container inspection)
- Ollama running on `http://host.docker.internal:11434`
- Read access to `/opt/data/config.yaml`

## License

MIT
