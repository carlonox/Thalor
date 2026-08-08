#!/bin/bash
# =============================================================================
# Thalor Manager v1.0 — Unified Control Panel (Docker Compose Edition)
# =============================================================================
# Starts, restarts, and stops Thalor agents using Docker Compose.
#
# Supports:
# - Single agent (default)
# - Multi-agent (with Ops)
# - FreeLLMAPI router (optional)
#
# Usage:
#   ./start.sh
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DATA_DIR="./data"
OPS_DATA_DIR="./data-ops"
SHARED_DIR="./shared"
VAULT_DIR="./vault"
COMPOSE_FILE="./docker-compose.yml"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

initialize_directories() {
    echo -e "  ${CYAN}[Init]${NC} Creating directories..."
    
    mkdir -p "$DATA_DIR" "$OPS_DATA_DIR" "$SHARED_DIR" "$VAULT_DIR"
    mkdir -p "$SHARED_DIR/docs_arquitectura" "$SHARED_DIR/kanban/boards"
    
    echo -e "    ${GREEN}Directories OK${NC}"
}

start_docker() {
    echo -e "  ${CYAN}[Docker]${NC} Checking..."
    
    if ! docker info >/dev/null 2>&1; then
        echo -e "    ${YELLOW}Starting Docker...${NC}"
        
        # Linux: systemctl
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl start docker
        # macOS: open Docker.app
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            open -a Docker
        fi
        
        # Wait for Docker
        while ! docker info >/dev/null 2>&1; do
            echo -e "    Waiting for Docker..."
            sleep 5
        done
    fi
    
    echo -e "    ${GREEN}Docker OK${NC}"
}

install_mnemosyne() {
    local container=$1
    local label=$2
    
    echo -e "    ${CYAN}[$label]${NC} Checking Mnemosyne..."
    
    # Check if installed (pip entry point in venv — NOT a directory)
    if ! docker exec "$container" bash -c "/opt/hermes/.venv/bin/python -c 'import mnemosyne_hermes' 2>/dev/null" >/dev/null; then
        echo -e "    ${YELLOW}[$label] Mnemosyne not installed. Installing...${NC}"
        
        docker exec -u 0 "$container" bash -c "
            cd /opt/hermes && \
            uv pip install 'mnemosyne-hermes' 'mnemosyne-memory[all]' --python /opt/hermes/.venv/bin/python && \
            chown -R hermes:hermes /opt/hermes/.venv
        " 2>&1
        
        if [ $? -ne 0 ]; then
            echo -e "    ${RED}[$label] ERROR: Failed to install Mnemosyne${NC}"
            return 1
        fi
        
        echo -e "    ${GREEN}[$label] Mnemosyne installed. Restarting container...${NC}"
        docker restart "$container" >/dev/null
        sleep 15
    else
        echo -e "    ${GREEN}[$label] Mnemosyne OK${NC}"
    fi
}

# =============================================================================
# START FUNCTIONS
# =============================================================================

start_agent() {
    local service_name=$1
    local label=$2
    
    echo -e "  ${CYAN}[$label]${NC} Starting with Docker Compose..."
    
    docker compose -f "$COMPOSE_FILE" up -d "$service_name" >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo -e "    ${GREEN}$label OK${NC}"
        sleep 15
        return 0
    else
        echo -e "    ${RED}ERROR starting $label${NC}"
        return 1
    fi
}

start_main_agent() {
    start_agent "hermes" "Main Agent" || return 1
    
    # Check vault
    echo -e "    Checking vault..."
    if docker exec hermes bash -c "[ -d /mnt/vault ]" 2>/dev/null; then
        echo -e "    ${GREEN}Vault OK${NC}"
    else
        echo -e "    ${RED}Vault NOT mounted${NC}"
    fi
    
    # Ollama
    if ! curl -s --max-time 5 http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "    ${YELLOW}Starting Ollama...${NC}"
        OLLAMA_HOST=0.0.0.0 ollama serve >/dev/null 2>&1 &
        sleep 10
    else
        echo -e "    ${GREEN}Ollama OK${NC}"
    fi
    
    install_mnemosyne "hermes" "Main Agent"
    
    # Dashboard proxy runs as a compose service (dashboard-proxy on port 9999)
    # — no docker exec needed. Just verify it's up:
    if curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://localhost:9999/ | grep -q "200"; then
        echo -e "    ${GREEN}Dashboard: http://localhost:9999${NC}"
    else
        echo -e "    ${YELLOW}Dashboard proxy starting (compose service)...${NC}"
        docker compose -f "$COMPOSE_FILE" up -d dashboard-proxy >/dev/null 2>&1 || true
        sleep 5
        if curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://localhost:9999/ | grep -q "200"; then
            echo -e "    ${GREEN}Dashboard: http://localhost:9999${NC}"
        else
            echo -e "    ${RED}Dashboard NOT responding${NC}"
        fi
    fi
}

