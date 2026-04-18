"""FastAPI router for the OAuth 2.1 authorization server and well-known metadata.

Endpoints mounted:
  POST /oauth/register              — RFC 7591 Dynamic Client Registration
  GET  /oauth/authorize             — render consent form (PKCE required)
  POST /oauth/authorize             — validate password, issue auth code
  POST /oauth/token                 — authorization_code / refresh_token grants
  GET  /.well-known/oauth-authorization-server  — RFC 8414 metadata
  GET  /.well-known/oauth-protected-resource    — RFC 9728 metadata
  GET  /.well-known/jwks.json       — public signing key set

Personal-infra design note: there is no user database. The /oauth/authorize
consent step is gated by a shared password (GALACTICA_AUTHORIZE_PASSWORD env
var). Clif types this to approve a grant. That password is the trust boundary
for the authorization step.
"""
from __future__ import annotations

import html
import secrets
import time
import urllib.parse
from typing import Any

from authlib.oauth2.rfc7636 import create_s256_code_challenge
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from . import config, oauth_storage, scopes, tokens

router = APIRouter(tags=["oauth"])


# ==========================================================================
# Helpers
# ==========================================================================


def _oauth_error(error: str, description: str, status: int = 400) -> JSONResponse:
    """Per RFC 6749 §5.2 — token/registration errors are JSON bodies with a
    stable error code and free-form description."""
    return JSONResponse(
        status_code=status,
        content={"error": error, "error_description": description},
    )


def _redirect_error(
    redirect_uri: str, error: str, description: str, state: str | None
) -> RedirectResponse:
    """Per RFC 6749 §4.1.2.1 — authorize errors are query-param redirects to
    the client's registered redirect URI, not JSON."""
    params = {"error": error, "error_description": description}
    if state is not None:
        params["state"] = state
    separator = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(
        url=f"{redirect_uri}{separator}{urllib.parse.urlencode(params)}",
        status_code=302,
    )


def _verify_pkce(verifier: str, challenge: str, method: str) -> bool:
    """OAuth 2.1 requires S256; we reject everything else."""
    if method != "S256":
        return False
    expected = create_s256_code_challenge(verifier)
    return secrets.compare_digest(expected, challenge)


# ==========================================================================
# RFC 8414 / RFC 9728 / JWKS — metadata discovery (public, no auth)
# ==========================================================================


@router.get("/.well-known/oauth-authorization-server")
async def authorization_server_metadata() -> dict[str, Any]:
    """RFC 8414 authorization server metadata."""
    return {
        "issuer": config.ISSUER,
        "authorization_endpoint": f"{config.ISSUER}/oauth/authorize",
        "token_endpoint": f"{config.ISSUER}/oauth/token",
        "registration_endpoint": f"{config.ISSUER}/oauth/register",
        "jwks_uri": f"{config.ISSUER}/.well-known/jwks.json",
        "scopes_supported": list(scopes.ALL_SCOPES),
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["none", "client_secret_post"],
        "code_challenge_methods_supported": ["S256"],
        "service_documentation": f"{config.ISSUER}/docs",
    }


@router.get("/.well-known/oauth-protected-resource")
async def protected_resource_metadata() -> dict[str, Any]:
    """RFC 9728 protected resource metadata. Tells MCP clients where to find
    the authorization server."""
    return {
        "resource": config.RESOURCE,
        "authorization_servers": [config.ISSUER],
        "bearer_methods_supported": ["header"],
        "scopes_supported": list(scopes.ALL_SCOPES),
        "resource_documentation": f"{config.ISSUER}/docs",
    }


@router.get("/.well-known/jwks.json")
async def jwks() -> dict[str, Any]:
    """Public JWK set so clients / resource servers can verify our JWTs."""
    return {"keys": [tokens.public_jwk()]}


# ==========================================================================
# RFC 7591 — Dynamic Client Registration
# ==========================================================================


