"""Galactica 2.0 Phase 1 — native MCP-over-HTTP + embedded OAuth 2.1.

This package adds a native MCP endpoint at /mcp protected by an OAuth 2.1
authorization server to the existing Galactica FastAPI service. Existing REST
endpoints are not modified.

Public surface:
- oauth_router: FastAPI router mounting /oauth/* and /.well-known/* endpoints.
- mcp_router:   FastAPI router mounting /mcp (JSON-RPC streamable HTTP).
"""

__version__ = "2.0.0-phase1"
