"""End-to-end OAuth 2.1 flow: register → authorize → token → refresh."""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
import urllib.parse

import pytest


def _pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) per RFC 7636 S256."""
    verifier = secrets.token_urlsafe(64)[:64]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def test_authorization_server_metadata_public(client):
    """AC #1: metadata endpoint is unauthenticated and returns RFC 8414 fields."""
    resp = client.get("/.well-known/oauth-authorization-server")
    assert resp.status_code == 200
    meta = resp.json()
    assert meta["issuer"] == "https://test.galactica.local"
    assert meta["authorization_endpoint"].endswith("/oauth/authorize")
    assert meta["token_endpoint"].endswith("/oauth/token")
    assert meta["registration_endpoint"].endswith("/oauth/register")
    assert "S256" in meta["code_challenge_methods_supported"]
    assert "code" in meta["response_types_supported"]
    assert "authorization_code" in meta["grant_types_supported"]
    assert "refresh_token" in meta["grant_types_supported"]


def test_protected_resource_metadata(client):
    resp = client.get("/.well-known/oauth-protected-resource")
    assert resp.status_code == 200
    meta = resp.json()
    assert meta["resource"] == "https://test.galactica.local/mcp"
    assert "https://test.galactica.local" in meta["authorization_servers"]


def test_jwks(client):
    resp = client.get("/.well-known/jwks.json")
    assert resp.status_code == 200
    body = resp.json()
    assert "keys" in body
    assert len(body["keys"]) == 1
    key = body["keys"][0]
    assert key["kty"] == "RSA"
    assert key["alg"] == "RS256"
    assert "d" not in key  # public only