class ClientRegistrationRequest(BaseModel):
    client_name: str | None = Field(None)
    redirect_uris: list[str] = Field(default_factory=list)
    grant_types: list[str] | None = Field(None)
    response_types: list[str] | None = Field(None)
    scope: str | None = Field(None)
    token_endpoint_auth_method: str | None = Field(None)


@router.post("/oauth/register")
async def register_client(body: ClientRegistrationRequest) -> JSONResponse:
    """Dynamic Client Registration (RFC 7591). Open endpoint: any caller can
    register a client, but granted scopes are constrained at /authorize.

    Registered clients default to public (no secret), PKCE-required, with
    auth_code + refresh_token grants. Only `memory:read` is auto-granted;
    elevated scopes require the seeded-client path.
    """
    if not body.redirect_uris:
        return _oauth_error("invalid_redirect_uri", "redirect_uris is required")
    requested = scopes.parse(body.scope or scopes.MEMORY_READ)
    allowed = scopes.validate_subset(requested, [scopes.MEMORY_READ])
    if not allowed:
        allowed = [scopes.MEMORY_READ]

    client_id = f"client-{secrets.token_hex(8)}"
    client = oauth_storage.OAuthClient(
        client_id=client_id,
        client_secret=None,
        client_name=body.client_name or "Unnamed Client",
        redirect_uris=body.redirect_uris,
        grant_types=body.grant_types or ["authorization_code", "refresh_token"],
        response_types=body.response_types or ["code"],
        scope=allowed,
        token_endpoint_auth_method=body.token_endpoint_auth_method or "none",
    )
    try:
        oauth_storage.save_client(client)
    except Exception as exc:  # sqlite IntegrityError etc. — let's surface a clean error
        return _oauth_error("server_error", f"client registration failed: {exc}", status=500)

    return JSONResponse(
        status_code=201,
        content={
            "client_id": client.client_id,
            "client_name": client.client_name,
            "redirect_uris": client.redirect_uris,
            "grant_types": client.grant_types,
            "response_types": client.response_types,
            "scope": " ".join(client.scope),
            "token_endpoint_auth_method": client.token_endpoint_auth_method,
        },
    )


# ==========================================================================
# RFC 6749 + RFC 7636 — authorization endpoint
# ==========================================================================


def _render_consent_form(
    *,
    client_name: str,
    client_id: str,
    redirect_uri: str,
    response_type: str,
    scope: str,
    state: str,
    code_challenge: str,
    code_challenge_method: str,
    error: str | None = None,
) -> HTMLResponse:
    """Render the one-page consent form. Minimal HTML, no JS, no CSS frameworks."""
    error_html = (
        f'<p style="color:#b00;">Error: {html.escape(error)}</p>' if error else ""
    )
    # All values go into hidden fields and are echoed back on POST. Escaping
    # is essential — everything that lands here came from a query string.
    fields = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": response_type,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
    }
    hidden_html = "\n".join(
        f'<input type="hidden" name="{html.escape(k)}" value="{html.escape(v)}">'
        for k, v in fields.items()
    )
    body = f"""<!doctype html>
<html><head><title>Galactica — Authorize</title></head>
<body style="font-family:system-ui;max-width:520px;margin:40px auto;padding:20px;">
<h1 style="margin-bottom:0;">Authorize access</h1>
<p style="color:#555;">Application <b>{html.escape(client_name)}</b> is requesting
access to Galactica with scope <code>{html.escape(scope)}</code>.</p>
{error_html}
<form method="post" action="/oauth/authorize">
{hidden_html}
<label>Authorization password:<br>
<input type="password" name="password" autocomplete="off" autofocus
       style="width:100%;padding:8px;margin-top:4px;"></label>
<div style="margin-top:16px;">
<button name="decision" value="allow" type="submit"
        style="padding:8px 16px;">Allow</button>
<button name="decision" value="deny" type="submit" formnovalidate
        style="padding:8px 16px;margin-left:8px;">Deny</button>
</div>
</form>
</body></html>
"""
    return HTMLResponse(content=body)


