"""Configuration for Galactica MCP + OAuth.

All values come from environment variables so secrets never live in code.
Loaded once at import time and cached. Tests may override via monkeypatch
of the module-level constants or by setting env vars before import.
"""
from __future__ import annotations

import os
from pathlib import Path


def _env(name: str, default: str | None = None, *, required: bool = False) -> str:
    """Fetch an env var, raising if required and unset."""
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value or ""


ISSUER = _env("GALACTICA_ISSUER", "https://galactica.barge2rail.com")
"""The OAuth issuer URL. Used as `iss` in JWTs and as the base of metadata URLs."""

RESOURCE = _env("GALACTICA_RESOURCE", f"{ISSUER}/mcp")
"""The protected resource URL. Used as `aud` in JWTs per RFC 8707."""

ACCESS_TOKEN_TTL_SECONDS = int(_env("GALACTICA_ACCESS_TOKEN_TTL", "3600"))
"""Access token lifetime — 1 hour per brief."""

REFRESH_TOKEN_TTL_SECONDS = int(_env("GALACTICA_REFRESH_TOKEN_TTL", str(30 * 24 * 3600)))
"""Refresh token lifetime — 30 days per brief."""

AUTH_CODE_TTL_SECONDS = int(_env("GALACTICA_AUTH_CODE_TTL", "600"))
"""Authorization code lifetime — 10 minutes, per OAuth 2.1 BCP."""

_AI_MEMORY_DIR = Path(os.environ.get("GALACTICA_AI_MEMORY_DIR", Path.home() / ".ai-memory"))
AUDIT_DB_PATH = Path(_env("GALACTICA_AUDIT_DB", str(_AI_MEMORY_DIR / "galactica_audit.db")))
OAUTH_DB_PATH = Path(_env("GALACTICA_OAUTH_DB", str(_AI_MEMORY_DIR / "galactica_oauth.db")))

OAUTH_PRIVATE_KEY_PEM = _env("GALACTICA_OAUTH_PRIVATE_KEY", "")
"""RSA private key in PEM format for signing JWTs. Loaded from env, never from disk in code."""

AUTHORIZE_PASSWORD = _env("GALACTICA_AUTHORIZE_PASSWORD", "")
"""Shared password that gates the /oauth/authorize consent form.

Personal-infra trust boundary: Clif types this on the consent page to approve
an OAuth grant. Empty value means the authorize endpoint is disabled (fail-closed).
"""


def metadata_authorization_server_url() -> str:
    """RFC 8414 metadata URL."""
    return f"{ISSUER}/.well-known/oauth-authorization-server"


def metadata_protected_resource_url() -> str:
    """RFC 9728 metadata URL."""
    return f"{ISSUER}/.well-known/oauth-protected-resource"
