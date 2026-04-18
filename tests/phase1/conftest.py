"""Shared fixtures for Phase 1 tests.

Builds a throw-away FastAPI app with only the Galactica MCP+OAuth routers
mounted. memory_service is not used directly; tests monkeypatch
galactica_mcp.mcp_tools._get_service to return a fake service that mirrors
the methods the tools call.

Each test gets:
  - fresh sqlite DBs in a tmp_path
  - a fresh RSA keypair in env
  - its own authorize password
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Make src/ importable.
_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def rsa_private_key_pem() -> str:
    """Generate an RSA 2048 keypair and return the PEM-encoded private key."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.decode("ascii")


@pytest.fixture
def configured_env(monkeypatch, tmp_path, rsa_private_key_pem):
    """Point config at throw-away DBs + inject a test keypair + set the password."""
    audit_db = tmp_path / "audit.db"
    oauth_db = tmp_path / "oauth.db"
    monkeypatch.setenv("GALACTICA_ISSUER", "https://test.galactica.local")
    monkeypatch.setenv("GALACTICA_RESOURCE", "https://test.galactica.local/mcp")
    monkeypatch.setenv("GALACTICA_OAUTH_PRIVATE_KEY", rsa_private_key_pem)
    monkeypatch.setenv("GALACTICA_AUTHORIZE_PASSWORD", "test-password")
    monkeypatch.setenv("GALACTICA_AUDIT_DB", str(audit_db))
    monkeypatch.setenv("GALACTICA_OAUTH_DB", str(oauth_db))

    # Force module-level reload so the env vars take effect for this test.
    # Popping from sys.modules alone is insufficient — the parent package still
    # caches submodules as attributes, so `from galactica_mcp import config`
    # would return the stale module. Clear both.
    _SUBMODULES = (
        "config", "tokens", "audit", "oauth_storage",
        "oauth_router", "mcp_tools", "mcp_router",
    )
    for sub in _SUBMODULES:
        sys.modules.pop(f"galactica_mcp.{sub}", None)
    pkg = sys.modules.get("galactica_mcp")
    if pkg is not None:
        for sub in _SUBMODULES:
            if hasattr(pkg, sub):
                delattr(pkg, sub)

    from galactica_mcp import audit, config, oauth_storage, tokens  # noqa: F401
    audit.init_db()
    oauth_storage.init_db()
    tokens.reset_key_cache_for_tests()

    return {
        "audit_db": audit_db,
        "oauth_db": oauth_db,
        "issuer": "https://test.galactica.local",
        "resource": "https://test.galactica.local/mcp",
        "password": "test-password",
    }


class FakeMemoryService:
    """Minimal stub of UniversalMemoryService — only the methods MCP tools call."""

    def __init__(self) -> None:
        self.stored: list[dict] = []

    def search_memories(self, *, query, project, category, tags,
                        min_importance, limit, include_semantic):
        return [{"id": 1, "content": f"match for {query}", "importance": 7}]

    def store_memory(self, *, content, project, category, tags, importance):
        entry = {"id": len(self.stored) + 1, "status": "stored",
                 "project": project or "default", "category": category}
        self.stored.append(entry)
        return entry

    def get_context(self, *, relevant_to, project, max_tokens,
                    include_cross_project, protection_aware):
        return f"CONTEXT for {relevant_to}"

    def health_check(self):
        return {"status": "ok"}

    def get_statistics(self):
        return {"overall": {
            "total_memories": 42,
            "total_projects": 3,
            "embedding_provider": "test",
            "vector_search_enabled": True,
            "storage_path": "/test/memories.db",
        }}


@pytest.fixture
def fake_service(monkeypatch, configured_env):
    """Install FakeMemoryService as the backend the MCP tools see."""
    service = FakeMemoryService()
    import galactica_mcp.mcp_tools as mcp_tools
    monkeypatch.setattr(mcp_tools, "_get_service", lambda: service)
    return service


@pytest.fixture
def app(configured_env):
    """Build a throw-away FastAPI app with only the Galactica routers."""
    from fastapi import FastAPI

    from galactica_mcp.mcp_router import router as mcp_router
    from galactica_mcp.oauth_router import router as oauth_router

    app = FastAPI()
    app.include_router(oauth_router)
    app.include_router(mcp_router)
    return app


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    return TestClient(app)
