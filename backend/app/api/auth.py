"""
Optional API token authentication (#148).

When the API_TOKEN environment variable is set, every /api/v1 route (except
/api/v1/health) and the player-facing playlist/EPG routes require the token.
When it is unset or empty the API stays open — the historical
trusted-network default.

Accepted credential carriers, checked in order:
- Authorization: Bearer <token>
- X-Api-Token: <token>
- ?token=<token> query parameter (for IPTV players and XMLTV grabbers,
  which can usually only be configured with a bare URL)

The dependency reads the request directly instead of declaring Header/Query
parameters so the OpenAPI schema (and the generated frontend client) stays
unchanged.
"""

import os
import secrets
from urllib.parse import urlencode

from fastapi import HTTPException, Request, status
from app.utils.request_path import route_path

# Paths that must stay reachable without a token: container/orchestrator
# health probes cannot carry credentials.
PUBLIC_PATHS = {"/api/v1/health"}


def _configured_token() -> str:
    return os.environ.get("API_TOKEN", "").strip()


def _presented_token(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    header_token = request.headers.get("X-Api-Token", "")
    if header_token:
        return header_token.strip()
    return request.query_params.get("token", "")


async def require_api_token(request: Request) -> None:
    """FastAPI dependency enforcing the optional API token."""
    path = route_path(request.scope)
    if getattr(request.state, 'access_checked', False) or path.startswith('/api/v1/auth/'):
        return
    if path.startswith('/api/v1/viewers/'):
        # Every viewer read/release is independently capability-checked.
        return
    expected = _configured_token()
    if not expected:
        return
    if path in PUBLIC_PATHS:
        return
    presented = _presented_token(request)
    # Compare bytes: compare_digest raises TypeError on non-ASCII str input,
    # which would turn a garbage token into a 500 instead of a 401.
    if presented and secrets.compare_digest(
        presented.encode("utf-8"), expected.encode("utf-8")
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def authenticated_player_url(request: Request, url: str) -> str:
    """Carry an already validated credential into a player-followed URL.

    Never disclose the server's configured secret to an unauthenticated caller.
    The destination must be an application URL resolved by the caller.
    """
    if getattr(request.state, 'access_mode', 'open') == 'accounts':
        # Never propagate a cookie or an administrative header credential.
        token = getattr(request.state, 'playback_token', '')
        if token:
            return url + ('&' if '?' in url else '?') + urlencode({'token': token})
        return url
    expected, presented = _configured_token(), _presented_token(request)
    if expected and presented and secrets.compare_digest(expected.encode(), presented.encode()):
        return url + ('&' if '?' in url else '?') + urlencode({'token': presented})
    return url
