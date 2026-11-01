"""Account verification, request identity and narrowly scoped authorization."""
from collections import OrderedDict, deque
import hashlib
import hmac
import ipaddress
import os
import secrets
import threading
import time
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import HTTPException, Request

from app.schemas.access import PERMISSIONS

COOKIE = 'scraper_session'
CSRF_COOKIE = 'scraper_csrf'
_CSRF_KEY = secrets.token_bytes(32)
_HASHER = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
_HASH_SLOTS = threading.BoundedSemaphore(2)
_ATTEMPTS: OrderedDict[str, deque] = OrderedDict()
_ATTEMPTS_LOCK = threading.Lock()


def hash_password(password):
    if len(password) < 12 or len(password) > 128:
        raise HTTPException(422, 'Use a password between 12 and 128 characters')
    if not _HASH_SLOTS.acquire(blocking=False):
        raise HTTPException(429, 'Account verification is busy; try again shortly', headers={'Retry-After': '2'})
    try:
        return _HASHER.hash(password)
    finally:
        _HASH_SLOTS.release()


def verify_password(encoded, password):
    if not _HASH_SLOTS.acquire(blocking=False):
        raise HTTPException(429, 'Account verification is busy; try again shortly', headers={'Retry-After': '2'})
    try:
        try:
            # A missing account performs the same expensive operation.
            if not encoded:
                _HASHER.hash(password)
                return False
            return _HASHER.verify(encoded, password)
        except (VerificationError, InvalidHashError):
            return False
    finally:
        _HASH_SLOTS.release()


def limit_login(request):
    key = request.client.host if request.client else 'unknown'
    now = time.monotonic()
    with _ATTEMPTS_LOCK:
        events = _ATTEMPTS.setdefault(key, deque(maxlen=10))
        while events and now - events[0] >= 60:
            events.popleft()
        if len(events) >= 10:
            raise HTTPException(429, 'Too many attempts; try again in a minute', headers={'Retry-After': '60'})
        events.append(now)
        _ATTEMPTS.move_to_end(key)
        while len(_ATTEMPTS) > 2048:
            _ATTEMPTS.popitem(last=False)


def csrf_token():
    value = secrets.token_hex(24)
    return value + '.' + hmac.new(_CSRF_KEY, value.encode(), hashlib.sha256).hexdigest()


def valid_csrf(value):
    parts = value.split('.')
    return len(parts) == 2 and hmac.compare_digest(parts[1].encode(), hmac.new(_CSRF_KEY, parts[0].encode(), hashlib.sha256).hexdigest().encode())


def same_origin(request):
    origin = request.headers.get('origin')
    if not origin:
        return True
    try:
        candidate = urlsplit(origin)
        expected = request.url
        def port(url):
            return url.port or (443 if url.scheme == 'https' else 80)
        return bool(candidate.scheme in ('http', 'https') and not candidate.username and not candidate.password
                    and not candidate.path and not candidate.query and not candidate.fragment
                    and (candidate.scheme, candidate.hostname, port(candidate)) == (expected.scheme, expected.hostname, port(expected)))
    except ValueError:
        return False


def require_csrf(request: Request):
    if not same_origin(request) or request.headers.get('sec-fetch-site') == 'cross-site':
        raise HTTPException(403, 'Open this form from the application itself')
    value = request.headers.get('x-csrf-token', '')
    cookie = request.cookies.get(CSRF_COOKIE, '')
    if not valid_csrf(value) or not hmac.compare_digest(value.encode(), cookie.encode()):
        raise HTTPException(403, 'Reload the page before submitting this form')


def account_transport(request):
    """Allow accounts at private LAN URLs, including Docker NAT connections."""
    if request.url.scheme == 'https':
        return 'https'
    peer = getattr(request.state, 'peer', ('', 0))[0]
    try:
        address = ipaddress.ip_address(peer)
        address = getattr(address, 'ipv4_mapped', None) or address
        local = address.is_loopback
    except ValueError:
        local = False
    if request.url.scheme == 'http':
        if private_lan_address(request) is not None:
            return 'local_http'
        if local and request.url.hostname in ('localhost', '127.0.0.1', '::1') and not any(
                name in request.headers for name in ('forwarded', 'x-forwarded-for', 'x-real-ip', 'x-forwarded-host')):
            return 'local_http'
        try:
            destination = ipaddress.ip_address(request.url.hostname or '')
            destination = getattr(destination, 'ipv4_mapped', None) or destination
        except ValueError:
            destination = None
        # A public address trusted for casting never grants plaintext account access.
        if destination and any(destination in ipaddress.ip_network(value) for value in DEFAULT_HOME_NETWORKS) and trusted_client(request, DEFAULT_HOME_NETWORKS):
            return 'local_http'
    return 'blocked'


def secure_transport(request):
    if account_transport(request) == 'blocked':
        raise HTTPException(403, 'Use HTTPS, or open the server’s private IP address on your home network.')


def header_token(request):
    bearer = request.headers.get('authorization', '')
    return bearer[7:].strip() if bearer.lower().startswith('bearer ') else request.headers.get('x-api-token', '').strip()


def legacy_matches(token):
    expected = os.environ.get('API_TOKEN', '').strip()
    return bool(expected and token and hmac.compare_digest(expected.encode(), token.encode()))