start_ops_agent() {
    start_agent "hermes-ops" "Ops Agent" || return 1
    
    if curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://localhost:9219/ | grep -qE "200|302"; then
        echo -e "    ${GREEN}Ops Dashboard: http://localhost:9219${NC}"
    else
        echo -e "    ${RED}Ops Dashboard NOT responding${NC}"
    fi
}

start_router() {
    start_agent "freellmapi" "Router" || return 1
    
    if curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:3000 | grep -qE "200|302|401"; then
        echo -e "    ${GREEN}Router: http://localhost:3000${NC}"
    fi
}

# =============================================================================
# STOP FUNCTION
# =============================================================================

stop_agent() {
    local service_name=$1
    local label=$2
    
    echo -e "  ${RED}[$label]${NC} Stopping..."
    docker compose -f "$COMPOSE_FILE" stop "$service_name" >/dev/null 2>&1
    echo -e "    ${YELLOW}Container stopped${NC}"
}

# =============================================================================
# MENU
# =============================================================================

echo ""
echo -e "  ${MAGENTA}========================================${NC}"
echo -e "  ${MAGENTA} THALOR - CONTROL PANEL v1.0${NC}"
echo -e "  ${MAGENTA}========================================${NC}"
echo ""

echo -e "  ${CYAN}Agent:${NC}"
echo "  [1] Main Agent only"
echo "  [2] Main + Ops Agents"
echo "  [3] Full Stack (Main + Ops + Router)"
read -p "Option (1-3): " agent_choice

echo ""
echo -e "  ${CYAN}Action:${NC}"
echo "  [1] Start"
echo "  [2] Restart"
echo "  [3] Stop"
read -p "Option (1-3): " action_choice
echo ""

if [[ "$action_choice" == "1" || "$action_choice" == "2" ]]; then
    start_docker
    initialize_directories
    
    [[ "$agent_choice" == "3" ]] && start_router
    start_main_agent
    
    if [[ "$agent_choice" == "2" || "$agent_choice" == "3" ]]; then
        start_ops_agent
    fi
    
    echo ""
    echo -e "  ${GREEN}========================================${NC}"
    echo -e "  ${GREEN} COMPLETED${NC}"
    echo -e "  ${GREEN}========================================${NC}"
    echo -e "  ${CYAN}Main Agent:${NC} http://localhost:9999"
    
    if [[ "$agent_choice" == "2" || "$agent_choice" == "3" ]]; then
        echo -e "  ${CYAN}Ops Agent:${NC}  http://localhost:9219"
    fi
    
    if [[ "$agent_choice" == "3" ]]; then
        echo -e "  ${GREEN}Router:${NC}     http://localhost:3000"
    fi
    
    echo -e "  ${GREEN}========================================${NC}"

elif [[ "$action_choice" == "3" ]]; then
    if [[ "$agent_choice" == "1" ]]; then
        stop_agent "hermes" "Main Agent"
    elif [[ "$agent_choice" == "2" ]]; then
        stop_agent "hermes" "Main Agent"
        stop_agent "hermes-ops" "Ops Agent"
    elif [[ "$agent_choice" == "3" ]]; then
        stop_agent "hermes" "Main Agent"
        stop_agent "hermes-ops" "Ops Agent"
        stop_agent "freellmapi" "Router"
    fi
    
    echo -e "  ${RED}Shutdown completed.${NC}"

else
    echo -e "  ${RED}Invalid option${NC}"
fi

echo ""
read -p "Press Enter to close."
