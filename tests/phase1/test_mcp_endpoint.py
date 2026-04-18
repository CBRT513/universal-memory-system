"""MCP endpoint — authN, dispatch, scope enforcement, audit."""
from __future__ import annotations

import base64
import hashlib
import secrets
import sqlite3
import urllib.parse


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:64]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return verifier, base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _get_access_token(client, *, scope: str = "memory:read") -> str:
    """Run the full OAuth flow against a freshly-seeded client. Returns access token."""
    from galactica_mcp import oauth_storage
    redirect_uri = "https://claude.ai/callback"
    client_id = "claude-ios-testmcp"
    oauth_storage.save_client(oauth_storage.OAuthClient(
        client_id=client_id,
        client_secret=None,
        client_name="Claude iOS MCP test",
        redirect_uris=[redirect_uri],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        scope=scope.split(),
        token_endpoint_auth_method="none",
    ))
    verifier, challenge = _pkce_pair()
    resp = client.post("/oauth/authorize", data={
        "client_id": client_id, "redirect_uri": redirect_uri,
        "response_type": "code", "scope": scope, "state": "s",
        "code_challenge": challenge, "code_challenge_method": "S256",
        "password": "test-password", "decision": "allow",
    }, follow_redirects=False)
    code = urllib.parse.parse_qs(urllib.parse.urlparse(resp.headers["location"]).query)["code"][0]
    resp = client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code,
        "client_id": client_id, "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    })
    return resp.json()["access_token"]


def test_mcp_no_token_returns_401_with_www_authenticate(client):
    """AC #2."""
    resp = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert resp.status_code == 401
    www = resp.headers.get("WWW-Authenticate", "")
    assert "Bearer" in www
    assert "resource_metadata=" in www
    assert ".well-known/oauth-protected-resource" in www


def test_mcp_invalid_token_returns_401(client):
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={"Authorization": "Bearer not-a-real-jwt"},
    )
    assert resp.status_code == 401


def test_mcp_malformed_authorization_header(client):
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={"Authorization": "NotBearer abc"},
    )
    assert resp.status_code == 401


def test_mcp_initialize(client, fake_service):
    token = _get_access_token(client)
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == 1
    assert body["result"]["protocolVersion"]
    assert body["result"]["serverInfo"]["name"] == "galactica-mcp-server"
    assert "tools" in body["result"]["capabilities"]


def test_mcp_tools_list_returns_four(client, fake_service):
    """AC #4."""
    token = _get_access_token(client)
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    tools = resp.json()["result"]["tools"]
    names = sorted(t["name"] for t in tools)
    assert names == ["get_context", "health_check", "search_nodes", "store_memory"]


def test_mcp_search_nodes_success(client, fake_service):
    """AC #5 — result shape mirrors stdio wrapper."""
    token = _get_access_token(client)
    resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "search_nodes", "arguments": {"query": "hello world", "limit": 3}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # MCP envelope
    assert body["result"]["isError"] is False
    content = body["result"]["content"]
    assert len(content) == 1 and content[0]["type"] == "text"

    # Inner JSON must match stdio wrapper shape.
    import json as _json
    payload = _json.loads(content[0]["text"])
    assert set(payload.keys()) == {"query", "count", "results", "timestamp"}
    assert payload["query"] == "hello world"
    assert payload["count"] >= 0


