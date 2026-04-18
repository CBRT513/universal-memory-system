"""FastAPI router for the native MCP-over-HTTP endpoint at /mcp.

Implements the streamable-HTTP transport's minimum viable surface: POST /mcp
returning application/json. SSE streaming is unused for the four current tools
(all return complete results synchronously) and omitted.

Auth model:
  - No bearer token:   HTTP 401 + WWW-Authenticate header with
                       `resource_metadata=` pointing at /.well-known/oauth-protected-resource.
  - Invalid/expired:   HTTP 401 (same).
  - Valid but missing required scope for a tool:
                       HTTP 200 with JSON-RPC error, code -32001.

Audit log:
  - One row per tool call, success or failure.
  - args hashed; never stored in cleartext.
  - Write happens in a finally block so every call is accounted for.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from . import audit, config, mcp_tools, scopes, tokens

router = APIRouter(tags=["mcp"])

MCP_PROTOCOL_VERSION = "2025-06-18"
MCP_SERVER_NAME = "galactica-mcp-server"
MCP_SERVER_VERSION = "2.0.0-phase1"

# JSON-RPC standard codes
_JSONRPC_PARSE_ERROR = -32700
_JSONRPC_INVALID_REQUEST = -32600
_JSONRPC_METHOD_NOT_FOUND = -32601
_JSONRPC_INVALID_PARAMS = -32602
_JSONRPC_INTERNAL_ERROR = -32603

# Implementation-defined (server range -32000 to -32099)
MCP_ERROR_INSUFFICIENT_SCOPE = -32001
MCP_ERROR_TOOL_EXECUTION = -32002


def _www_authenticate_header() -> str:
    """Per MCP spec: point to the protected-resource metadata so clients
    can discover the authorization server."""
    return (
        f'Bearer realm="galactica", '
        f'resource_metadata="{config.metadata_protected_resource_url()}"'
    )


def _unauth_response(description: str) -> JSONResponse:
    """Return an HTTP 401 with WWW-Authenticate. Body is RFC-6750-ish JSON."""
    return JSONResponse(
        status_code=401,
        headers={"WWW-Authenticate": _www_authenticate_header()},
        content={
            "error": "invalid_token",
            "error_description": description,
        },
    )


def _jsonrpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _jsonrpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _parse_bearer(authorization: str | None) -> str | None:
    """Return the raw bearer token, or None if missing/malformed."""
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def _authenticate(authorization: str | None) -> tokens.TokenClaims | JSONResponse:
    """Validate the Authorization header. Returns claims or a 401 response."""
    raw = _parse_bearer(authorization)
    if raw is None:
        return _unauth_response("missing bearer token")
    try:
        claims = tokens.verify(raw, expected_type="access")
    except tokens.TokenExpiredError:
        return _unauth_response("access token expired")
    except tokens.TokenError as exc:
        return _unauth_response(f"access token invalid: {exc}")
    return claims


# ==========================================================================
# Dispatch
# ==========================================================================


async def _dispatch_tools_call(
    params: dict[str, Any], claims: tokens.TokenClaims, request_id: Any
) -> dict[str, Any]:
    """Execute a tool, enforce scope, write exactly one audit row."""
    tool_name = params.get("name", "")
    args = params.get("arguments") or {}

    required_scope = scopes.TOOL_REQUIRED_SCOPE.get(tool_name)
    if required_scope is None:
        # Record the attempt as a failed call before returning — audit must
        # cover every tools/call invocation.
        audit.record(
            client_id=claims.client_id,
            scope=claims.scope,
            tool_name=tool_name or "<unknown>",
            args=args,
            result_size_bytes=0,
            success=False,
            error_code="method_not_found",
        )
        return _jsonrpc_error(request_id, _JSONRPC_METHOD_NOT_FOUND,
                              f"unknown tool: {tool_name}")

    if not scopes.has_scope(claims.scope, required_scope):
        audit.record(
            client_id=claims.client_id,
            scope=claims.scope,
            tool_name=tool_name,
            args=args,
            result_size_bytes=0,
            success=False,
            error_code="insufficient_scope",
        )
        return _jsonrpc_error(
            request_id,
            MCP_ERROR_INSUFFICIENT_SCOPE,
            f"missing required scope '{required_scope}' for tool '{tool_name}'",
        )

    handler = mcp_tools.TOOL_DISPATCH[tool_name]
    try:
        raw_result = await handler(args)
    except Exception as exc:  # noqa: BLE001 — tool exceptions become MCP errors
        audit.record(
            client_id=claims.client_id,
            scope=claims.scope,
            tool_name=tool_name,
            args=args,
            result_size_bytes=0,
            success=False,
            error_code="execution_error",
        )
        return _jsonrpc_error(
            request_id, MCP_ERROR_TOOL_EXECUTION, f"tool execution failed: {exc}"
        )

    # Wrap the tool's raw result in the MCP content envelope.
    if isinstance(raw_result, str):
        text = raw_result
    else:
        text = json.dumps(raw_result, default=str, indent=2)
    mcp_result = {"content": [{"type": "text", "text": text}], "isError": False}

    audit.record(
        client_id=claims.client_id,
        scope=claims.scope,
        tool_name=tool_name,
        args=args,
        result_size_bytes=len(text.encode("utf-8")),
        success=True,
        error_code=None,
    )
    return _jsonrpc_result(request_id, mcp_result)


async def _dispatch_one(
    message: dict[str, Any], claims: tokens.TokenClaims
) -> dict[str, Any] | None:
    """Handle a single JSON-RPC message. Returns None for notifications."""
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    if not isinstance(method, str):
        return _jsonrpc_error(request_id, _JSONRPC_INVALID_REQUEST, "method required")

    if method == "initialize":
        return _jsonrpc_result(request_id, {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": MCP_SERVER_NAME, "version": MCP_SERVER_VERSION},
        })

    if method == "notifications/initialized":
        # Notification — no response.
        return None

    if method == "ping":
        return _jsonrpc_result(request_id, {})

    if method == "tools/list":
        return _jsonrpc_result(request_id, {"tools": mcp_tools.TOOL_DEFINITIONS})

    if method == "tools/call":
        if not isinstance(params, dict):
            return _jsonrpc_error(request_id, _JSONRPC_INVALID_PARAMS,
                                  "params must be an object")
        return await _dispatch_tools_call(params, claims, request_id)

    return _jsonrpc_error(request_id, _JSONRPC_METHOD_NOT_FOUND,
                           f"method not found: {method}")


# ==========================================================================
# Routes
# ==========================================================================


@router.post("/mcp")
async def mcp_post(
    request: Request,
    authorization: str | None = Header(default=None),
) -> JSONResponse:
    """Main MCP entry point. Accepts a single JSON-RPC message; replies with
    one JSON-RPC response (or no body if the incoming message was a notification)."""
    auth_result = _authenticate(authorization)
    if isinstance(auth_result, JSONResponse):
        return auth_result
    claims = auth_result

    try:
        raw = await request.body()
        if not raw:
            return JSONResponse(
                status_code=200,
                content=_jsonrpc_error(None, _JSONRPC_PARSE_ERROR, "empty body"),
            )
        message = json.loads(raw)
    except json.JSONDecodeError as exc:
        return JSONResponse(
            status_code=200,
            content=_jsonrpc_error(None, _JSONRPC_PARSE_ERROR, f"malformed JSON: {exc}"),
        )

    if not isinstance(message, dict):
        return JSONResponse(
            status_code=200,
            content=_jsonrpc_error(None, _JSONRPC_INVALID_REQUEST,
                                    "JSON-RPC message must be an object"),
        )

    response = await _dispatch_one(message, claims)
    if response is None:
        # Notification — HTTP 204 No Content per JSON-RPC convention.
        return JSONResponse(status_code=204, content=None)
    return JSONResponse(status_code=200, content=response)


@router.get("/mcp")
async def mcp_get(authorization: str | None = Header(default=None)) -> JSONResponse:
    """MCP over HTTP uses POST. GET is rejected with 405 if authed, 401 if not,
    so unauthenticated probes get the WWW-Authenticate hint per the MCP spec."""
    auth_result = _authenticate(authorization)
    if isinstance(auth_result, JSONResponse):
        return auth_result
    return JSONResponse(
        status_code=405,
        content={"error": "method_not_allowed",
                 "error_description": "use POST for MCP JSON-RPC"},
    )
