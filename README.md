# kvc-mcp

MCP access is included with every Krystal Voice Caller tier. Use this package to manage a tenant from Claude, Cursor, or any MCP-aware agent.

mcp-name: io.github.KrystalUnity/kvc-mcp

## Install

```bash
pip install kvc-mcp
```

## Configure

Create or rotate an API token in the Krystal Voice Caller dashboard, then set:

```bash
export KVC_API_TOKEN="kvc_token_..."
export KVC_BASE_URL="https://krystalunity.com/api/admin/kvc"
```

Cursor example:

```json
{
  "mcpServers": {
    "krystal-voice-caller": {
      "command": "kvc-mcp",
      "env": {
        "KVC_API_TOKEN": "kvc_token_..."
      }
    }
  }
}
```

## Tools

The server exposes tenant config, DNC, call history, reception captures, digest send-now, Script Author draft chat, contact upload, outbound captures, and test-call tools. Product availability is enforced by the Krystal Voice Caller API, so Reception-only tenants get inbound/reception tools and Bundle/Premium tenants get outbound Email Hunter tools.

Script approval is not exposed through MCP. Approval stays admin-only in the web UI.

## Publish

Operator-only steps:

1. `cd packages/kvc-mcp && uv build`
2. `uv publish --username __token__ --password "$PYPI_TOKEN"`
3. Submit an MCP Registry entry named `io.github.KrystalUnity/kvc-mcp` pointing at the PyPI package.
4. Verify from a fresh venv with `pip install kvc-mcp && kvc-mcp --help`.
