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

from app.repositories.access_repository import AccessRepository
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


def secure_transport(request):
    peer = getattr(request.state, 'peer', ('', 0))[0]
    try:
        local = ipaddress.ip_address(peer).is_loopback
    except ValueError:
        local = False
    if request.url.scheme != 'https' and not (local and request.url.hostname in ('localhost', '127.0.0.1', '::1')):
        raise HTTPException(403, 'Use HTTPS for account access, or open the application through localhost')


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
    return repo.session_user(session) if session else None


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
    if parse_trusted(get_settings().FORWARDED_ALLOW_IPS).contains(peer) and (host == peer or not request.headers.get('x-forwarded-for')):
        return False
    if host == peer and TunerNetworkGate.classify_source(peer, False) in ('docker-gateway', 'loopback'):
        return False
    return any(address in ipaddress.ip_network(value) for value in networks)


def require_server_cast(request):
    require_permission(request, 'cast_server')
    if not getattr(request.state, 'access_user', None):
        raise HTTPException(403, 'Sign in with permission to control server devices')
    policy = request.state.access_policy
    if not policy.remote_casting and not trusted_client(request, policy.home_networks):
        raise HTTPException(403, 'Server devices can only be controlled from an approved home network')


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
