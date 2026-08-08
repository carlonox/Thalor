#!/bin/bash
# =============================================================================
# Install Mnemosyne Memory Provider
# =============================================================================
# Helper script to install Mnemosyne in a Hermes container.
#
# The plugin registers via pip entry points in the Hermes venv
# (hermes_agent.memory_providers + hermes_agent.plugins) — NOT via a
# directory symlink. Verification is done by importing the package.
#
# Usage:
#   ./install-mnemosyne.sh <container_name>
#
# Example:
#   ./install-mnemosyne.sh thalor-agent
# =============================================================================

set -e

CONTAINER=${1:-"thalor-agent"}

echo "[install-mnemosyne] Installing Mnemosyne in container: $CONTAINER"

# Check if container exists
if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
    echo "[ERROR] Container '$CONTAINER' not found"
    exit 1
fi

# Check if Mnemosyne already installed (pip entry point in venv)
if docker exec "$CONTAINER" bash -c "/opt/hermes/.venv/bin/python -c 'import mnemosyne_hermes' 2>/dev/null" >/dev/null; then
    echo "[install-mnemosyne] Mnemosyne already installed"
else
    echo "[install-mnemosyne] Installing Mnemosyne package..."
    
    docker exec -u 0 "$CONTAINER" bash -c "
        cd /opt/hermes && \
        uv pip install 'mnemosyne-hermes' 'mnemosyne-memory[all]' --python /opt/hermes/.venv/bin/python && \
        chown -R hermes:hermes /opt/hermes/.venv
    " 2>&1
    
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install Mnemosyne"
        exit 1
    fi
    
    echo "[install-mnemosyne] Package installed"
fi

# Verify the pip entry point resolves (memory provider registration)
if docker exec "$CONTAINER" bash -c "/opt/hermes/.venv/bin/python -c 'import mnemosyne_hermes; print(\"OK\")'" >/dev/null 2>&1; then
    echo "[install-mnemosyne] Plugin entry point OK"
else
    echo "[install-mnemosyne] Plugin entry point missing — reinstalling..."
    docker exec -u 0 "$CONTAINER" bash -c "
        cd /opt/hermes && \
        uv pip install 'mnemosyne-hermes' 'mnemosyne-memory[all]' --python /opt/hermes/.venv/bin/python && \
        chown -R hermes:hermes /opt/hermes/.venv
    " 2>&1
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to reinstall Mnemosyne"
        exit 1
    fi
fi

echo "[install-mnemosyne] Restarting container to load the provider..."
docker restart "$CONTAINER"
sleep 15

echo "[install-mnemosyne] Installation complete"
