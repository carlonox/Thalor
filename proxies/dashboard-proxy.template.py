#!/usr/bin/env python3
"""
dashboard-proxy.py - Custom WebSocket relay proxy for Hermes dashboard

Adds branding, authentication, and mood-based avatars to the default Hermes dashboard.

Requirements:
- aiohttp
- PyYAML
- Hermes agent running on HERMES_HOST:HERMES_PORT

Environment Variables:
- HERMES_HOST: Hermes gateway host (default: 127.0.0.1)
- HERMES_PORT: Hermes gateway port (default: 9119)
- DASHBOARD_PORT: Proxy port (default: 9999)
- DASHBOARD_USERNAME: Dashboard username
- DASHBOARD_PASSWORD: Dashboard password
- ASSETS_DIR: Path to custom assets (default: /opt/data/assets)

Usage:
    python3 dashboard-proxy.py
"""

import aiohttp
from aiohttp import web
import asyncio
import os
import traceback
import yaml

# Configuration from environment
HERMES_HOST = os.getenv("HERMES_HOST", "127.0.0.1")
HERMES_PORT = int(os.getenv("HERMES_PORT", "9119"))
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "9999"))
USERNAME = os.getenv("DASHBOARD_USERNAME", "agent")
PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")
ASSETS_DIR = os.getenv("ASSETS_DIR", "/opt/data/assets")
CONFIG_PATH = "/opt/data/config.yaml"

_session = None
_session_lock = asyncio.Lock()


async def get_session():
    """Get or create authenticated aiohttp session."""
    global _session
    
    if _session is None or _session.closed:
        async with _session_lock:
            # Double-check inside lock
            if _session is not None and not _session.closed:
                return _session
            
            jar = aiohttp.CookieJar(unsafe=True)
            _session = aiohttp.ClientSession(cookie_jar=jar)
            
            try:
                async with _session.post(
                    f"http://{HERMES_HOST}:{HERMES_PORT}/auth/password-login",
                    json={
                        "provider": "basic",
                        "username": USERNAME,
                        "password": PASSWORD,
                        "next": "",
                    },
                ) as resp:
                    print(f"[dashboard-proxy] Login status: {resp.status}", flush=True)
            except Exception as e:
                print(f"[dashboard-proxy] Login failed: {e}", flush=True)
    
    return _session


async def index(request):
    """Serve custom dashboard HTML."""
    return web.FileResponse(os.path.join(ASSETS_DIR, "index.html"))


async def ws_ticket(request):
    """Get WebSocket authentication ticket."""
    session = await get_session()
    async with session.post(
        f"http://{HERMES_HOST}:{HERMES_PORT}/api/auth/ws-ticket"
    ) as resp:
        data = await resp.json()
        return web.json_response({"ticket": data.get("ticket", "")})


async def mcp_servers(request):
    """Get MCP server configuration."""
    try:
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f)
        
        servers = config.get("mcp_servers", {})
        result = []
        
        for name, cfg in servers.items():
            result.append({
                "name": name,
                "enabled": cfg.get("enabled", False),
                "command": cfg.get("command", ""),
                "args": cfg.get("args", []),
            })
        
        return web.json_response({"servers": result})
    
    except Exception as e:
        return web.json_response({"servers": [], "error": str(e)})


async def proxy_api(request):
    """Proxy API requests to Hermes gateway."""
    try:
        session = await get_session()
        
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length")
        }
        
        body = await request.read()
        
        async with session.request(
            request.method,
            f"http://{HERMES_HOST}:{HERMES_PORT}{request.path_qs}",
            headers=headers,
            data=body if body else None,
        ) as resp:
            response_body = await resp.read()
            return web.Response(
                body=response_body,
                status=resp.status,
                content_type=resp.content_type
            )
    
    except Exception as e:
        print(f"[dashboard-proxy] proxy_api error: {e}", flush=True)
        traceback.print_exc()
        return web.json_response(
            {"error": str(e), "path": request.path_qs},
            status=502
        )


async def websocket_relay(request):
    """Relay WebSocket connections between browser and Hermes."""
    session = await get_session()
    
    # Get authentication ticket
    async with session.post(
        f"http://{HERMES_HOST}:{HERMES_PORT}/api/auth/ws-ticket"
    ) as resp:
        t_data = await resp.json()
        ticket = t_data.get("ticket", "")
    
    # Connect to internal WebSocket
    internal_ws_url = f"ws://{HERMES_HOST}:{HERMES_PORT}/api/ws?ticket={ticket}"
    
    async with session.ws_connect(internal_ws_url) as ws_hermes:
        ws_browser = web.WebSocketResponse()
        await ws_browser.prepare(request)
        
        async def browser_to_hermes():
            """Relay messages from browser to Hermes."""
            async for msg in ws_browser:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await ws_hermes.send_str(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    await ws_hermes.close()
                    break
        
        async def hermes_to_browser():
            """Relay messages from Hermes to browser."""
            async for msg in ws_hermes:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await ws_browser.send_str(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    await ws_browser.close()
                    break
        
        # Run both directions concurrently
        await asyncio.gather(browser_to_hermes(), hermes_to_browser())
    
    return ws_browser


def create_app():
    """Create and configure the web application."""
    app = web.Application()
    
    # Custom dashboard
    app.router.add_get("/", index)
    
    # WebSocket authentication
    app.router.add_get("/api/auth/ws-ticket", ws_ticket)
    app.router.add_get("/api/ws", websocket_relay)
    
    # API proxy (all /api/* routes)
    app.router.add_route("*", "/api/{tail:.*}", proxy_api)
    
    # MCP servers endpoint
    app.router.add_get("/mcp-servers", mcp_servers)
    
    # OpenAI-compatible endpoint (for tool calls)
    app.router.add_route("*", "/v1/{tail:.*}", proxy_api)
    
    # Static assets
    app.router.add_static("/", ASSETS_DIR, show_index=False)
    
    return app


if __name__ == "__main__":
    print(f"[dashboard-proxy] Serving on http://0.0.0.0:{DASHBOARD_PORT}", flush=True)
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=DASHBOARD_PORT, print=None)
