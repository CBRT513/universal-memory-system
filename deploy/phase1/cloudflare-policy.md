# Cloudflare Zero Trust policy changes — Phase 1

Applied by **Clif** in the Cloudflare dashboard during deployment step 6.
Claude Code prepares the plan; Clif executes in the console (Clif owns CF Access).

## Current state (Phase 0 snapshot)

One Zero Trust Access application covers the entire `galactica.barge2rail.com`
hostname. Access is gated by service tokens (Cloudflare-issued client id/secret
headers). Current consumers:

- **galactica-proxy Cloudflare Worker** (ChatGPT Custom GPT)
- **n8n on M2** (uptime monitor + automations)

Both continue to use the CF Access service-token path. Nothing about their
flow changes in Phase 1.

## Target state

OAuth becomes the auth layer for three specific path patterns. CF Access
continues to guard everything else.

| Path pattern         | Auth gate                       | Who uses it                   |
|----------------------|----------------------------------|-------------------------------|
| `/mcp`               | OAuth 2.1 Bearer                 | Claude iOS (Phase 1)          |
| `/oauth/*`           | None — public OAuth endpoints    | Claude iOS (OAuth flow)       |
| `/.well-known/*`     | None — public metadata           | OAuth clients (any)           |
| Everything else      | CF Access service tokens (today) | Worker, n8n, any `/api/*` use |

## Recommended implementation — Bypass Application pattern

This is the pattern Cloudflare recommends for exceptions to a broader Access
policy. It avoids editing the current Application's path rules (which is
where most people make mistakes).

### Steps

1. **Zero Trust dashboard** → Access → Applications → "Add an application"
2. **Type**: Self-hosted
3. **Application name**: `galactica-phase1-oauth-bypass`
4. **Session duration**: (doesn't matter for Bypass)
5. **Application domain**: add THREE entries, all on `galactica.barge2rail.com`:
   - Path: `/mcp`
   - Path: `/oauth/*`
   - Path: `/.well-known/*`
6. **Policies** → Add policy
   - Policy name: `bypass-phase1-public`
   - **Action: Bypass**
   - Include: Everyone
   - (no other rules needed)
7. Save.

**Cloudflare evaluates more-specific Applications first.** The existing
broad-hostname Application still matches the rest of the paths; the new
narrow-path Bypass Application takes precedence for the three carve-outs.

## Verification (outside the network — no service token, no bearer)

```bash
# Should succeed (public) — returns JSON metadata:
curl -i https://galactica.barge2rail.com/.well-known/oauth-authorization-server

# Should succeed (public) — returns JSON metadata:
curl -i https://galactica.barge2rail.com/.well-known/oauth-protected-resource

# Should 401 (WWW-Authenticate) — not 403 from CF Access:
curl -i https://galactica.barge2rail.com/mcp

# Should 403 from CF Access (unchanged existing behavior):
curl -i https://galactica.barge2rail.com/api/health
```

If `/mcp` returns 403 (the CF Access "not authorized" page), the Bypass
application isn't matching. Most common causes: path pattern typo, or the
Bypass application was saved without a policy.

## Rollback

Delete the `galactica-phase1-oauth-bypass` Application in the CF dashboard.
The original broad-hostname Access policy resumes covering everything,
including `/mcp` and `/oauth/*`. OAuth flow will break for Claude iOS
(it can't inject service tokens) but nothing else regresses.

## n8n + ChatGPT impact

**Zero impact.** Both consumers hit `/api/*` paths through the existing
CF Access service-token flow. None of the carve-out paths match their
traffic. The parallel-operation canary (n8n uptime monitor) continues to
alert via the existing mechanism.