def request_user(request, repo):
    token = header_token(request)
    if token:
        user = repo.credential_user(token, 'admin')
        if user and user['administrator']:
            request.state.header_authenticated = True
            return user
    session = request.cookies.get(COOKIE, '')
    user = repo.session_user(session) if session else None
    if user:
        secure_transport(request)
    return user


def permissions(request):
    user = getattr(request.state, 'access_user', None)
    if user:
        return set(PERMISSIONS if user['administrator'] else user['permissions'])
    return set(getattr(request.state, 'access_policy', None).public_features if getattr(request.state, 'access_policy', None) else [])


def require_admin(request):
    user = getattr(request.state, 'access_user', None)
    if not user or not user['administrator']:
        raise HTTPException(403, 'Administrator access required')
    return user


def require_permission(request, permission):
    if getattr(request.state, 'access_mode', 'open') == 'open' and permission != 'cast_server':
        return
    if permission not in permissions(request):
        raise HTTPException(403, 'This account does not have permission for that action')


def trusted_client(request, networks):
    """Never infer home membership from a private proxy or container gateway."""
    from app.middleware.forwarded import parse_trusted
    from app.config.settings import get_settings
    from app.services.tuner_network import TunerNetworkGate
    peer = getattr(request.state, 'peer', (None, 0))[0]
    host = request.client.host if request.client else None
    try:
        address = ipaddress.ip_address(host or '')
        address = getattr(address, 'ipv4_mapped', None) or address
    except ValueError:
        return False
    # A configured proxy without a resolved forwarding chain is ambiguous.
    proxy = parse_trusted(get_settings().FORWARDED_ALLOW_IPS).contains(peer)
    if not proxy and any(name in request.headers for name in ('forwarded', 'x-forwarded-for', 'x-real-ip')):
        return False
    if proxy and (host == peer or not request.headers.get('x-forwarded-for')):
        return False
    if host == peer and TunerNetworkGate.classify_source(peer, False) in ('docker-gateway', 'loopback'):
        return False
    return any(address in ipaddress.ip_network(value) for value in networks)


DEFAULT_HOME_NETWORKS = ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7')



def private_lan_address(request):
    """A private URL reached over a private connection is a local deployment.

    Docker may replace the source with its private gateway. No browser pairing
    is required. Public destinations and public forwarded clients stay separate;
    this exception does not change IPTV or reverse-proxy trust.
    """
    if request.url.scheme not in ('http', 'https') or not request.client:
        return None
    try:
        destination = ipaddress.ip_address(request.url.hostname or '')
        client = ipaddress.ip_address(request.client.host)
        destination = getattr(destination, 'ipv4_mapped', None) or destination
        client = getattr(client, 'ipv4_mapped', None) or client
    except ValueError:
        return None
    networks = tuple(ipaddress.ip_network(value) for value in DEFAULT_HOME_NETWORKS)
    if not all(any(address in network for network in networks) for address in (destination, client)):
        return None
    if any(name in request.headers for name in ('forwarded', 'x-forwarded-for', 'x-real-ip', 'x-forwarded-host')) and not trusted_client(request, DEFAULT_HOME_NETWORKS):
        return None
    return destination


def home_client(request):
    return private_lan_address(request) is not None or trusted_client(request, request.state.access_policy.home_networks or DEFAULT_HOME_NETWORKS)


def require_server_cast(request):
    user = getattr(request.state, 'access_user', None)
    if getattr(request.state, 'access_mode', 'open') != 'open':
        require_permission(request, 'cast_server')
        if not user:
            raise HTTPException(403, 'Sign in with permission to control server devices')
    policy = request.state.access_policy
    # Remote control always requires an account, including after accounts are disabled.
    if not (policy.remote_casting and user) and not home_client(request):
        from app.config.settings import get_settings
        from app.middleware.forwarded import parse_trusted
        peer = getattr(request.state, 'peer', (None, 0))[0]
        if parse_trusted(get_settings().FORWARDED_ALLOW_IPS).contains(peer) and request.client and request.client.host == peer:
            raise HTTPException(403, 'The client address is hidden or listed as a trusted proxy. In Settings → Network, trust only your actual reverse proxy; without a proxy use 127.0.0.1. Save and restart the container.')
        raise HTTPException(403, 'This connection is not recognized as home. Open TV casting to check the connection or trust your home connection as an administrator.')
    if not same_origin(request):
        raise HTTPException(403, 'Open casting from the application itself')
    if request.method not in ('GET', 'HEAD') and not getattr(request.state, 'header_authenticated', False):
        require_csrf(request)


def playback_allowed(request, repo):
    policy = request.state.access_policy
    user = getattr(request.state, 'access_user', None)
    token = request.query_params.get('token', '') or header_token(request)
    if token and (legacy_matches(token) or repo.credential_user(token, 'playback')):
        token_user = repo.credential_user(token, 'playback')
        if token_user and not (token_user['administrator'] or 'playlists' in token_user['permissions']):
            return False
        request.state.playback_token = token
        return True
    return bool((user and (user['administrator'] or 'playlists' in user['permissions'])) or policy.public_playlists
                or (policy.local_iptv and trusted_client(request, policy.local_networks)))
