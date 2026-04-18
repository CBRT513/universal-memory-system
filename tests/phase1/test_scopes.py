"""Scope expansion, parsing, and enforcement helpers."""
from __future__ import annotations

from galactica_mcp import scopes


def test_expand_read_returns_read():
    assert scopes.expand(["memory:read"]) == ["memory:read"]


def test_expand_write_includes_read():
    result = scopes.expand(["memory:write"])
    assert "memory:read" in result
    assert "memory:write" in result
    assert "memory:admin" not in result


def test_expand_admin_includes_all():
    result = scopes.expand(["memory:admin"])
    assert set(result) == {"memory:read", "memory:write", "memory:admin"}


def test_expand_unknown_scope_dropped():
    assert scopes.expand(["garbage", "memory:read"]) == ["memory:read"]


def test_parse_dedupes_and_preserves_order():
    assert scopes.parse("memory:read memory:write memory:read") == [
        "memory:read",
        "memory:write",
    ]


def test_parse_empty_returns_empty():
    assert scopes.parse("") == []
    assert scopes.parse("   ") == []


def test_validate_subset_filters_to_allowed():
    allowed = ["memory:read"]
    requested = ["memory:read", "memory:write", "memory:admin"]
    assert scopes.validate_subset(requested, allowed) == ["memory:read"]


def test_has_scope_match():
    assert scopes.has_scope(["memory:read", "memory:write"], "memory:read")


def test_has_scope_miss():
    assert not scopes.has_scope(["memory:read"], "memory:write")


def test_tool_required_scope_read_tools():
    assert scopes.TOOL_REQUIRED_SCOPE["search_nodes"] == scopes.MEMORY_READ
    assert scopes.TOOL_REQUIRED_SCOPE["get_context"] == scopes.MEMORY_READ
    assert scopes.TOOL_REQUIRED_SCOPE["health_check"] == scopes.MEMORY_READ


def test_tool_required_scope_write_tool():
    assert scopes.TOOL_REQUIRED_SCOPE["store_memory"] == scopes.MEMORY_WRITE
