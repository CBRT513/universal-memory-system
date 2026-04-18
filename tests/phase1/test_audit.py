"""Audit log recording and args hashing."""
from __future__ import annotations

import json
import sqlite3


def test_hash_args_is_stable(configured_env):
    from galactica_mcp import audit
    # Different dict orderings must hash identically.
    a = audit.hash_args({"b": 2, "a": 1})
    b = audit.hash_args({"a": 1, "b": 2})
    assert a == b


def test_hash_args_differs_on_content(configured_env):
    from galactica_mcp import audit
    assert audit.hash_args({"q": "foo"}) != audit.hash_args({"q": "bar"})


def test_record_writes_row(configured_env):
    from galactica_mcp import audit, config
    row_id = audit.record(
        client_id="c1",
        scope=["memory:read"],
        tool_name="search_nodes",
        args={"query": "hello", "limit": 5},
        result_size_bytes=42,
        success=True,
    )
    assert row_id > 0
    with sqlite3.connect(str(config.AUDIT_DB_PATH)) as conn:
        rows = conn.execute("SELECT * FROM mcp_audit_log").fetchall()
    assert len(rows) == 1
    row = rows[0]
    # (id, ts, client_id, scope, tool_name, args_hash, size, success, error_code)
    assert row[2] == "c1"
    assert row[3] == "memory:read"
    assert row[4] == "search_nodes"
    # args hash must be 64 hex chars (sha256)
    assert len(row[5]) == 64
    assert all(c in "0123456789abcdef" for c in row[5])
    assert row[6] == 42
    assert row[7] == 1
    assert row[8] is None


def test_record_failure_row(configured_env):
    from galactica_mcp import audit, config
    audit.record(
        client_id="c1",
        scope=["memory:read"],
        tool_name="store_memory",
        args={"content": "x"},
        result_size_bytes=0,
        success=False,
        error_code="insufficient_scope",
    )
    with sqlite3.connect(str(config.AUDIT_DB_PATH)) as conn:
        row = conn.execute(
            "SELECT success, error_code FROM mcp_audit_log"
        ).fetchone()
    assert row[0] == 0
    assert row[1] == "insufficient_scope"


def test_cleartext_args_never_stored(configured_env):
    """The sensitive args string must never appear in any audit column."""
    from galactica_mcp import audit, config
    secret = "SUPER-SECRET-CONTENT-STRING-UNIQUE-" + "x" * 20
    audit.record(
        client_id="c1",
        scope=["memory:write"],
        tool_name="store_memory",
        args={"content": secret},
        result_size_bytes=10,
        success=True,
    )
    with sqlite3.connect(str(config.AUDIT_DB_PATH)) as conn:
        rows = conn.execute("SELECT * FROM mcp_audit_log").fetchall()
    dumped = json.dumps(rows)
    assert secret not in dumped
