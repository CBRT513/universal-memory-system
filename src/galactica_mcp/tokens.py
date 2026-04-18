"""JWT signing and verification using joserfc (post-authlib.jose).

All tokens are RS256-signed. The private key PEM is loaded from the
GALACTICA_OAUTH_PRIVATE_KEY environment variable exactly once at import
time; the public key is derived from it. No key material ever touches
the filesystem from within this process.

Access tokens and refresh tokens use the same signing key; they're
distinguished by the `token_type` claim.
"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Any

from joserfc import jwt
from joserfc.errors import BadSignatureError, DecodeError, ExpiredTokenError
from joserfc.jwk import RSAKey

from . import config


class TokenError(Exception):
    """Base class for JWT problems surfaced by this module."""


class TokenInvalidError(TokenError):
    """Signature failed, payload malformed, or claims missing."""


class TokenExpiredError(TokenError):
    """Token is syntactically valid but past its `exp`."""


@dataclass(frozen=True)
class TokenClaims:
    """A verified JWT's claims, typed."""

    jti: str
    sub: str
    client_id: str
    scope: list[str]
    token_type: str
    issued_at: int
    expires_at: int


_signing_key: RSAKey | None = None


def _load_signing_key() -> RSAKey:
    """Load the RSA key from env once; cache the object."""
    global _signing_key
    if _signing_key is None:
        pem = config.OAUTH_PRIVATE_KEY_PEM
        if not pem:
            raise TokenError(
                "GALACTICA_OAUTH_PRIVATE_KEY env var is empty; cannot sign or verify JWTs"
            )
        _signing_key = RSAKey.import_key(pem.encode("utf-8"))
    return _signing_key


def reset_key_cache_for_tests() -> None:
    """Drop the cached signing key so tests can swap config between runs."""
    global _signing_key
    _signing_key = None


def _mint(
    *,
    client_id: str,
    subject: str,
    scope: list[str],
    token_type: str,
    ttl_seconds: int,
) -> tuple[str, TokenClaims]:
    """Mint a signed JWT and return the encoded string plus parsed claims."""
    now = int(time.time())
    jti = secrets.token_urlsafe(16)
    claims = {
        "iss": config.ISSUER,
        "sub": subject,
        "aud": config.RESOURCE,
        "iat": now,
        "nbf": now,
        "exp": now + ttl_seconds,
        "jti": jti,
        "client_id": client_id,
        "scope": " ".join(scope),
        "token_type": token_type,
    }
    header = {"alg": "RS256", "typ": "JWT", "kid": _key_id()}
    encoded = jwt.encode(header, claims, _load_signing_key())
    return encoded, TokenClaims(
        jti=jti,
        sub=subject,
        client_id=client_id,
        scope=list(scope),
        token_type=token_type,
        issued_at=now,
        expires_at=now + ttl_seconds,
    )


def mint_access_token(*, client_id: str, subject: str, scope: list[str]) -> tuple[str, TokenClaims]:
    """Mint an access token (TTL from config)."""
    return _mint(
        client_id=client_id,
        subject=subject,
        scope=scope,
        token_type="access",
        ttl_seconds=config.ACCESS_TOKEN_TTL_SECONDS,
    )


def mint_refresh_token(*, client_id: str, subject: str, scope: list[str]) -> tuple[str, TokenClaims]:
    """Mint a refresh token (TTL from config)."""
    return _mint(
        client_id=client_id,
        subject=subject,
        scope=scope,
        token_type="refresh",
        ttl_seconds=config.REFRESH_TOKEN_TTL_SECONDS,
    )


def verify(token: str, *, expected_type: str | None = None) -> TokenClaims:
    """Verify signature, expiry, audience, and (optionally) token_type.

    Raises TokenInvalidError or TokenExpiredError on failure.
    """
    key = _load_signing_key()
    try:
        obj = jwt.decode(token, key)
    except ExpiredTokenError as e:
        raise TokenExpiredError(str(e)) from e
    except (BadSignatureError, DecodeError, ValueError) as e:
        raise TokenInvalidError(f"decode failed: {e}") from e

    claims = obj.claims
    now = int(time.time())
    if claims.get("exp", 0) < now:
        raise TokenExpiredError("exp in the past")
    if claims.get("iss") != config.ISSUER:
        raise TokenInvalidError("iss mismatch")
    if claims.get("aud") != config.RESOURCE:
        raise TokenInvalidError("aud mismatch")
    if expected_type is not None and claims.get("token_type") != expected_type:
        raise TokenInvalidError(f"token_type must be {expected_type}")

    scope_str = claims.get("scope", "")
    return TokenClaims(
        jti=claims.get("jti", ""),
        sub=claims.get("sub", ""),
        client_id=claims.get("client_id", ""),
        scope=scope_str.split() if scope_str else [],
        token_type=claims.get("token_type", ""),
        issued_at=int(claims.get("iat", 0)),
        expires_at=int(claims.get("exp", 0)),
    )


def public_jwk() -> dict[str, Any]:
    """Return the public key as a JWK dict for the JWKS endpoint."""
    private = _load_signing_key()
    jwk = private.as_dict(private=False)
    jwk["use"] = "sig"
    jwk["alg"] = "RS256"
    jwk["kid"] = _key_id()
    return jwk


def _key_id() -> str:
    """Derive a stable-ish kid from the key's public modulus."""
    private = _load_signing_key()
    jwk = private.as_dict(private=False)
    # RSA JWKs expose `n` (modulus, base64url). Use its first 16 chars as kid —
    # stable per key, human-opaque, survives restart without needing persistence.
    modulus = jwk.get("n", "")
    return modulus[:16] if modulus else "galactica-oauth"
