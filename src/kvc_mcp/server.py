"""Krystal Voice Caller MCP Server.

Use these tools to manage a Krystal Voice Caller tenant: view config, manage
DNC, browse call history, author scripts, place test calls, and upload
outbound contacts. Script approval is intentionally not exposed via MCP; that
admin-only action stays in the web UI.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

API_TOKEN = os.getenv("KVC_API_TOKEN", "")
BASE_URL = os.getenv("KVC_BASE_URL", "https://krystalunity.com/api/admin/kvc").rstrip("/")
TIMEOUT = float(os.getenv("KVC_TIMEOUT", "30"))
BILLING_URL = "https://krystalunity.com/voice/krystal-caller/dashboard/billing"
TOKEN_URL = "https://krystalunity.com/voice/krystal-caller/dashboard/api-tokens"

mcp = FastMCP(
    "Krystal Voice Caller",
    instructions=(
        "Use these tools to manage a Krystal Voice Caller tenant - view config, "
        "manage DNC, browse call history, author scripts, place test calls, "
        "and upload outbound contacts."
    ),
)

UPDATE_WHITELIST = {"agent_name", "business_hours", "digest_recipient_email", "digest_hour_local"}


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {API_TOKEN}", "Accept": "application/json"}


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=TIMEOUT)


def _tenant_id() -> str:
    token = API_TOKEN.strip()
    if not token:
        raise RuntimeError("KVC_API_TOKEN is required")
    return os.getenv("KVC_TENANT_ID", "me")


async def _request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    async with _client() as client:
        response = await client.request(method, f"{BASE_URL}{path}", headers=_headers(), **kwargs)
        response.raise_for_status()
        return response.json()


def _format_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 401:
            return f"Authentication failed. Check your KVC_API_TOKEN. Generate a new one at {TOKEN_URL}"
        if status == 403:
            product = "required"
            try:
                detail = exc.response.json().get("detail", {})
                if isinstance(detail, dict):
                    product = str(detail.get("product") or product)
            except Exception:
                pass
            return f"This tool requires the {product} product. Upgrade at {BILLING_URL}"
        if status == 429:
            retry = exc.response.headers.get("Retry-After", "?")
            return f"Rate limited. Retry after {retry}s."
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except Exception:
            detail = exc.response.text
        return f"API error {status}: {detail}"
    return f"Request failed: {exc}"


def _json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def kvc_get_tenant() -> str:
    """Return current tenant config."""
    try:
        return _json(await _request("GET", f"/{_tenant_id()}"))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_update_tenant(updates: dict[str, Any]) -> str:
    """Patch safe tenant config fields."""
    disallowed = sorted(set(updates) - UPDATE_WHITELIST)
    if disallowed:
        return f"These fields are not allowed through MCP: {', '.join(disallowed)}"
    try:
        return _json(await _request("PATCH", f"/{_tenant_id()}", json=updates))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_list_dnc() -> str:
    """List tenant DNC entries."""
    try:
        return _json(await _request("GET", f"/{_tenant_id()}/dnc"))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_add_dnc(phone: str, reason: str) -> str:
    """Add an AU E.164 phone number to tenant DNC."""
    try:
        return _json(await _request("POST", f"/{_tenant_id()}/dnc", json={"phone": phone, "reason": reason}))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_call_history(limit: int = 50, kind: str | None = None) -> str:
    """Return recent call outcomes."""
    try:
        return _json(await _request("GET", f"/{_tenant_id()}/call-history", params={"limit": limit, "kind": kind}))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_after_hours_captures(limit: int = 20) -> str:
    """Return recent reception captures."""
    try:
        return _json(await _request("GET", f"/{_tenant_id()}/captures", params={"limit": limit, "kind": "inbound"}))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_send_digest_now() -> str:
    """Trigger an immediate digest email send."""
    try:
        return _json(await _request("POST", f"/{_tenant_id()}/digest/send-now"))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_create_script_draft(prompt: str) -> str:
    """Start a Script Author draft."""
    try:
        data = await _request("POST", f"/{_tenant_id()}/scripts/draft")
        if prompt.strip():
            data = await _request("POST", f"/{_tenant_id()}/scripts/draft/{data['draft_id']}/message", json={"message": prompt})
        return _json(data)
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_chat_script_draft(draft_id: int, message: str) -> str:
    """Send a message to an active Script Author draft."""
    try:
        return _json(await _request("POST", f"/{_tenant_id()}/scripts/draft/{draft_id}/message", json={"message": message}))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_upload_contacts(csv_content: str) -> str:
    """Upload CSV contacts for outbound Email Hunter."""
    try:
        files = {"file": ("contacts.csv", csv_content.encode("utf-8"), "text/csv")}
        return _json(await _request("POST", f"/{_tenant_id()}/contacts/upload", files=files))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_list_outbound_captures(limit: int = 50) -> str:
    """List captures from outbound Email Hunter calls."""
    try:
        return _json(await _request("GET", f"/{_tenant_id()}/captures", params={"limit": limit, "kind": "outbound"}))
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def kvc_place_test_call(target_phone: str) -> str:
    """Place a test outbound roleplay call."""
    try:
        return _json(await _request("POST", f"/{_tenant_id()}/test-call", json={"target_phone": target_phone}))
    except Exception as exc:
        return _format_error(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Krystal Voice Caller MCP server.")
    parser.parse_args()
    mcp.run()


if __name__ == "__main__":
    main()
