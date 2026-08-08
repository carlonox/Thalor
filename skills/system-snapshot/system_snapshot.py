#!/usr/bin/env python3
"""
system_snapshot.py - Extract current system state for auditing and documentation

Generates a comprehensive JSON snapshot of:
- Docker container status
- Available LLM models (Ollama)
- MCP server configuration
- Mnemosyne memory statistics
- Image versions and digests
- Network configuration

Output: /opt/data/shared/system_snapshot.json
"""

import json
import subprocess
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
import yaml

try:
    import requests
except ImportError:
    print("[ERROR] requests not installed. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


def run_command(cmd: str, timeout: int = 10) -> tuple[int, str]:
    """Run a shell command and return (exit_code, output)."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT"
    except Exception as e:
        return 1, str(e)


def get_docker_containers() -> dict:
    """Get status of all Docker containers."""
    containers = {}
    
    # Check if docker socket is accessible
    exit_code, output = run_command("docker ps --format '{{.Names}}|{{.Status}}|{{.Image}}'")
    
    if exit_code != 0:
        return {"error": "Docker socket not accessible", "containers": {}}
    
    for line in output.split('\n'):
        if not line:
            continue
        parts = line.split('|')
        if len(parts) >= 3:
            name, status, image = parts[0], parts[1], parts[2]
            
            # Check health status
            health_exit, health_output = run_command(
                f"docker inspect --format='{{{{.State.Health.Status}}}}' {name}"
            )
            health = health_output if health_exit == 0 else "unknown"
            
            containers[name] = {
                "status": "running" if "Up" in status else "stopped",
                "health": health,
                "image": image,
                "uptime": status
            }
    
    return {"containers": containers}


def get_ollama_models() -> dict:
    """Get list of available Ollama models."""
    try:
        response = requests.get("http://host.docker.internal:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = []
            for model in data.get("models", []):
                models.append({
                    "name": model.get("name"),
                    "size": f"{model.get('size', 0) / 1e9:.2f}GB",
                    "modified": model.get("modified_at"),
                    "digest": model.get("digest", "")[:12]
                })
            return {"ollama": models}
    except Exception as e:
        return {"ollama": {"error": str(e)}}
    
    return {"ollama": []}


def get_mcp_servers() -> dict:
    """Get MCP server configuration from config.yaml."""
    config_path = Path("/opt/data/config.yaml")
    
    if not config_path.exists():
        return {"error": "config.yaml not found"}
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        mcp_servers = config.get("mcp_servers", {})
        servers = {}
        
        for name, cfg in mcp_servers.items():
            servers[name] = {
                "enabled": cfg.get("enabled", False),
                "command": cfg.get("command", ""),
                "url": cfg.get("url", "")
            }
        
        return {"mcp_servers": servers}
    
    except Exception as e:
        return {"error": str(e)}


def get_memory_stats() -> dict:
    """Get Mnemosyne memory statistics."""
    db_path = Path("/opt/data/mnemosyne/data/mnemosyne.db")
    
    if not db_path.exists():
        return {"error": "Mnemosyne database not found"}
    
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count working memories
        cursor.execute("SELECT COUNT(*) FROM working_memories")
        working = cursor.fetchone()[0]
        
        # Count episodic memories
        cursor.execute("SELECT COUNT(*) FROM episodic_memories")
        episodic = cursor.fetchone()[0]
        
        # Count embeddings
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        embeddings = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "provider": "mnemosyne",
            "working": working,
            "episodic": episodic,
            "embeddings": embeddings,
            "db_size": f"{db_path.stat().st_size / 1e6:.2f}MB"
        }
    
    except Exception as e:
        return {"error": str(e)}


def get_network_info() -> dict:
    """Get Docker network information."""
    exit_code, output = run_command(
        "docker network inspect thalor-net --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}'"
    )
    
    if exit_code == 0:
        return {
            "bridge": "thalor-net",
            "subnet": output
        }
    
    return {"error": "Network not found or not accessible"}


def main():
    """Generate system snapshot."""
    print("[system_snapshot] Generating system snapshot...", file=sys.stderr)
    
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "containers": get_docker_containers(),
        "models": get_ollama_models(),
        "mcp_servers": get_mcp_servers(),
        "memory": get_memory_stats(),
        "network": get_network_info()
    }
    
    output_path = Path("/opt/data/shared/system_snapshot.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"[system_snapshot] Snapshot saved to {output_path}", file=sys.stderr)
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
