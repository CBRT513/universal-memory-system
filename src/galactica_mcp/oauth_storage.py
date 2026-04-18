"""OAuth state persistence — clients, authorization codes, refresh tokens.

Lives in its own SQLite database (config.OAUTH_DB_PATH). Access tokens are
NOT stored; they're stateless JWTs verified cryptographically.

Auth codes are single-use; we mark them consumed rather than deleting, so
replay attempts against a used code fail loudly.

Refresh tokens are stored as sha256 hashes (never plaintext).
"""
from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS oauth_clients (
    client_id TEXT PRIMARY KEY,
    client_secret TEXT,
    client_name TEXT NOT NULL,
    redirect_uris TEXT NOT NULL,
    grant_types TEXT NOT NULL,
    response_types TEXT NOT NULL,
    scope TEXT NOT NULL,
    token_endpoint_auth_method TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_authorization_codes (
    code TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    scope TEXT NOT NULL,
    code_challenge TEXT NOT NULL,
    code_challenge_method TEXT NOT NULL,
    subject TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_refresh_tokens (
    token_hash TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    scope TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    revoked INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_oauth_codes_client ON oauth_authorization_codes(client_id);
CREATE INDEX IF NOT EXISTS idx_oauth_refresh_client ON oauth_refresh_tokens(client_id);
"""


@dataclass(frozen=True)
class OAuthClient:
    """Registered OAuth client (a public or confidential relying party)."""

    client_id: str
    client_secret: str | None
    client_name: str
    redirect_uris: list[str]
    grant_types: list[str]
    response_types: list[str]
    scope: list[str]
    token_endpoint_auth_method: str

    def allows_redirect_uri(self, uri: str) -> bool:
        """Strict match against registered redirect URIs (no wildcards)."""
        return uri in self.redirect_uris

    def allowed_scope(self) -> list[str]:
        """Scopes this client may ever be granted (max set)."""
        return list(self.scope)


@dataclass(frozen=True)
class AuthorizationCode:
    """A one-time authorization code awaiting redemption at /oauth/token."""

    code: str
    client_id: str
    redirect_uri: str
    scope: list[str]
    code_challenge: str
    code_challenge_method: str
    subject: str
    expires_at: int
    used: bool


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or config.OAUTH_DB_PATH
    _ensure_parent(path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    """Create OAuth tables if they don't already exist."""
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        conn.commit()


# ---- Clients -------------------------------------------------------------


def save_client(client: OAuthClient, *, db_path: Path | None = None) -> None:
    """Insert a new client. Raises sqlite3.IntegrityError if client_id exists."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO oauth_clients
              (client_id, client_secret, client_name, redirect_uris, grant_types,
               response_types, scope, token_endpoint_auth_method, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client.client_id,
                client.client_secret,
                client.client_name,
                json.dumps(client.redirect_uris),
                json.dumps(client.grant_types),
                json.dumps(client.response_types),
                " ".join(client.scope),
                client.token_endpoint_auth_method,
                int(time.time()),
            ),
        )
        conn.commit()


def get_client(client_id: str, *, db_path: Path | None = None) -> OAuthClient | None:
    """Fetch a client by id, or None."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM oauth_clients WHERE client_id = ?", (client_id,)
        ).fetchone()
    if row is None:
        return None
    return OAuthClient(
        client_id=row["client_id"],
        client_secret=row["client_secret"],
        client_name=row["client_name"],
        redirect_uris=json.loads(row["redirect_uris"]),
        grant_types=json.loads(row["grant_types"]),
        response_types=json.loads(row["response_types"]),
        scope=row["scope"].split() if row["scope"] else [],
        token_endpoint_auth_method=row["token_endpoint_auth_method"],
    )


# ---- Authorization codes -------------------------------------------------


def generate_code() -> str:
    """Cryptographically random, URL-safe code."""
    return secrets.token_urlsafe(32)


def save_authorization_code(code: AuthorizationCode, *, db_path: Path | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO oauth_authorization_codes
              (code, client_id, redirect_uri, scope, code_challenge,
               code_challenge_method, subject, expires_at, used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                code.code,
                code.client_id,
                code.redirect_uri,
                " ".join(code.scope),
                code.code_challenge,
                code.code_challenge_method,
                code.subject,
                code.expires_at,
                int(time.time()),
            ),
        )
        conn.commit()


def consume_authorization_code(
    code: str, *, db_path: Path | None = None
) -> AuthorizationCode | None:
    """Atomically mark a code as used and return it.

    Returns None if the code is unknown, already used, or expired. The
    single-use semantic is enforced by the UPDATE's WHERE clause — a
    concurrent second call will match zero rows.
    """
    now = int(time.time())
    with _connect(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE oauth_authorization_codes
               SET used = 1
             WHERE code = ? AND used = 0 AND expires_at > ?
            """,
            (code, now),
        )
        if cur.rowcount == 0:
            conn.commit()
            return None
        row = conn.execute(
            "SELECT * FROM oauth_authorization_codes WHERE code = ?", (code,)
        ).fetchone()
        conn.commit()
    if row is None:
        return None
    return AuthorizationCode(
        code=row["code"],
        client_id=row["client_id"],
        redirect_uri=row["redirect_uri"],
        scope=row["scope"].split() if row["scope"] else [],
        code_challenge=row["code_challenge"],
        code_challenge_method=row["code_challenge_method"],
        subject=row["subject"],
        expires_at=int(row["expires_at"]),
        used=True,
    )


# ---- Refresh tokens ------------------------------------------------------


def _hash_refresh(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def save_refresh_token(
    *,
    token: str,
    client_id: str,
    subject: str,
    scope: list[str],
    expires_at: int,
    db_path: Path | None = None,
) -> None:
    """Persist a refresh token as a sha256 hash."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO oauth_refresh_tokens
              (token_hash, client_id, subject, scope, expires_at, revoked, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (
                _hash_refresh(token),
                client_id,
                subject,
                " ".join(scope),
                expires_at,
                int(time.time()),
            ),
        )
        conn.commit()


def lookup_refresh_token(token: str, *, db_path: Path | None = None) -> dict | None:
    """Look up a refresh token by its hash. Returns dict or None if unknown/revoked/expired."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM oauth_refresh_tokens WHERE token_hash = ?",
            (_hash_refresh(token),),
        ).fetchone()
    if row is None:
        return None
    if int(row["revoked"]) == 1 or int(row["expires_at"]) < int(time.time()):
        return None
    return {
        "client_id": row["client_id"],
        "subject": row["subject"],
        "scope": row["scope"].split() if row["scope"] else [],
        "expires_at": int(row["expires_at"]),
    }


def revoke_refresh_token(token: str, *, db_path: Path | None = None) -> None:
    """Mark a refresh token revoked (after use in rotation)."""
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE oauth_refresh_tokens SET revoked = 1 WHERE token_hash = ?",
            (_hash_refresh(token),),
        )
        conn.commit()
