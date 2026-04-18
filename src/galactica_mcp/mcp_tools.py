"""Tool implementations for the MCP endpoint.

These mirror the four tools exposed by the stdio MCP wrapper
(/Users/cerion/Projects/galactica-mcp-server/galactica-mcp-server.js).
Output shapes match the wrapper's shapes — criterion #5 of the acceptance
checklist requires identical shape for search_nodes.

Tools call memory_service directly rather than looping back over HTTP.
That avoids a self-call through the CF tunnel and removes any ambiguity
about which auth layer applies.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Tool-list is the authoritative schema; it's exposed via tools/list and MUST
# stay in sync with the stdio wrapper's schema.
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_nodes",
        "description": "Search memories using semantic vector search. Returns relevant memories with similarity scores.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (supports multi-keyword semantic search)",
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of results to return (default: 5, max: 50)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "store_memory",
        "description": "Store a new memory in Galactica with tags, importance, and project context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Memory content to store"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorization (optional)",
                    "default": [],
                },
                "importance": {
                    "type": "number",
                    "description": "Importance level from 1-10 (default: 5)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 10,
                },
                "project": {"type": "string", "description": "Project context (optional)"},
                "category": {
                    "type": "string",
                    "description": "Memory category (default: note)",
                    "default": "note",
                },
            },
            "required": ["content"],
        },
    },
    {
        "name": "get_context",
        "description": "Get AI-ready context string from relevant memories for a given topic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Topic to get context for"},
                "limit": {
                    "type": "number",
                    "description": "Number of memories to include (default: 10, max: 50)",
                    "default": 10,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "health_check",
        "description": "Check Galactica service status and get system information.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _get_service() -> Any:
    """Resolve the running memory service singleton. Imported lazily to avoid
    import-time dependencies on the full api_service module."""
    from memory_service import get_memory_service  # type: ignore[import-not-found]
    return get_memory_service()


def _clamp(value: Any, *, low: int, high: int, default: int) -> int:
    """Coerce an arbitrary value into an int within [low, high], defaulting on failure."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(n, high))


# ==========================================================================
# Tool implementations — shape-identical to the stdio wrapper
# ==========================================================================


async def search_nodes(args: dict[str, Any]) -> dict[str, Any]:
    """Semantic memory search. Mirrors the stdio wrapper's shape."""
    query = args.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("'query' is required and must be a non-empty string")
    limit = _clamp(args.get("limit", 5), low=1, high=50, default=5)

    service = _get_service()
    results = service.search_memories(
        query=query.strip(),
        project=None,
        category=None,
        tags=None,
        min_importance=0,
        limit=limit,
        include_semantic=True,
    )
    return {
        "query": query,
        "count": len(results),
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def store_memory(args: dict[str, Any]) -> dict[str, Any]:
    """Store a new memory. Shape mirrors the stdio wrapper."""
    content = args.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("'content' is required and must be a non-empty string")
    importance = _clamp(args.get("importance", 5), low=1, high=10, default=5)
    tags = args.get("tags") or []
    if not isinstance(tags, list):
        raise ValueError("'tags' must be a list of strings")
    project = args.get("project")
    category = args.get("category") or "note"

    service = _get_service()
    result = service.store_memory(
        content=content.strip(),
        project=project.strip() if isinstance(project, str) and project.strip() else None,
        category=category,
        tags=tags,
        importance=importance,
    )
    return {
        "id": result.get("id"),
        "status": result.get("status", "stored"),
        "project": result.get("project"),
        "category": result.get("category", category),
    }


async def get_context(args: dict[str, Any]) -> str:
    """Return a context string. MCP content wrapping happens in the router."""
    query = args.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("'query' is required and must be a non-empty string")
    limit = _clamp(args.get("limit", 10), low=1, high=50, default=10)

    service = _get_service()
    context = service.get_context(
        relevant_to=query.strip(),
        project=None,
        max_tokens=4000,
        include_cross_project=True,
        protection_aware=True,
    )
    if context is None:
        return ""
    if isinstance(context, str):
        return context
    return str(context)


async def health_check(_args: dict[str, Any]) -> dict[str, Any]:
    """Return service health. Shape mirrors the stdio wrapper."""
    service = _get_service()
    health = service.health_check()
    stats = service.get_statistics()
    overall = stats.get("overall", {}) if isinstance(stats, dict) else {}
    return {
        "status": health.get("status") if isinstance(health, dict) else "unknown",
        "total_memories": overall.get("total_memories"),
        "total_projects": overall.get("total_projects"),
        "embedding_provider": overall.get("embedding_provider"),
        "vector_search_enabled": overall.get("vector_search_enabled", False),
        "storage_path": overall.get("storage_path"),
    }


TOOL_DISPATCH = {
    "search_nodes": search_nodes,
    "store_memory": store_memory,
    "get_context": get_context,
    "health_check": health_check,
}
