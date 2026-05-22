from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import httpx
import pytest

PACKAGE_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))


def _reload_server(monkeypatch):
    monkeypatch.setenv("KVC_API_TOKEN", "kvc_token_ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    monkeypatch.setenv("KVC_BASE_URL", "https://krystalunity.com/api/admin/kvc")
    sys.modules.pop("kvc_mcp.server", None)
    return importlib.import_module("kvc_mcp.server")


@pytest.mark.asyncio
async def test_mcp_tool_calls_send_bearer_header(monkeypatch):
    server = _reload_server(monkeypatch)
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization")
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"tenant_id": "tenant-a", "company_name": "Acme"})

    monkeypatch.setattr(server, "_tenant_id", lambda: "tenant-a")
    monkeypatch.setattr(server, "_client", lambda: httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    payload = await server.kvc_get_tenant()

    assert seen["authorization"] == "Bearer kvc_token_ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    assert seen["url"] == "https://krystalunity.com/api/admin/kvc/tenant-a"
    assert json.loads(payload)["tenant_id"] == "tenant-a"


def test_mcp_tool_403_returns_human_readable_capability_message(monkeypatch):
    server = _reload_server(monkeypatch)
    request = httpx.Request("GET", "https://example.test")
    response = httpx.Response(
        403,
        request=request,
        json={"detail": {"code": "product_required", "product": "email_hunter"}},
    )

    message = server._format_error(httpx.HTTPStatusError("forbidden", request=request, response=response))

    assert "requires the email_hunter product" in message
    assert "upgrade" in message.lower()
    assert "https://krystalunity.com/voice/krystal-caller/dashboard/billing" in message


def test_registered_tools_include_all_stream_l_tools(monkeypatch):
    server = _reload_server(monkeypatch)

    tool_names = {tool.name for tool in server.mcp._tool_manager.list_tools()}

    assert {
        "kvc_get_tenant",
        "kvc_update_tenant",
        "kvc_list_dnc",
        "kvc_add_dnc",
        "kvc_call_history",
        "kvc_after_hours_captures",
        "kvc_send_digest_now",
        "kvc_create_script_draft",
        "kvc_chat_script_draft",
        "kvc_upload_contacts",
        "kvc_list_outbound_captures",
        "kvc_place_test_call",
    }.issubset(tool_names)


@pytest.mark.asyncio
async def test_kvc_update_tenant_rejects_non_whitelisted_fields(monkeypatch):
    server = _reload_server(monkeypatch)

    result = await server.kvc_update_tenant({"agent_name": "Sam", "enabled_products": {"email_hunter": False}})

    assert "not allowed" in result
    assert "enabled_products" in result
