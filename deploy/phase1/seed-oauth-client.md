# Seeding the Claude iOS OAuth client — Phase 1

Applied by **Clif** on M2 after the plist is live (step 5) and before the
iOS connector flow (step 8).

## What you need first

- Galactica running on M2 with the new plist env vars set (step 5 succeeded).
- The exact Claude custom-connector callback URL — visible in the
  claude.ai **Settings → Connectors → Add Custom Connector** flow after
  you enter `https://galactica.barge2rail.com/mcp` as the server URL.
  Copy it from the claude.ai UI; DO NOT guess.

## Steps

```bash
# On M2
cd /Users/admin/universal-memory-system
./venv_new/bin/python scripts/seed_oauth_client.py "<PASTE CALLBACK URL HERE>"
```

Expected output:
```
seeded Claude iOS:
  client_id:      claude-ios-xxxxxxxx
  redirect_uris:  https://...
  scope:          memory:read
  auth method:    none (PKCE-only public client)
```

Copy the `client_id` — you'll enter it in the claude.ai connector dialog.

## Re-seeding

If you need to change the callback URL, delete the row first:

```bash
sqlite3 /Users/admin/.ai-memory/galactica_oauth.db \
  "DELETE FROM oauth_clients WHERE client_id LIKE 'claude-ios-%';"
```

Then re-run the seed script with the new URL.
