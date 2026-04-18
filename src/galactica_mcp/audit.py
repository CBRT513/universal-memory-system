"""MCP audit log.

Every /mcp tool call writes exactly one row, success or failure. Writes are
synchronous; audit-write failure fails the tool call so we never serve traffic
we can't account for.

Args are stored as a sha256 hex digest of a canonical JSON encoding. Raw args
never touch disk — they can carry user content we shouldn't retain.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS mcp_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    client_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    args_hash TEXT NOT NULL,
    result_size_bytes INTEGER NOT NULL,
    success INTEGER NOT NULL,
    error_code TEXT
);
CREATE INDEX IF NOT EXISTS idx_mcp_audit_timestamp ON mcp_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_mcp_audit_client ON mcp_audit_log(client_id);
"""


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def init_db(db_path: Path | None = None) -> None:
    """Create the audit DB and table if they don't already exist."""
    path = db_path or config.AUDIT_DB_PATH
    _ensure_parent(path)
    with sqlite3.connect(str(path)) as conn:
        conn.executescript(_SCHEMA)
        conn.commit()


def hash_args(args: Any) -> str:
    """Return sha256 hex of a canonical JSON encoding of args.

    Uses sort_keys + separators with no whitespace so logically-equal args
    always hash identically regardless of input dict order. Non-serializable
    args fall back to str() — defensive, but all our tool args are JSON-safe.
    """
    try:
        serialized = json.dumps(args, sort_keys=True, separators=(",", ":"), default=str)
    except (TypeError, ValueError):
        serialized = str(args)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def record(
    *,
    client_id: str,
    scope: list[str] | str,
    tool_name: str,
    args: Any,
    result_size_bytes: int,
    success: bool,
    error_code: str | None = None,
    db_path: Path | None = None,
) -> int:
    """Write one audit row synchronously. Returns the inserted row id.

    A raised exception here propagates: the caller MUST let it fail the tool call.
    """
    path = db_path or config.AUDIT_DB_PATH
    scope_str = scope if isinstance(scope, str) else " ".join(scope)
    _ensure_parent(path)
    with sqlite3.connect(str(path)) as conn:
        cur = conn.execute(
            """
            INSERT INTO mcp_audit_log
              (timestamp, client_id, scope, tool_name, args_hash,
               result_size_bytes, success, error_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(timespec="microseconds"),
                client_id,
                scope_str,
                tool_name,
                hash_args(args),
                int(result_size_bytes),
                1 if success else 0,
                error_code,
            ),
        )
        conn.commit()
        return int(cur.lastrowid or 0)
