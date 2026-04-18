# Galactica 2.0 Phase 1 — consolidated deployment runbook

Single source of truth for shipping Phase 1 to M2. Top-to-bottom execution;
do not skip steps. Each step has a stop condition — if it trips, stop and
contact **Claude CTO**. Do not improvise past a failure.

**Approximate wall-clock**: 20–30 minutes. Brief service downtime (~10 s)
during launchctl reload in Step 8.

**What you'll need at hand before starting**:

- SSH access to `admin@100.83.147.42` (M2 Mac Mini)
- Access to the Cloudflare Zero Trust dashboard (policy changes)
- Your password manager (you'll store one generated secret + one chosen password)
- A browser open to https://claude.ai (custom connector setup at the end)

**What this does**:

1. Generates an RSA keypair on M2 (OAuth signing key)
2. Pulls merged Phase 1 code on M2
3. Installs new Python deps into the active venv
4. Updates the launchd plist with new env vars
5. Restarts Galactica
6. Verifies new endpoints live
7. Seeds the Claude iOS OAuth client
8. Applies Cloudflare Zero Trust bypass policy
9. Verifies externally
10. Adds the Claude iOS connector on claude.ai

---

## STEP 1 — SSH into M2

```bash
ssh admin@100.83.147.42
```

**Stop condition**: SSH fails. If Tailscale isn't up on your laptop, fix that
first. Do not try to diagnose networking from M2.

---

## STEP 2 — Generate the OAuth signing key

```bash
# ~/.ai-memory/ already exists (it's where memories.db lives).
# Generate RSA 2048 keypair, restrictive permissions.
openssl genrsa -out /Users/admin/.ai-memory/galactica_oauth.pem 2048
chmod 600 /Users/admin/.ai-memory/galactica_oauth.pem
ls -la /Users/admin/.ai-memory/galactica_oauth.pem

# Confirm it parses as a valid RSA key.
openssl rsa -in /Users/admin/.ai-memory/galactica_oauth.pem -check -noout
```

**Expected**: the final command prints `RSA key ok`.

**Stop condition**: key generation or validation fails. `openssl` missing
from `/opt/homebrew/bin/` would be a surprise — stop and report.

**Note**: this PEM file lives on M2 only. Do NOT copy it anywhere else.
Keep a record in your password manager that this key exists at this path
(key material itself doesn't need to be in the manager — it's recoverable
only from the file, which is fine for this use case).

---

## STEP 3 — Pick and record the authorize password

Choose a strong passphrase (your password manager can generate one — 32+ chars
recommended). Store it in your password manager under an entry named
`Galactica OAuth authorize password`. You'll type this on the consent page
whenever you approve a new OAuth grant.

**You won't paste this password into the terminal now.** You'll paste it
into the plist in Step 6.

---

## STEP 4 — Navigate to repo and pull merged main

```bash
cd /Users/admin/universal-memory-system
git status -s                        # expect: empty (clean working tree since baseline push)
git fetch origin
git log --oneline main..origin/main  # shows new Phase 1 commits
git pull --ff-only origin main       # fast-forward to d6b44b4 or later
git log --oneline -5
```

**Expected log top**: a merge commit, then `chore(phase1)`, `fix(phase1)`,
`feat(phase1)`, then the baseline commit.

**Stop condition**:
- `git status -s` shows dirty state (should be clean after baseline push).
- `git pull --ff-only` refuses because local main has diverged.

---

## STEP 5 — Install Phase 1 Python deps into venv_new

```bash
./venv_new/bin/pip install --upgrade pip --quiet
./venv_new/bin/pip install --quiet \
    'authlib>=1.7.0,<2.0.0' \
    'joserfc>=1.6.0,<2.0.0' \
    'cryptography>=46.0.0' \
    'python-multipart>=0.0.6'

# Verify imports work under Python 3.14.
./venv_new/bin/python - <<'PY'
from fastapi import FastAPI
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from joserfc import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
print("phase1 deps import ok")
PY
```

**Expected final output**: `phase1 deps import ok`.

**Stop condition**: any `pip install` fails, or the import check fails. The
import check is the canary — if it passes, launchd's restart in Step 8 will
succeed.

---

## STEP 6 — Update the launchd plist

```bash
# Back up the existing plist.
cp /Users/admin/Library/LaunchAgents/com.galactica.plist \
   /Users/admin/Library/LaunchAgents/com.galactica.plist.pre-phase1.backup

# Open in your editor.
open -a TextEdit /Users/admin/Library/LaunchAgents/com.galactica.plist
```

**In TextEdit**: locate the existing `<key>EnvironmentVariables</key>` /
`<dict>...</dict>` block. Add these three entries INSIDE that existing dict,
right before its closing `</dict>`:

```xml
        <key>GALACTICA_OAUTH_PRIVATE_KEY</key>
        <string>PASTE_FULL_PEM_INCLUDING_BEGIN_AND_END_LINES</string>
        <key>GALACTICA_AUTHORIZE_PASSWORD</key>
        <string>PASTE_AUTHORIZE_PASSWORD_FROM_STEP_3</string>
        <key>GALACTICA_ISSUER</key>
        <string>https://galactica.barge2rail.com</string>
```

**To get the PEM contents**:

```bash
cat /Users/admin/.ai-memory/galactica_oauth.pem
```

Copy the entire output (including the `-----BEGIN PRIVATE KEY-----` and
`-----END PRIVATE KEY-----` lines) and paste between the `<string>` tags.
Literal newlines are fine — plist XML tolerates them.

Save and close TextEdit.

**Validate the plist parses:**

```bash
plutil -lint /Users/admin/Library/LaunchAgents/com.galactica.plist
```

**Expected**: exactly `OK`.

**Stop condition**: `plutil -lint` prints anything other than `OK`. This
means the XML is broken — most likely cause is an unescaped `<` or `&` in
the PEM (extremely rare, but possible). If this happens, restore the backup
and try again:

```bash
cp /Users/admin/Library/LaunchAgents/com.galactica.plist.pre-phase1.backup \
   /Users/admin/Library/LaunchAgents/com.galactica.plist
```

---

## STEP 7 — Verify current service state before reload

```bash
# Confirm the service is running on 8091 right now.
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8091/api/health
```

**Expected**: `200`.

**Stop condition**: anything other than `200`. If the service is already
down, the reload in Step 8 won't fix it — fix the underlying issue first.

---

## STEP 8 — Reload launchd (brief downtime)

```bash
launchctl unload /Users/admin/Library/LaunchAgents/com.galactica.plist
launchctl load   /Users/admin/Library/LaunchAgents/com.galactica.plist
sleep 3
launchctl list | grep com.galactica
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8091/api/health
```

**Expected**:
- `launchctl list` line shows `com.galactica` with a PID in the first column
  (not `-`).
- `curl` returns `200`.

**Stop condition**:
- `launchctl list` shows PID as `-` → process crashed on startup. Tail the
  log to find why:
  ```bash
  tail -n 100 /Users/admin/Library/Logs/com.galactica.log 2>/dev/null || \
  tail -n 100 /tmp/com.galactica.*.log 2>/dev/null || \
  log show --predicate 'process == "python3"' --last 2m | tail -n 100
  ```
- Restore the backup plist and reload to recover:
  ```bash
  cp /Users/admin/Library/LaunchAgents/com.galactica.plist.pre-phase1.backup \
     /Users/admin/Library/LaunchAgents/com.galactica.plist
  launchctl unload /Users/admin/Library/LaunchAgents/com.galactica.plist
  launchctl load   /Users/admin/Library/LaunchAgents/com.galactica.plist
  ```
  Then STOP and contact Claude CTO with the log output.

---

## STEP 9 — Verify new Phase 1 endpoints (on M2, localhost only)

```bash
# Metadata endpoints — public, should return JSON.
curl -s http://localhost:8091/.well-known/oauth-authorization-server | python3 -m json.tool | head -12
curl -s http://localhost:8091/.well-known/oauth-protected-resource | python3 -m json.tool
curl -s http://localhost:8091/.well-known/jwks.json | python3 -m json.tool | head -6

# /mcp without a token — should 401 with WWW-Authenticate.
curl -s -i http://localhost:8091/mcp -X POST -H "Content-Type: application/json" -d '{}' | head -8
```

**Expected**:
- First three commands: JSON output with fields like `issuer`, `resource`, `kty`.
- `/mcp` response starts with `HTTP/1.1 401` and includes a
  `WWW-Authenticate: Bearer ... resource_metadata=...` header.

**Stop condition**:
- Any metadata endpoint returns HTML instead of JSON → routes didn't register
  (plist env var missing or typo).
- `/mcp` returns 500 instead of 401 → `GALACTICA_OAUTH_PRIVATE_KEY` env var
  isn't reaching the process. Check the plist; reload.

---

## STEP 10 — Seed the Claude iOS OAuth client

You'll need the exact callback URL Claude uses. Get it from the claude.ai
connector setup page before running this step (see Step 14 for the URL
discovery flow — stop here, jump to Step 14 to find the URL, then come back).

Once you have the URL:

```bash
cd /Users/admin/universal-memory-system
./venv_new/bin/python scripts/seed_oauth_client.py "PASTE_CALLBACK_URL_HERE"
```

**Expected output**: lines starting with `seeded Claude iOS:` followed by
the generated `client_id` (format `claude-ios-XXXXXXXX`). **Copy the
`client_id` to your password manager** — you'll enter it in claude.ai.

**Stop condition**: script errors or output is different. If the script
reports `client already seeded`, that's fine (idempotent) unless the
redirect URI has changed. To rotate:

```bash
sqlite3 /Users/admin/.ai-memory/galactica_oauth.db \
  "DELETE FROM oauth_clients WHERE client_id LIKE 'claude-ios-%';"
```

Then re-run the seed command.

---

## STEP 11 — Exit M2

```bash
exit
```

The M2-side work is done. Remaining steps are in your browser.

---

## STEP 12 — Apply Cloudflare Zero Trust bypass policy

Open the Cloudflare Zero Trust dashboard. Navigate:
**Access → Applications → "Add an application"**.

Fill in:

- **Type**: Self-hosted
- **Application name**: `galactica-phase1-oauth-bypass`
- **Session duration**: default (doesn't matter for Bypass)
- **Application domain** — add three entries, ALL on the same hostname
  `galactica.barge2rail.com`:
  - Path: `/mcp`
  - Path: `/oauth/*`
  - Path: `/.well-known/*`
- Save application, proceed to policy step.

Add a policy:

- **Policy name**: `bypass-phase1-public`
- **Action**: **Bypass** ← critical, not Allow
- **Include**: Everyone
- (no other rules)
- Save.

**Stop condition**: you can't find a "Bypass" action, or the UI forces you
to pick an identity provider. That means Cloudflare has changed the UI —
stop and contact Claude CTO. Do NOT save an Allow-action policy by mistake
(that would require users to authenticate with CF, which Claude iOS can't).

---

## STEP 13 — Verify externally (from your laptop, NOT through Tailscale)

Open Terminal on your laptop (or use a cellular-only device to be sure
you're not accidentally inside the trusted network):

```bash
# Public — should return JSON, NOT the CF Access login page.
curl -s https://galactica.barge2rail.com/.well-known/oauth-authorization-server | head
curl -s https://galactica.barge2rail.com/.well-known/oauth-protected-resource | head

# /mcp — should 401 from Galactica (not 403 from Cloudflare).
curl -i -s https://galactica.barge2rail.com/mcp -X POST -H "Content-Type: application/json" -d '{}' | head -8

# /api/health — should 403 from Cloudflare Access (unchanged behavior).
curl -i -s https://galactica.barge2rail.com/api/health | head -5
```

**Expected**:
- `.well-known/*` returns JSON.
- `/mcp` starts with `HTTP/2 401` and has a `www-authenticate: Bearer ...`
  header (lowercase in HTTP/2).
- `/api/health` starts with `HTTP/2 403` and the body is Cloudflare's
  access-denied HTML (NOT a Galactica JSON response).

**Stop condition**:
- `.well-known/*` returns HTML → Cloudflare Bypass Application isn't
  matching. Most common cause: typo in path patterns (e.g., `.well-known`
  without the leading `/`). Edit the application in the CF dashboard.
- `/mcp` returns 403 instead of 401 → same issue.
- `/api/health` returns 200 → the bypass is too broad. **CRITICAL** — this
  leaks existing endpoints publicly. Delete the bypass application
  immediately and stop.

---

## STEP 14 — Add the custom connector on claude.ai

1. Open https://claude.ai in a browser.
2. **Settings → Connectors → Add Custom Connector**.
3. Enter server URL: `https://galactica.barge2rail.com/mcp`
4. Claude will probe the server and display a callback URL for this connector.
   **Copy that callback URL verbatim.**
   - If you haven't run Step 10 yet, this is the URL you need for it.
     Run Step 10 now, then come back.
5. Enter the `client_id` you saved in Step 10 (format `claude-ios-XXXXXXXX`).
6. Claude will redirect you to Galactica's authorize page.
7. You'll see a consent form saying "Application Claude iOS is requesting
   access with scope memory:read".
8. Type the **authorize password** you chose in Step 3.
9. Click **Allow**.
10. Claude should confirm the connector was added.

**Stop condition**: any step here errors visibly. Most likely cause is
callback-URL mismatch — the URL you seeded in Step 10 must exactly match
what claude.ai presents. If mismatched, re-seed (see Step 10's rotation
instructions) with the correct URL and retry.

---

## STEP 15 — End-to-end iOS verification

On your iOS device:

1. Open Claude app. Confirm the Galactica connector is listed in Settings.
2. Ask Claude: *"Use Galactica to search for 'test query'"*.
   **Expected**: Claude calls `search_nodes`, shows results.
3. Ask Claude: *"Use Galactica to store a memory saying 'Phase 1 iOS test'"*.
   **Expected**: Claude attempts the call, receives a scope error, tells
   you it doesn't have permission to write. This is correct — the Claude
   iOS client was seeded with `memory:read` only.

**Stop condition**: either step fails in a way that isn't an explicit
scope-error response. Capture screenshots and contact Claude CTO.

---

## STEP 16 — Spot-check the audit log

Back on M2:

```bash
ssh admin@100.83.147.42
sqlite3 /Users/admin/.ai-memory/galactica_audit.db \
  "SELECT timestamp, client_id, tool_name, success, error_code \
   FROM mcp_audit_log ORDER BY id DESC LIMIT 10;"
exit
```

**Expected**: recent rows reflecting your Step 15 activity:
- one row per `search_nodes` call with `success=1`, `error_code=NULL`
- one row per `store_memory` attempt with `success=0`,
  `error_code=insufficient_scope`
- no rows containing cleartext search queries or memory content
  (verify by scanning the output — only hashes, timestamps, tool names
  should appear)

**Stop condition**:
- No rows at all → MCP tool calls aren't reaching the audit layer. The tool
  responses in Step 15 were something else (cached? a different endpoint?).
  Contact CTO.
- Any cleartext query/content string appears in the dump. Contact CTO
  immediately; redaction invariant failed.

---

## STEP 17 — Confirm existing consumers still work (parallel-operation canary)

From your laptop:

```bash
# ChatGPT custom GPT path — still gated by CF Access service tokens.
# Trigger a ChatGPT query that normally hits Galactica. Confirm it works.
```

Check n8n uptime monitor on M2 — no alerts in the last hour.

**Stop condition**: ChatGPT Custom GPT can't reach Galactica anymore, OR
n8n uptime alert fires. That implies the CF policy changes affected the
wrong paths. Contact CTO.

---

## Rollback procedure (execute if the full deploy goes wrong)

If anything past Step 8 fails hard enough that you need to revert:

```bash
ssh admin@100.83.147.42
cd /Users/admin/universal-memory-system
git log --oneline -5   # note current HEAD

# Revert to pre-Phase-1 baseline (undoes code but keeps commit history).
git revert --no-commit HEAD~1..HEAD
# The exact range depends on how many merge commits landed; the goal is to
# revert to 8fc8ffe (baseline) without touching the baseline itself.
# Safer alternative: hard reset to the baseline commit.
git reset --hard 8fc8ffe

# Restore the original plist.
cp /Users/admin/Library/LaunchAgents/com.galactica.plist.pre-phase1.backup \
   /Users/admin/Library/LaunchAgents/com.galactica.plist
launchctl unload /Users/admin/Library/LaunchAgents/com.galactica.plist
launchctl load   /Users/admin/Library/LaunchAgents/com.galactica.plist
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8091/api/health   # expect 200

exit
```

Delete the Cloudflare Bypass Application in the CF dashboard.

This restores Galactica to its pre-Phase-1 state. Tell CTO what happened.

---

## "Call Claude CTO if..." quick reference

- Step 2: `openssl` missing or RSA key doesn't validate.
- Step 4: `git pull --ff-only` rejected.
- Step 5: `pip install` fails, or the Python import check errors.
- Step 6: `plutil -lint` prints anything other than `OK`.
- Step 8: service doesn't come up after reload (PID `-` in `launchctl list`).
- Step 9: `/mcp` returns 500 instead of 401.
- Step 12: can't find a "Bypass" action in the CF UI.
- Step 13: `/api/health` returns 200 externally (bypass is too broad — **urgent**).
- Step 15: a tool call fails in a way that isn't a scope error.
- Step 16: audit rows missing, or cleartext content visible in the log.
- Step 17: ChatGPT Custom GPT fails, or n8n alerts.

Never improvise past any of these. The rollback procedure above exists
because the cost of a bad guess on personal infra is a weekend.
