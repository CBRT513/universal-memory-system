"""OAuth storage — clients, authorization codes, refresh tokens."""
from __future__ import annotations

import time


def _client(**overrides):
    from galactica_mcp import oauth_storage
    defaults = dict(
        client_id="c-test",
        client_secret=None,
        client_name="Test Client",
        redirect_uris=["https://example.com/cb"],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        scope=["memory:read"],
        token_endpoint_auth_method="none",
    )
    defaults.update(overrides)
    return oauth_storage.OAuthClient(**defaults)


def test_save_and_get_client(configured_env):
    from galactica_mcp import oauth_storage
    client = _client()
    oauth_storage.save_client(client)
    fetched = oauth_storage.get_client("c-test")
    assert fetched is not None
    assert fetched.client_name == "Test Client"
    assert fetched.redirect_uris == ["https://example.com/cb"]
    assert fetched.scope == ["memory:read"]


def test_get_client_missing_returns_none(configured_env):
    from galactica_mcp import oauth_storage
    assert oauth_storage.get_client("no-such-client") is None


def test_auth_code_single_use(configured_env):
    from galactica_mcp import oauth_storage
    code = oauth_storage.generate_code()
    oauth_storage.save_authorization_code(
        oauth_storage.AuthorizationCode(
            code=code,
            client_id="c-test",
            redirect_uri="https://example.com/cb",
            scope=["memory:read"],
            code_challenge="x" * 43,
            code_challenge_method="S256",
            subject="c-test",
            expires_at=int(time.time()) + 600,
            used=False,
        )
    )
    first = oauth_storage.consume_authorization_code(code)
    assert first is not None
    # Second consumption must fail — single-use enforcement.
    second = oauth_storage.consume_authorization_code(code)
    assert second is None


def test_auth_code_expired_not_consumed(configured_env):
    from galactica_mcp import oauth_storage
    code = oauth_storage.generate_code()
    oauth_storage.save_authorization_code(
        oauth_storage.AuthorizationCode(
            code=code,
            client_id="c-test",
            redirect_uri="https://example.com/cb",
            scope=["memory:read"],
            code_challenge="x" * 43,
            code_challenge_method="S256",
            subject="c-test",
            expires_at=int(time.time()) - 1,  # already expired
            used=False,
        )
    )
    assert oauth_storage.consume_authorization_code(code) is None


def test_refresh_token_roundtrip(configured_env):
    from galactica_mcp import oauth_storage
    oauth_storage.save_refresh_token(
        token="tok-abc-123",
        client_id="c-test",
        subject="c-test",
        scope=["memory:read"],
        expires_at=int(time.time()) + 3600,
    )
    record = oauth_storage.lookup_refresh_token("tok-abc-123")
    assert record is not None
    assert record["client_id"] == "c-test"
    assert record["scope"] == ["memory:read"]


def test_refresh_token_revoked(configured_env):
    from galactica_mcp import oauth_storage
    oauth_storage.save_refresh_token(
        token="tok-zzz",
        client_id="c-test",
        subject="c-test",
        scope=["memory:read"],
        expires_at=int(time.time()) + 3600,
    )
    oauth_storage.revoke_refresh_token("tok-zzz")
    assert oauth_storage.lookup_refresh_token("tok-zzz") is None


def test_refresh_token_expired(configured_env):
    from galactica_mcp import oauth_storage
    oauth_storage.save_refresh_token(
        token="tok-old",
        client_id="c-test",
        subject="c-test",
        scope=["memory:read"],
        expires_at=int(time.time()) - 1,
    )
    assert oauth_storage.lookup_refresh_token("tok-old") is None


def test_refresh_token_unknown(configured_env):
    from galactica_mcp import oauth_storage
    assert oauth_storage.lookup_refresh_token("never-seen") is None