@router.get("/oauth/authorize", response_model=None)
async def authorize_get(request: Request) -> HTMLResponse | RedirectResponse:
    """Render the consent page. All parameter validation happens here before
    we show anything — the user shouldn't be asked to approve a malformed request."""
    params = dict(request.query_params)
    client_id = params.get("client_id", "")
    redirect_uri = params.get("redirect_uri", "")
    response_type = params.get("response_type", "")
    scope = params.get("scope", scopes.MEMORY_READ)
    state = params.get("state", "")
    code_challenge = params.get("code_challenge", "")
    code_challenge_method = params.get("code_challenge_method", "")

    if not client_id:
        raise HTTPException(status_code=400, detail="client_id required")
    client = oauth_storage.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=400, detail="unknown client_id")
    if not client.allows_redirect_uri(redirect_uri):
        # Per OAuth 2.1 — if redirect_uri is bad, do NOT redirect; show error.
        raise HTTPException(status_code=400, detail="redirect_uri not registered for this client")
    if response_type != "code":
        return _redirect_error(redirect_uri, "unsupported_response_type",
                                "only 'code' is supported", state or None)
    if code_challenge_method != "S256":
        return _redirect_error(redirect_uri, "invalid_request",
                                "code_challenge_method must be S256", state or None)
    if not code_challenge:
        return _redirect_error(redirect_uri, "invalid_request",
                                "code_challenge is required (PKCE)", state or None)

    return _render_consent_form(
        client_name=client.client_name,
        client_id=client_id,
        redirect_uri=redirect_uri,
        response_type=response_type,
        scope=scope,
        state=state,
        code_challenge=code_challenge,
        code_challenge_method=code_challenge_method,
    )


@router.post("/oauth/authorize", response_model=None)
async def authorize_post(
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form(...),
    scope: str = Form(scopes.MEMORY_READ),
    state: str = Form(""),
    code_challenge: str = Form(...),
    code_challenge_method: str = Form(...),
    password: str = Form(""),
    decision: str = Form("deny"),
) -> HTMLResponse | RedirectResponse:
    """Validate consent + password, issue authorization code."""
    client = oauth_storage.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=400, detail="unknown client_id")
    if not client.allows_redirect_uri(redirect_uri):
        raise HTTPException(status_code=400, detail="redirect_uri not registered for this client")

    if decision != "allow":
        return _redirect_error(redirect_uri, "access_denied",
                                "user denied the request", state or None)

    expected = config.AUTHORIZE_PASSWORD
    if not expected or not secrets.compare_digest(password, expected):
        # Re-render the form with an error — never redirect.
        return _render_consent_form(
            client_name=client.client_name,
            client_id=client_id,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            error="incorrect password",
        )

    requested_scopes = scopes.parse(scope)
    granted = scopes.validate_subset(requested_scopes, client.allowed_scope())
    if not granted:
        return _redirect_error(redirect_uri, "invalid_scope",
                                "requested scopes are not allowed for this client",
                                state or None)
    expanded = scopes.expand(granted)

    code = oauth_storage.generate_code()
    oauth_storage.save_authorization_code(
        oauth_storage.AuthorizationCode(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=expanded,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            subject=client_id,
            expires_at=int(time.time()) + config.AUTH_CODE_TTL_SECONDS,
            used=False,
        )
    )

    params = {"code": code}
    if state:
        params["state"] = state
    separator = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(
        url=f"{redirect_uri}{separator}{urllib.parse.urlencode(params)}",
        status_code=302,
    )


# ==========================================================================
# RFC 6749 — token endpoint
# ==========================================================================


