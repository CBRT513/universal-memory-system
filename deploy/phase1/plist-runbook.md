# Launchd plist update runbook — Phase 1

Applied by **Clif** on **M2** during deployment step 5. Windowed downtime ~5 s.

## 1. Generate the OAuth signing key (one-time)

```bash
# On M2
openssl genrsa -out /Users/admin/.ai-memory/galactica_oauth.pem 2048
chmod 600 /Users/admin/.ai-memory/galactica_oauth.pem
```

The PEM file never enters the repo. It's read into the launchd plist below.
Key rotation later means regenerate + update plist + restart.

## 2. Choose a strong authorize password

Any high-entropy string (Clif's password manager). This is the trust boundary
for the /oauth/authorize consent step.

## 3. Prepare the plist (stage, don't activate)

```bash
# On M2
cp /Users/admin/Library/LaunchAgents/com.galactica.plist \
   /Users/admin/Library/LaunchAgents/com.galactica.plist.pre-phase1.backup

# Paste new contents from deploy/phase1/com.galactica.plist.proposed,
# substituting:
#   REPLACE_WITH_PEM_PRIVATE_KEY  → full PEM contents (BEGIN/END lines included,
#                                   literal newlines; plist tolerates them)
#   REPLACE_WITH_STRONG_PASSPHRASE → authorize password
```

Sanity-check the plist parses before load:

```bash
plutil -lint /Users/admin/Library/LaunchAgents/com.galactica.plist
# expect: "OK"
```

## 4. Reload launchd

```bash
launchctl unload /Users/admin/Library/LaunchAgents/com.galactica.plist
launchctl load   /Users/admin/Library/LaunchAgents/com.galactica.plist
# confirm it came back up
launchctl list | grep com.galactica
curl -s http://localhost:8091/api/health | head -c 200
```

## 5. Verify OAuth endpoint is live

```bash
curl -s http://localhost:8091/.well-known/oauth-authorization-server | python3 -m json.tool | head
curl -s http://localhost:8091/.well-known/oauth-protected-resource | python3 -m json.tool
curl -s -i http://localhost:8091/mcp | head
# expect: HTTP/1.1 401 ... WWW-Authenticate: Bearer ...
```

## Rollback

One command restores the pre-Phase-1 plist:

```bash
cp /Users/admin/Library/LaunchAgents/com.galactica.plist.pre-phase1.backup \
   /Users/admin/Library/LaunchAgents/com.galactica.plist
launchctl unload /Users/admin/Library/LaunchAgents/com.galactica.plist
launchctl load   /Users/admin/Library/LaunchAgents/com.galactica.plist
```

The new code still executes (it's in the repo and venv) but the OAuth routes
will fail on startup because `GALACTICA_OAUTH_PRIVATE_KEY` will be empty.
That's fine — Phase 1 routes remain reachable only through auth, and auth
fails closed. Existing `/api/*` endpoints are untouched.
