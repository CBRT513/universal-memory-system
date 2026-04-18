"""Scope model for Galactica MCP.

Three scopes are defined in code from day one. memory:admin has no tool
handlers in Phase 1 — the scope exists so the plumbing is designed in,
not bolted on later.

Scopes are hierarchical: granting a higher scope implies lower scopes.
Expansion happens at token issuance, not at check time, so enforcement
is a simple membership test.
"""
from __future__ import annotations

from typing import Iterable

MEMORY_READ = "memory:read"
MEMORY_WRITE = "memory:write"
MEMORY_ADMIN = "memory:admin"

ALL_SCOPES: tuple[str, ...] = (MEMORY_READ, MEMORY_WRITE, MEMORY_ADMIN)

_IMPLIES: dict[str, tuple[str, ...]] = {
    MEMORY_READ: (MEMORY_READ,),
    MEMORY_WRITE: (MEMORY_READ, MEMORY_WRITE),
    MEMORY_ADMIN: (MEMORY_READ, MEMORY_WRITE, MEMORY_ADMIN),
}

TOOL_REQUIRED_SCOPE: dict[str, str] = {
    "search_nodes": MEMORY_READ,
    "get_context": MEMORY_READ,
    "health_check": MEMORY_READ,
    "store_memory": MEMORY_WRITE,
}


def expand(scopes: Iterable[str]) -> list[str]:
    """Expand a scope list to include all implied scopes. Unknown scopes are dropped."""
    expanded: set[str] = set()
    for scope in scopes:
        if scope in _IMPLIES:
            expanded.update(_IMPLIES[scope])
    return sorted(expanded)


def parse(scope_string: str) -> list[str]:
    """Parse a space-separated scope string into a list, preserving order, deduped."""
    seen: set[str] = set()
    result: list[str] = []
    for token in scope_string.split():
        if token and token not in seen:
            seen.add(token)
            result.append(token)
    return result


def validate_subset(requested: Iterable[str], allowed: Iterable[str]) -> list[str]:
    """Return the intersection of requested and allowed scopes, preserving request order.

    Used at token issuance: even if a client asks for memory:admin, the server
    returns only the subset the client is actually permitted to have.
    """
    allowed_set = set(allowed)
    return [s for s in requested if s in allowed_set]


def has_scope(token_scopes: Iterable[str], required: str) -> bool:
    """Check whether a token carries the required scope (after expansion)."""
    return required in set(token_scopes)
