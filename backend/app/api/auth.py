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

from fastapi import HTTPException, Request, status

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
    expected = _configured_token()
    if not expected:
        return
    if request.url.path in PUBLIC_PATHS:
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