def test_register_creates_client(client):
    resp = client.post("/oauth/register", json={
        "client_name": "Test Dyn",
        "redirect_uris": ["https://example.com/cb"],
        "scope": "memory:read",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["client_id"].startswith("client-")
    assert body["scope"] == "memory:read"


def test_register_filters_elevated_scope(client):
    """Dynamic registration must not grant memory:write or memory:admin."""
    resp = client.post("/oauth/register", json={
        "redirect_uris": ["https://example.com/cb"],
        "scope": "memory:read memory:write memory:admin",
    })
    assert resp.status_code == 201
    assert resp.json()["scope"] == "memory:read"


def _seed_claude_ios(redirect_uri: str = "https://claude.ai/callback") -> str:
    """Insert a Claude-iOS-like client directly via the storage layer.
    Returns the client_id."""
    from galactica_mcp import oauth_storage
    client_id = "claude-ios-test"
    oauth_storage.save_client(oauth_storage.OAuthClient(
        client_id=client_id,
        client_secret=None,
        client_name="Claude iOS",
        redirect_uris=[redirect_uri],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        scope=["memory:read"],
        token_endpoint_auth_method="none",
    ))
    return client_id


def _full_oauth_flow(client, *, requested_scope: str = "memory:read"):
    """Run the full OAuth 2.1 PKCE flow. Returns the token response dict."""
    redirect_uri = "https://claude.ai/callback"
    client_id = _seed_claude_ios(redirect_uri)
    verifier, challenge = _pkce_pair()
    state = "test-state-123"

    # GET /authorize — should render consent form
    resp = client.get("/oauth/authorize", params={
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": requested_scope,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    assert resp.status_code == 200
    assert "Allow" in resp.text

    # POST /authorize with correct password
    resp = client.post("/oauth/authorize", data={
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": requested_scope,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "password": "test-password",
        "decision": "allow",
    }, follow_redirects=False)
    assert resp.status_code == 302
    location = resp.headers["location"]
    parsed = urllib.parse.urlparse(location)
    q = urllib.parse.parse_qs(parsed.query)
    assert q["state"] == [state]
    code = q["code"][0]

    # POST /token — exchange code
    resp = client.post("/oauth/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    })
    assert resp.status_code == 200
    return resp.json(), client_id, redirect_uri


def test_full_flow_happy_path(client):
    """AC #3: full PKCE flow yields an access token carrying memory:read."""
    tokens, client_id, _ = _full_oauth_flow(client)
    assert tokens["token_type"] == "Bearer"
    assert tokens["expires_in"] == 3600
    assert "memory:read" in tokens["scope"]
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    # Decode (without verifying audience — just read claims) to sanity check
    from galactica_mcp import tokens as tokens_mod
    claims = tokens_mod.verify(tokens["access_token"], expected_type="access")
    assert claims.client_id == client_id
    assert "memory:read" in claims.scope


def test_authorize_wrong_password_rerenders_form(client):
    redirect_uri = "https://claude.ai/callback"
    client_id = _seed_claude_ios(redirect_uri)
    _, challenge = _pkce_pair()
    resp = client.post("/oauth/authorize", data={
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "memory:read",
        "state": "s",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "password": "WRONG",
        "decision": "allow",
    }, follow_redirects=False)
    assert resp.status_code == 200
    assert "Error" in resp.text or "incorrect" in resp.text.lower()


def test_authorize_deny_redirects_with_error(client):
    redirect_uri = "https://claude.ai/callback"
    client_id = _seed_claude_ios(redirect_uri)
    _, challenge = _pkce_pair()
    resp = client.post("/oauth/authorize", data={
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "memory:read",
        "state": "s",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "password": "test-password",
        "decision": "deny",
    }, follow_redirects=False)
    assert resp.status_code == 302
    q = urllib.parse.parse_qs(urllib.parse.urlparse(resp.headers["location"]).query)
    assert q["error"] == ["access_denied"]


def test_authorize_rejects_plain_pkce(client):
    redirect_uri = "https://claude.ai/callback"
    client_id = _seed_claude_ios(redirect_uri)
    resp = client.get("/oauth/authorize", params={
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "memory:read",
        "state": "s",
        "code_challenge": "anything",
        "code_challenge_method": "plain",  # OAuth 2.1 disallows
    }, follow_redirects=False)
    assert resp.status_code == 302
    q = urllib.parse.parse_qs(urllib.parse.urlparse(resp.headers["location"]).query)
    assert q["error"] == ["invalid_request"]


def test_authorize_rejects_unregistered_redirect(client):
    client_id = _seed_claude_ios("https://claude.ai/callback")
    _, challenge = _pkce_pair()
    resp = client.get("/oauth/authorize", params={
        "client_id": client_id,
        "redirect_uri": "https://evil.example.com/steal",
        "response_type": "code",
        "scope": "memory:read",
        "state": "s",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    assert resp.status_code == 400


def test_token_rejects_bad_pkce(client):
    redirect_uri = "https://claude.ai/callback"
    client_id = _seed_claude_ios(redirect_uri)
    _, challenge = _pkce_pair()

    resp = client.post("/oauth/authorize", data={
        "client_id": client_id, "redirect_uri": redirect_uri,
        "response_type": "code", "scope": "memory:read", "state": "s",
        "code_challenge": challenge, "code_challenge_method": "S256",
        "password": "test-password", "decision": "allow",
    }, follow_redirects=False)
    code = urllib.parse.parse_qs(urllib.parse.urlparse(resp.headers["location"]).query)["code"][0]

    # Submit a DIFFERENT verifier than the one that produced `challenge`
    resp = client.post("/oauth/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_verifier": "completely-wrong-verifier-that-is-not-it",
    })
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_grant"


def test_token_rejects_reused_code(client):
    tokens, client_id, redirect_uri = _full_oauth_flow(client)
    assert tokens["access_token"]

    # We can't reuse the same code (already consumed). Try the flow again
    # with a fresh code, then replay the FIRST code — test is that a consumed
    # code is rejected. Simplest approach: redo flow partway, then replay.
    verifier, challenge = _pkce_pair()
    resp = client.post("/oauth/authorize", data={
        "client_id": client_id, "redirect_uri": redirect_uri,
        "response_type": "code", "scope": "memory:read", "state": "s",
        "code_challenge": challenge, "code_challenge_method": "S256",
        "password": "test-password", "decision": "allow",
    }, follow_redirects=False)
    code = urllib.parse.parse_qs(urllib.parse.urlparse(resp.headers["location"]).query)["code"][0]

    # First exchange — succeeds
    resp1 = client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code,
        "client_id": client_id, "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    })
    assert resp1.status_code == 200
    # Second exchange with same code — fails
    resp2 = client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code,
        "client_id": client_id, "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    })
    assert resp2.status_code == 400
    assert resp2.json()["error"] == "invalid_grant"


def test_refresh_token_rotation(client):
    tokens, client_id, _ = _full_oauth_flow(client)
    old_refresh = tokens["refresh_token"]

    resp = client.post("/oauth/token", data={
        "grant_type": "refresh_token",
        "refresh_token": old_refresh,
        "client_id": client_id,
    })
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != old_refresh

    # Old refresh must be revoked
    resp = client.post("/oauth/token", data={
        "grant_type": "refresh_token",
        "refresh_token": old_refresh,
        "client_id": client_id,
    })
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_grant"


def _seed_confidential_client(
    redirect_uri: str = "https://confidential.example.com/cb",
    *,
    client_id: str = "confidential-test",
    client_secret: str = "s3cr3t-confidential-value",
    scope: list[str] | None = None,
) -> tuple[str, str]:
    """Seed a confidential (client_secret_post) OAuth client. Returns (id, secret)."""
    from galactica_mcp import oauth_storage
    oauth_storage.save_client(oauth_storage.OAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        client_name="Confidential Test Client",
        redirect_uris=[redirect_uri],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        scope=scope or ["memory:read"],
        token_endpoint_auth_method="client_secret_post",
    ))
    return client_id, client_secret


def _authorize_and_get_code(client, *, client_id: str, redirect_uri: str):
    """Drive the authorize endpoint; return (code, code_verifier)."""
    verifier, challenge = _pkce_pair()
    resp = client.post("/oauth/authorize", data={
        "client_id": client_id, "redirect_uri": redirect_uri,
        "response_type": "code", "scope": "memory:read", "state": "s",
        "code_challenge": challenge, "code_challenge_method": "S256",
        "password": "test-password", "decision": "allow",
    }, follow_redirects=False)
    code = urllib.parse.parse_qs(urllib.parse.urlparse(resp.headers["location"]).query)["code"][0]
    return code, verifier


def test_confidential_client_requires_secret_on_code_exchange(client):
    """Codex finding #1: confidential clients cannot redeem a code without
    presenting client_secret — even if PKCE is satisfied."""
    redirect_uri = "https://confidential.example.com/cb"
    cid, secret = _seed_confidential_client(redirect_uri)
    code, verifier = _authorize_and_get_code(client, client_id=cid, redirect_uri=redirect_uri)

    # Without secret → invalid_client
    resp = client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code,
        "client_id": cid, "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    })
    assert resp.status_code == 401
    assert resp.json()["error"] == "invalid_client"

    # Wrong secret → invalid_client (same response; don't leak validity signals).
    # Use a *different* code since the first attempt consumed the one above.
    code2, verifier2 = _authorize_and_get_code(client, client_id=cid, redirect_uri=redirect_uri)
    resp = client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code2,
        "client_id": cid, "redirect_uri": redirect_uri,
        "code_verifier": verifier2, "client_secret": "wrong-secret",
    })
    assert resp.status_code == 401
    assert resp.json()["error"] == "invalid_client"

    # Correct secret → success.
    code3, verifier3 = _authorize_and_get_code(client, client_id=cid, redirect_uri=redirect_uri)
    resp = client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code3,
        "client_id": cid, "redirect_uri": redirect_uri,
        "code_verifier": verifier3, "client_secret": secret,
    })
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_confidential_client_requires_secret_on_refresh(client):
    """Codex finding #1 (refresh path): same rule applies to refresh_token grant."""
    redirect_uri = "https://confidential.example.com/cb"
    cid, secret = _seed_confidential_client(redirect_uri)
    code, verifier = _authorize_and_get_code(client, client_id=cid, redirect_uri=redirect_uri)

    # Get initial tokens with correct secret.
    resp = client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code,
        "client_id": cid, "redirect_uri": redirect_uri,
        "code_verifier": verifier, "client_secret": secret,
    })
    assert resp.status_code == 200
    refresh = resp.json()["refresh_token"]

    # Refresh without secret → invalid_client.
    resp = client.post("/oauth/token", data={
        "grant_type": "refresh_token", "refresh_token": refresh, "client_id": cid,
    })
    assert resp.status_code == 401
    assert resp.json()["error"] == "invalid_client"

    # Refresh with correct secret → success. The prior refresh MUST still be
    # valid — our fail path above must NOT have silently revoked it.
    resp = client.post("/oauth/token", data={
        "grant_type": "refresh_token", "refresh_token": refresh, "client_id": cid,
        "client_secret": secret,
    })
    assert resp.status_code == 200, (
        "refresh with correct secret must still work after a prior no-secret attempt"
    )
    assert resp.json()["access_token"]


