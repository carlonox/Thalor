# MCP Server Templates

Pre-configured templates for common MCP (Model Context Protocol) servers.

## Overview

MCP servers extend agent capabilities by providing specialized tools. These templates show how to configure popular MCP servers in your `config.yaml`.

## Available Templates

- **n8n** — Workflow automation
- **GNS3** — Network simulation
- **Packet Tracer** — Cisco network simulation
- **AgentMail** — Email management

## Usage

1. Copy the template to your `config.yaml` under `mcp_servers:`
2. Fill in the placeholders with your actual credentials
3. Restart your agent

## Security

- **Never commit credentials** to version control
- Use environment variables (`${VARIABLE}`) for sensitive data
- Store secrets in `.env` file (excluded from git)

## Example

```yaml
mcp_servers:
  n8n:
    enabled: true
    headers:
      Authorization: Bearer ${N8N_BEARER_TOKEN}
    url: ${N8N_URL}
```

## License

MIT
