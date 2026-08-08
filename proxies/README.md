# Dashboard Proxy Pattern

A custom WebSocket relay proxy that adds branding, authentication, and mood-based avatars to the Hermes dashboard.

## Overview

The default Hermes dashboard is functional but basic. This proxy pattern adds:

- **Custom branding** (logos, colors, fonts)
- **Mood-based avatars** (agent's emotional state reflected visually)
- **Simplified authentication** (single login for all endpoints)
- **Multi-agent support** (separate dashboards for each agent)
- **API aggregation** (all endpoints under one proxy)

## Architecture

```
┌─────────────────┐
│   Browser       │
│   (User)        │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│ Dashboard Proxy │ ← This pattern
│ (Port 9999)     │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│ Hermes Gateway  │
│ (Port 9119)     │
└─────────────────┘
```

## How It Works

### 1. Authentication Relay

The proxy logs into the Hermes gateway once on startup:

```python
async with session.post(
    f"http://{HERMES_HOST}:{HERMES_PORT}/auth/password-login",
    json={
        "provider": "basic",
        "username": USERNAME,
        "password": PASSWORD,
        "next": "",
    },
) as resp:
    # Session now has auth cookies
```

### 2. WebSocket Relay

For WebSocket connections, the proxy:
1. Requests a WS ticket from Hermes
2. Opens internal WebSocket to Hermes
3. Relays messages bidirectionally between browser and Hermes

```python
async def websocket_relay(request):
    # Get ticket
    async with session.post(f"http://{HERMES_HOST}:{HERMES_PORT}/api/auth/ws-ticket") as resp:
        ticket = (await resp.json()).get("ticket", "")
    
    # Connect to internal WS
    internal_ws_url = f"ws://{HERMES_HOST}:{HERMES_PORT}/api/ws?ticket={ticket}"
    async with session.ws_connect(internal_ws_url) as ws_hermes:
        ws_browser = web.WebSocketResponse()
        await ws_browser.prepare(request)
        
        # Bidirectional relay
        async def browser_to_hermes():
            async for msg in ws_browser:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await ws_hermes.send_str(msg.data)
        
        async def hermes_to_browser():
            async for msg in ws_hermes:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await ws_browser.send_str(msg.data)
        
        await asyncio.gather(browser_to_hermes(), hermes_to_browser())
```

### 3. API Proxy

All other API calls are proxied transparently:

```python
async def proxy_api(request):
    headers = {k: v for k, v in request.headers.items() 
               if k.lower() not in ("host", "content-length")}
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
```

## Edge Cases

### Proxy Behavior (Passive)

- **No server-side reconnect:** If the internal WebSocket drops, the proxy closes the browser connection
- **No retry logic:** The proxy doesn't attempt to reconnect to Hermes
- **No backoff:** Failed connections fail immediately

### Browser Behavior (Active)

The browser-side JavaScript implements:
- **Exponential backoff:** `base * 2^attempts`, capped at 30s
- **Jitter:** ±30% randomization to prevent thundering herd
- **Max attempts:** 15 retries before giving up
- **Cooldown:** 120s wait before retrying from scratch

```javascript
const RECONNECT = {
  base: 500,           // Initial delay (ms)
  max: 30000,          // Max delay (ms)
  maxAttempts: 15,     // Max retries
  jitter: 0.3          // ±30% randomization
};
```

### What Happens When Gateway Crashes?

1. Internal WebSocket drops
2. Proxy closes browser WebSocket
3. Browser detects disconnection
4. Browser schedules reconnect with backoff
5. Browser retries up to 15 times
6. If gateway recovers within ~30s, connection restored
7. If gateway doesn't recover, browser gives up after 15 attempts

## Multi-Agent Support

To support multiple agents, run separate proxy instances:

```bash
# Agent 1 (default)
python3 dashboard-proxy.py --port 9999 --agent-name "Atlas"

# Agent 2 (ops)
python3 dashboard-proxy.py --port 9250 --agent-name "Ops"
```

Each proxy has its own:
- Port
- Authentication credentials
- Custom HTML/CSS
- Avatar assets

## Security Considerations

- **Credentials in environment:** Never hardcode usernames/passwords
- **HTTPS in production:** Use reverse proxy (nginx) with TLS
- **Rate limiting:** Add rate limiting for public deployments
- **CORS:** Configure CORS headers if serving from different domain

## Customization

### Branding

Edit the HTML template (`assets/index.html`):
- Logo and favicon
- Color scheme
- Font families
- Layout

### Moods

Add mood-specific avatars:
```
assets/
  avatar-neutral.png
  avatar-happy.png
  avatar-focused.png
  avatar-tired.png
  avatar-proud.png
```

The dashboard detects `[mood: xxx]` tags in agent responses and switches avatars automatically.

## License

MIT
