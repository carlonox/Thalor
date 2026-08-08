<#
.SYNOPSIS
    Thalor Manager v1.0 — Unified Control Panel (Docker Compose Edition)
.DESCRIPTION
    Starts, restarts, and stops Thalor agents using Docker Compose.
    
    Supports:
    - Single agent (default)
    - Multi-agent (with Ops)
    - FreeLLMAPI router (optional)
#>

try {
    $Host.UI.RawUI.WindowTitle = "Thalor - Control Panel v1.0"

    # ============================================================
    # CONFIGURATION
    # ============================================================
    $script:DataDir      = ".\data"
    $script:OpsDataDir   = ".\data-ops"
    $script:SharedDir    = ".\shared"
    $script:VaultDir     = ".\vault"
    $script:ComposeFile  = ".\docker-compose.yml"

    # ============================================================
    # HELPER FUNCTIONS
    # ============================================================

    function Initialize-Directories {
        Write-Host "  [Init] Creating directories..." -ForegroundColor Cyan

        $dirs = @($script:DataDir, $script:OpsDataDir, $script:SharedDir, $script:VaultDir)
        foreach ($d in $dirs) {
            if (-not (Test-Path $d)) {
                New-Item -ItemType Directory -Force -Path $d | Out-Null
                Write-Host "    Created: $d" -ForegroundColor DarkGray
            }
        }

        # Create shared subdirectories
        $sharedDirs = @(
            "$script:SharedDir\docs_arquitectura",
            "$script:SharedDir\kanban",
            "$script:SharedDir\kanban\boards"
        )
        foreach ($d in $sharedDirs) {
            if (-not (Test-Path $d)) {
                New-Item -ItemType Directory -Force -Path $d | Out-Null
            }
        }

        Write-Host "    Directories OK" -ForegroundColor Green
    }

    function Start-Docker {
        Write-Host "  [Docker] Checking..." -ForegroundColor Cyan
        docker info 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    Starting Docker Desktop..." -ForegroundColor Yellow
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            do {
                Start-Sleep -Seconds 5
                docker info 2>&1 | Out-Null
                Write-Host "    Waiting for Docker..." -ForegroundColor DarkGray
            } while ($LASTEXITCODE -ne 0)
        }
        Write-Host "    Docker OK" -ForegroundColor Green
    }

    function Install-Mnemosyne {
        param([string]$Container, [string]$Label)

        Write-Host "    [$Label] Checking Mnemosyne..." -ForegroundColor DarkGray

        # Verify pip entry point in venv (NOT a directory)
        $mnemosyneInstalled = docker exec $Container bash -c "/opt/hermes/.venv/bin/python -c 'import mnemosyne_hermes' 2>/dev/null && echo yes || echo no"
        if ($mnemosyneInstalled -match "no") {
            Write-Host "    [$Label] Mnemosyne not installed. Installing..." -ForegroundColor Yellow
            docker exec -u 0 $Container bash -c "cd /opt/hermes && uv pip install 'mnemosyne-hermes' 'mnemosyne-memory[all]' --python /opt/hermes/.venv/bin/python && chown -R hermes:hermes /opt/hermes/.venv" 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "    [$Label] ERROR: Failed to install Mnemosyne" -ForegroundColor Red
                return
            }
            Write-Host "    [$Label] Mnemosyne installed. Restarting container..." -ForegroundColor Green
            docker restart $Container | Out-Null
            Start-Sleep -Seconds 15
        } else {
            Write-Host "    [$Label] Mnemosyne OK" -ForegroundColor Green
        }
    }

    # ============================================================
    # START FUNCTIONS
    # ============================================================

    function Start-Agent {
        param([string]$ServiceName, [string]$Label)

        Write-Host "  [$Label] Starting with Docker Compose..." -ForegroundColor Cyan
        
        docker compose -f $script:ComposeFile up -d $ServiceName 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    $Label OK" -ForegroundColor Green
            Start-Sleep -Seconds 15
            return $true
        } else {
            Write-Host "    ERROR starting $Label" -ForegroundColor Red
            return $false
        }
    }

    function Start-MainAgent {
        $ok = Start-Agent -ServiceName "hermes" -Label "Main Agent"
        if (-not $ok) { return }

        # Check vault
        Write-Host "    Checking vault..." -ForegroundColor DarkGray
        $vaultOk = docker exec hermes bash -c "if [ -d /mnt/vault ]; then echo OK; else echo NO; fi" 2>&1
        if ($vaultOk -match "OK") { Write-Host "    Vault OK" -ForegroundColor Green } else { Write-Host "    Vault NOT mounted" -ForegroundColor Red }

        # Ollama
        $ollamaRunning = $false
        try { $null = curl.exe -s --max-time 5 http://localhost:11434/api/tags; $ollamaRunning = $true } catch {}
        if (-not $ollamaRunning) {
            Write-Host "    Starting Ollama..." -ForegroundColor Yellow
            $env:OLLAMA_HOST = "0.0.0.0"
            Start-Process "ollama" -ArgumentList "serve" -PassThru -WindowStyle Hidden | Out-Null
            Start-Sleep -Seconds 10
        } else { Write-Host "    Ollama OK" -ForegroundColor Green }

        Install-Mnemosyne -Container "hermes" -Label "Main Agent"

        # Dashboard proxy runs as a compose service (dashboard-proxy on 9999)
        # — no docker exec needed. Just verify it's up:
        try {
            $status = curl.exe -s -o NUL -w "%{http_code}" --max-time 10 http://localhost:9999/
            if ($status -eq "200") { Write-Host "    Dashboard: http://localhost:9999" -ForegroundColor Green }
            else {
                Write-Host "    Dashboard proxy starting (compose service)..." -ForegroundColor Yellow
                docker compose -f $script:ComposeFile up -d dashboard-proxy 2>&1 | Out-Null
                Start-Sleep -Seconds 5
                $status = curl.exe -s -o NUL -w "%{http_code}" --max-time 10 http://localhost:9999/
                if ($status -eq "200") { Write-Host "    Dashboard: http://localhost:9999" -ForegroundColor Green }
                else { Write-Host "    Dashboard NOT responding" -ForegroundColor Red }
            }
        } catch { Write-Host "    Dashboard NOT responding" -ForegroundColor Red }
    }

    function Start-OpsAgent {
        $ok = Start-Agent -ServiceName "hermes-ops" -Label "Ops Agent"
        if (-not $ok) { return }

        try {
            $status = curl.exe -s -o NUL -w "%{http_code}" --max-time 10 http://localhost:9219/
            if ($status -eq "200" -or $status -eq "302") { Write-Host "    Ops Dashboard: http://localhost:9219" -ForegroundColor Green }
        } catch { Write-Host "    Ops Dashboard NOT responding" -ForegroundColor Red }
    }

    function Start-Router {
        $ok = Start-Agent -ServiceName "freellmapi" -Label "Router"
        if (-not $ok) { return }
        try {
            $status = curl.exe -s -o NUL -w "%{http_code}" --max-time 5 http://localhost:3000
            if ($status -eq "200" -or $status -eq "302" -or $status -eq "401") {
                Write-Host "    Router: http://localhost:3000" -ForegroundColor Green
            }
        } catch {}
    }

    # ============================================================
    # STOP FUNCTION
    # ============================================================

    function Stop-Agent {
        param([string]$ServiceName, [string]$Label)

        Write-Host "  [$Label] Stopping..." -ForegroundColor Red
        docker compose -f $script:ComposeFile stop $ServiceName 2>&1 | Out-Null
        Write-Host "    Container stopped" -ForegroundColor Yellow
    }

    # ============================================================
    # MENU
    # ============================================================

    Write-Host ""
    Write-Host "  ========================================" -ForegroundColor Magenta
    Write-Host "   THALOR - CONTROL PANEL v1.0" -ForegroundColor Magenta
    Write-Host "  ========================================" -ForegroundColor Magenta
    Write-Host ""

    Write-Host "  Agent:" -ForegroundColor Cyan
    Write-Host "  [1] Main Agent only"
    Write-Host "  [2] Main + Ops Agents"
    Write-Host "  [3] Full Stack (Main + Ops + Router)"
    $agentChoice = Read-Host "Option (1-3)"

    Write-Host ""
    Write-Host "  Action:" -ForegroundColor Cyan
    Write-Host "  [1] Start"
    Write-Host "  [2] Restart"
    Write-Host "  [3] Stop"
    $actionChoice = Read-Host "Option (1-3)"
    Write-Host ""

    if ($actionChoice -eq "1" -or $actionChoice -eq "2") {
        Start-Docker
        Initialize-Directories
        
        if ($agentChoice -eq "3") { Start-Router }
        Start-MainAgent
        
        if ($agentChoice -eq "2" -or $agentChoice -eq "3") {
            Start-OpsAgent
        }

        Write-Host ""
        Write-Host "  ========================================" -ForegroundColor Green
        Write-Host "   COMPLETED" -ForegroundColor Green
        Write-Host "  ========================================" -ForegroundColor Green
        Write-Host "  Main Agent: http://localhost:9999" -ForegroundColor Cyan
        if ($agentChoice -eq "2" -or $agentChoice -eq "3") {
            Write-Host "  Ops Agent:  http://localhost:9219" -ForegroundColor DarkCyan
        }
        if ($agentChoice -eq "3") {
            Write-Host "  Router:     http://localhost:3000" -ForegroundColor Green
        }
        Write-Host "  ========================================" -ForegroundColor Green

    } elseif ($actionChoice -eq "3") {
        if ($agentChoice -eq "1") {
            Stop-Agent -ServiceName "hermes" -Label "Main Agent"
        } elseif ($agentChoice -eq "2") {
            Stop-Agent -ServiceName "hermes" -Label "Main Agent"
            Stop-Agent -ServiceName "hermes-ops" -Label "Ops Agent"
        } elseif ($agentChoice -eq "3") {
            Stop-Agent -ServiceName "hermes" -Label "Main Agent"
            Stop-Agent -ServiceName "hermes-ops" -Label "Ops Agent"
            Stop-Agent -ServiceName "freellmapi" -Label "Router"
        }
        Write-Host "  Shutdown completed." -ForegroundColor Red

    } else {
        Write-Host "Invalid option" -ForegroundColor Red
    }

} catch {
    Write-Host ""
    Write-Host "  ========================================" -ForegroundColor Red
    Write-Host "   ERROR" -ForegroundColor Red
    Write-Host "  ========================================" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Press Enter to close."
Read-Host
