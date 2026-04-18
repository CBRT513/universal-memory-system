#!/usr/bin/env python3
"""Seed the Claude iOS OAuth client into Galactica's oauth_clients table.

Usage:
    python3 scripts/seed_oauth_client.py REDIRECT_URI [REDIRECT_URI ...]

The OAuth 2.1 security BCP disallows wildcard redirect URIs, so Galactica uses
strict string matching. Pass the exact callback URL(s) Claude will redirect to.

The current Claude custom-connector callback URL is visible in the
claude.ai Settings → Connectors → Add Custom Connector flow AFTER you enter
the server URL; it's easier to run this script once you know the value.

If the target client is already present, the script is a no-op (exits 0).
"""
from __future__ import annotations

import secrets
import sys
from pathlib import Path

# Make src/ importable when run as a script from the repo root.
_SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(_SRC))

from galactica_mcp import oauth_storage, scopes  # noqa: E402

CLIENT_NAME = "Claude iOS"
CLIENT_ID_PREFIX = "claude-ios-"


def main(argv: list[str]) -> int:
    """Create the Claude iOS client if it doesn't already exist. Idempotent."""
    if len(argv) < 2:
        print(__doc__)
        return 2
    redirect_uris = argv[1:]

    oauth_storage.init_db()

    # Idempotency — one seeded Claude iOS client at a time. Re-running after
    # the callback URL changes: delete the row in SQLite first, then re-seed.
    for existing_prefix in (CLIENT_ID_PREFIX,):
        # Naive scan; the table will only ever have a handful of rows.
        import sqlite3

        from galactica_mcp import config as cfg

        with sqlite3.connect(str(cfg.OAUTH_DB_PATH)) as conn:
            cur = conn.execute(
                "SELECT client_id FROM oauth_clients WHERE client_id LIKE ?",
                (f"{existing_prefix}%",),
            )
            existing = [r[0] for r in cur.fetchall()]
        if existing:
            print(f"client already seeded: {existing[0]}")
            print("to rotate: delete the row manually then re-run this script")
            return 0

    client_id = f"{CLIENT_ID_PREFIX}{secrets.token_hex(4)}"
    client = oauth_storage.OAuthClient(
        client_id=client_id,
        client_secret=None,
        client_name=CLIENT_NAME,
        redirect_uris=redirect_uris,
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        scope=[scopes.MEMORY_READ],
        token_endpoint_auth_method="none",
    )
    oauth_storage.save_client(client)

    print(f"seeded {CLIENT_NAME}:")
    print(f"  client_id:      {client_id}")
    print(f"  redirect_uris:  {', '.join(redirect_uris)}")
    print(f"  scope:          {scopes.MEMORY_READ}")
    print(f"  auth method:    none (PKCE-only public client)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
