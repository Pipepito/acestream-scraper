"""Casting configuration is independent of whether accounts are enabled."""
import ipaddress

from fastapi import HTTPException
from app.repositories.access_repository import AccessRepository, digest
from app.schemas.access import CastSettings
from app.services.access_service import (
    CSRF_COOKIE, DEFAULT_HOME_NETWORKS, home_client, require_admin, require_csrf,
    trusted_client, valid_csrf,
)
from app.services.public_url_service import host_warnings, request_origin


def require_cast_settings(request):
    if request.state.access_mode == 'open':
        if not home_client(request):
            raise HTTPException(403, 'Open TV casting from your home network to change its settings.')
        # Even an open installation must reject cross-site configuration writes.
        if request.method not in ('GET', 'HEAD'):
            require_csrf(request)
    else:
        require_admin(request)


def cast_settings(policy):
    return CastSettings.model_validate(policy.model_dump(include=set(CastSettings.model_fields)))


def controller(request):
    """Local browsers own their sessions without creating an account or admin role."""
    user = getattr(request.state, 'access_user', None)
    if user:
        return user
    token = request.cookies.get(CSRF_COOKIE, '')
    if not valid_csrf(token):
        raise HTTPException(403, 'Reload the application before controlling a TV.')
    return {'id': 'local:' + digest(token), 'administrator': False}


def media_base(request):
    # The browser's working address includes the published Docker port and the
    # trusted proxy scheme. An advanced override handles receiver-only routing.
    policy = request.state.access_policy
    if policy.cast_media_url:
        return policy.cast_media_url
    value = request_origin(request) + request.scope.get('root_path', '').rstrip('/')
    return '' if host_warnings(value) else value


def trust_home_connection(request):
    require_admin(request)
    host = request.client.host if request.client else ''
    try:
        address = ipaddress.ip_address(host)
        address = getattr(address, 'ipv4_mapped', None) or address
        network = str(ipaddress.ip_network(address))
    except ValueError:
        raise HTTPException(409, 'The proxy did not provide a usable client address.') from None
    if not (address.is_global or any(address in ipaddress.ip_network(n) for n in DEFAULT_HOME_NETWORKS)) or not trusted_client(request, [network]):
        raise HTTPException(409, 'The client address is hidden by a proxy or Docker gateway. Configure trusted forwarding before trusting this connection.')
    repo = AccessRepository()
    networks = list(request.state.access_policy.home_networks or DEFAULT_HOME_NETWORKS)
    if network not in networks and not home_client(request):
        if len(networks) >= 16:
            raise HTTPException(409, 'Remove an old home network before adding another.')
        networks.append(network)
    return cast_settings(repo.update_policy({'home_networks': networks}))