def test_mcp_store_memory_insufficient_scope(client, fake_service):
    """AC #6 — memory:read token calling store_memory gets a scope error, not 500."""
    token = _get_access_token(client, scope="memory:read")
    resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0", "id": 4, "method": "tools/call",
            "params": {"name": "store_memory", "arguments": {"content": "x"}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200  # JSON-RPC error returns HTTP 200
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == -32001  # insufficient scope
    assert "memory:write" in body["error"]["message"]


def test_mcp_unknown_tool_returns_method_not_found(client, fake_service):
    token = _get_access_token(client)
    resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0", "id": 5, "method": "tools/call",
            "params": {"name": "delete_everything", "arguments": {}},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    body = resp.json()
    assert body["error"]["code"] == -32601


def test_mcp_get_returns_405_when_authed(client, fake_service):
    token = _get_access_token(client)
    resp = client.get("/mcp", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 405


def test_mcp_audit_row_per_call(client, fake_service):
    """AC #7 — every tools/call writes exactly one audit row; args never cleartext."""
    from galactica_mcp import config
    token = _get_access_token(client)

    secret_query = "UNIQUE-SECRET-QUERY-TOKEN-" + secrets.token_hex(8)

    # success call
    client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 10, "method": "tools/call",
        "params": {"name": "search_nodes", "arguments": {"query": secret_query}},
    }, headers={"Authorization": f"Bearer {token}"})

    # scope-error call
    client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 11, "method": "tools/call",
        "params": {"name": "store_memory", "arguments": {"content": "x"}},
    }, headers={"Authorization": f"Bearer {token}"})

    # unknown-tool call
    client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 12, "method": "tools/call",
        "params": {"name": "nope", "arguments": {}},
    }, headers={"Authorization": f"Bearer {token}"})

    with sqlite3.connect(str(config.AUDIT_DB_PATH)) as conn:
        rows = conn.execute(
            "SELECT tool_name, success, error_code, args_hash FROM mcp_audit_log"
        ).fetchall()

    # Exactly 3 rows — one per tools/call
    assert len(rows) == 3
    by_tool = {r[0]: r for r in rows}
    assert by_tool["search_nodes"][1] == 1  # success
    assert by_tool["store_memory"][1] == 0 and by_tool["store_memory"][2] == "insufficient_scope"
    assert by_tool["nope"][1] == 0 and by_tool["nope"][2] == "method_not_found"

    # Secret query string must not be recoverable from the audit table.
    with sqlite3.connect(str(config.AUDIT_DB_PATH)) as conn:
        dump = conn.execute("SELECT * FROM mcp_audit_log").fetchall()
    import json as _json
    assert secret_query not in _json.dumps(dump)


def test_mcp_notification_returns_204(client, fake_service):
    token = _get_access_token(client)
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


def test_mcp_ping(client, fake_service):
    token = _get_access_token(client)
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 99, "method": "ping"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == {}


def test_mcp_tools_health_check_success(client, fake_service):
    token = _get_access_token(client)
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 20, "method": "tools/call",
        "params": {"name": "health_check", "arguments": {}},
    }, headers={"Authorization": f"Bearer {token}"})
    body = resp.json()
    assert body["result"]["isError"] is False
    import json as _json
    payload = _json.loads(body["result"]["content"][0]["text"])
    assert payload["status"] == "ok"
    assert payload["total_memories"] == 42


def test_mcp_get_context_returns_plain_string(client, fake_service):
    token = _get_access_token(client)
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 21, "method": "tools/call",
        "params": {"name": "get_context", "arguments": {"query": "golang"}},
    }, headers={"Authorization": f"Bearer {token}"})
    body = resp.json()
    # get_context returns a string — text field is the context itself, not JSON
    assert body["result"]["content"][0]["text"].startswith("CONTEXT for ")


def test_mcp_store_memory_with_write_scope(client, fake_service):
    """Ensure the scope system actually permits store_memory when present."""
    token = _get_access_token(client, scope="memory:write")
    resp = client.post("/mcp", json={
        "jsonrpc": "2.0", "id": 22, "method": "tools/call",
        "params": {"name": "store_memory", "arguments": {"content": "hi", "importance": 7}},
    }, headers={"Authorization": f"Bearer {token}"})
    body = resp.json()
    assert body["result"]["isError"] is False
    import json as _json
    payload = _json.loads(body["result"]["content"][0]["text"])
    assert payload["status"] == "stored"