def test_unsupported_auth_method_rejected(client):
    """A client record with an unrecognised token_endpoint_auth_method must
    not silently fall through to 'public client' semantics."""
    from galactica_mcp import oauth_storage
    redirect_uri = "https://weird.example.com/cb"
    oauth_storage.save_client(oauth_storage.OAuthClient(
        client_id="weird-auth",
        client_secret="anything",
        client_name="Weird Auth Client",
        redirect_uris=[redirect_uri],
        grant_types=["authorization_code"],
        response_types=["code"],
        scope=["memory:read"],
        token_endpoint_auth_method="client_secret_basic",  # not supported by us
    ))
    code, verifier = _authorize_and_get_code(client, client_id="weird-auth", redirect_uri=redirect_uri)
    resp = client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code,
        "client_id": "weird-auth", "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    })
    assert resp.status_code == 401
    assert resp.json()["error"] == "invalid_client"


def test_refresh_rejects_any_scope_outside_original_grant(client):
    """Codex finding #2: RFC 6749 §6 — if ANY requested scope is outside the
    original grant, return invalid_scope. Do not silently narrow."""
    # Give the Claude-iOS-like client memory:read only. Then ask refresh to
    # include memory:write (which was never in the original grant).
    tokens_resp, client_id, _ = _full_oauth_flow(client, requested_scope="memory:read")
    refresh = tokens_resp["refresh_token"]

    resp = client.post("/oauth/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh,
        "client_id": client_id,
        "scope": "memory:read memory:write",
    })
    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_scope"
    assert "memory:write" in resp.json()["error_description"]


def test_elevated_scope_request_filtered(client):
    """Seeded Claude iOS client requests memory:write — server must downgrade
    to memory:read since that's the maximum allowed at registration."""
    redirect_uri = "https://claude.ai/callback"
    client_id = _seed_claude_ios(redirect_uri)
    verifier, challenge = _pkce_pair()

    resp = client.post("/oauth/authorize", data={
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "memory:write",  # attempt elevation
        "state": "s",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "password": "test-password",
        "decision": "allow",
    }, follow_redirects=False)
    # validate_subset returns empty → invalid_scope error.
    assert resp.status_code == 302
    q = urllib.parse.parse_qs(urllib.parse.urlparse(resp.headers["location"]).query)
    assert q["error"] == ["invalid_scope"]