@router.post("/oauth/token")
async def token(request: Request) -> JSONResponse:
    """Token endpoint. Supports authorization_code and refresh_token grants.

    Both grants apply scope-filtering against the client's allowed scope set
    so elevated scopes can never be smuggled through.
    """
    form = await request.form()
    grant_type = form.get("grant_type", "")

    if grant_type == "authorization_code":
        return _grant_authorization_code(form)
    if grant_type == "refresh_token":
        return _grant_refresh_token(form)
    return _oauth_error("unsupported_grant_type",
                         f"grant_type '{grant_type}' is not supported")


def _grant_authorization_code(form: Any) -> JSONResponse:
    """Redeem an authorization code for access + refresh tokens."""
    code = form.get("code", "")
    client_id = form.get("client_id", "")
    redirect_uri = form.get("redirect_uri", "")
    code_verifier = form.get("code_verifier", "")

    if not code or not client_id or not code_verifier:
        return _oauth_error("invalid_request",
                             "code, client_id, and code_verifier are required")

    client = oauth_storage.get_client(client_id)
    if client is None:
        return _oauth_error("invalid_client", "unknown client_id", status=401)

    auth_code = oauth_storage.consume_authorization_code(code)
    if auth_code is None:
        return _oauth_error("invalid_grant", "code is unknown, expired, or already used")
    if auth_code.client_id != client_id:
        return _oauth_error("invalid_grant", "code was issued to a different client")
    if auth_code.redirect_uri != redirect_uri:
        return _oauth_error("invalid_grant", "redirect_uri does not match")
    if not _verify_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
        return _oauth_error("invalid_grant", "PKCE verification failed")

    return _mint_token_response(
        client_id=client_id,
        subject=auth_code.subject,
        scope=auth_code.scope,
    )


def _grant_refresh_token(form: Any) -> JSONResponse:
    """Rotate a refresh token, returning new access + refresh."""
    refresh_token_value = form.get("refresh_token", "")
    client_id = form.get("client_id", "")
    requested_scope_str = form.get("scope", "")

    if not refresh_token_value or not client_id:
        return _oauth_error("invalid_request", "refresh_token and client_id are required")

    client = oauth_storage.get_client(client_id)
    if client is None:
        return _oauth_error("invalid_client", "unknown client_id", status=401)

    record = oauth_storage.lookup_refresh_token(refresh_token_value)
    if record is None:
        return _oauth_error("invalid_grant", "refresh token is unknown, revoked, or expired")
    if record["client_id"] != client_id:
        return _oauth_error("invalid_grant", "refresh token was issued to a different client")

    existing_scope = record["scope"]
    if requested_scope_str:
        requested = scopes.parse(requested_scope_str)
        # RFC 6749 §6 — refresh scope MUST NOT exceed the original.
        new_scope = scopes.validate_subset(requested, existing_scope)
        if not new_scope:
            return _oauth_error("invalid_scope",
                                 "requested scope exceeds original grant")
    else:
        new_scope = existing_scope

    oauth_storage.revoke_refresh_token(refresh_token_value)
    return _mint_token_response(
        client_id=client_id,
        subject=record["subject"],
        scope=new_scope,
    )


def _mint_token_response(*, client_id: str, subject: str, scope: list[str]) -> JSONResponse:
    """Sign an access JWT + a refresh JWT, persist the refresh, return RFC 6749 JSON."""
    expanded = scopes.expand(scope)
    access_token, access_claims = tokens.mint_access_token(
        client_id=client_id, subject=subject, scope=expanded
    )
    refresh_token_value, refresh_claims = tokens.mint_refresh_token(
        client_id=client_id, subject=subject, scope=expanded
    )
    oauth_storage.save_refresh_token(
        token=refresh_token_value,
        client_id=client_id,
        subject=subject,
        scope=expanded,
        expires_at=refresh_claims.expires_at,
    )
    return JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": config.ACCESS_TOKEN_TTL_SECONDS,
            "refresh_token": refresh_token_value,
            "scope": " ".join(expanded),
        }
    )
