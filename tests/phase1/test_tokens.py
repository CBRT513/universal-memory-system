"""JWT signing, verification, and claim validation."""
from __future__ import annotations

import time

import pytest


def test_sign_verify_roundtrip(configured_env):
    from galactica_mcp import tokens
    token_str, claims = tokens.mint_access_token(
        client_id="c1", subject="c1", scope=["memory:read"],
    )
    verified = tokens.verify(token_str, expected_type="access")
    assert verified.client_id == "c1"
    assert verified.sub == "c1"
    assert verified.scope == ["memory:read"]
    assert verified.token_type == "access"
    assert verified.jti == claims.jti


def test_verify_rejects_tampered_signature(configured_env):
    from galactica_mcp import tokens
    token_str, _ = tokens.mint_access_token(
        client_id="c1", subject="c1", scope=["memory:read"],
    )
    tampered = token_str[:-4] + "AAAA"
    with pytest.raises(tokens.TokenInvalidError):
        tokens.verify(tampered)


def test_verify_rejects_wrong_token_type(configured_env):
    from galactica_mcp import tokens
    access, _ = tokens.mint_access_token(
        client_id="c1", subject="c1", scope=["memory:read"],
    )
    with pytest.raises(tokens.TokenInvalidError):
        tokens.verify(access, expected_type="refresh")


def test_verify_rejects_expired_token(configured_env, monkeypatch):
    from galactica_mcp import config, tokens
    monkeypatch.setattr(config, "ACCESS_TOKEN_TTL_SECONDS", 1)
    token_str, _ = tokens.mint_access_token(
        client_id="c1", subject="c1", scope=["memory:read"],
    )
    time.sleep(2)
    with pytest.raises(tokens.TokenExpiredError):
        tokens.verify(token_str)


def test_public_jwk_is_public_only(configured_env):
    from galactica_mcp import tokens
    jwk = tokens.public_jwk()
    assert jwk["kty"] == "RSA"
    assert jwk["use"] == "sig"
    assert jwk["alg"] == "RS256"
    # RSA public keys expose n + e only. Private fields (d, p, q, etc.) must NOT leak.
    for private_field in ("d", "p", "q", "dp", "dq", "qi"):
        assert private_field not in jwk
