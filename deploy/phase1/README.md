# Galactica 2.0 Phase 1 — deployment artifacts

Runbooks and configuration diffs for shipping Phase 1 (native MCP + OAuth 2.1)
to the M2 Mac Mini.

- **`plist-runbook.md`** — launchd plist update (deployment step 5)
- **`com.galactica.plist.proposed`** — the new plist contents
- **`cloudflare-policy.md`** — Zero Trust Access bypass setup (step 6)
- **`seed-oauth-client.md`** — insert the Claude iOS OAuth client (after step 7)

## Deployment sequence reminder (from original brief)

| Step | Actor          | Action                                                                |
|------|----------------|-----------------------------------------------------------------------|
| 1    | Clif           | Code on `feature/mcp-oauth-phase-1`, PR opened, `@codex review` tagged |
| 2    | Claude CTO     | Adjudicate Codex findings; CC applies fixes                           |
| 3    | CC             | Full test suite on M2 against port 8092 (non-prod)                    |
| 4    | CC             | Present plist/cloudflared/CF policy diffs for Clif approval           |
| 5    | CC via Clif    | Update launchd plist, restart on 8091 (see `plist-runbook.md`)        |
| 6    | Clif           | Apply CF Zero Trust changes in console (see `cloudflare-policy.md`)   |
| 7    | CC             | Verify AC 1, 2, 8 from outside the network                            |
| 8    | Clif           | Add custom connector on claude.ai with `/mcp` URL + client id          |
| 9    | Clif           | Complete OAuth flow; verify AC 3–7                                    |
| 10   | Clif           | iOS test: read succeeds, write returns scope error                    |

## Tunnel config

The cloudflared tunnel config (`~/.cloudflared/config.yml`) requires **no
changes**. The tunnel is path-agnostic; CF Access handles auth per path.
