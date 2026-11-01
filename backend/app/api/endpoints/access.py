"""Thin account endpoints with bounded credential parsing and redacted errors."""
import asyncio
import os
import secrets
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from app.repositories.access_repository import AccessRepository, digest
from app.schemas.access import (AccessStatus, AccountView, AccountCreate, AccountUpdate, Bootstrap,
    Credentials, PasswordChange, AccessPolicy, CredentialCreate, CredentialView, CredentialIssued, SessionView, DisableAccess)
from app.services.access_service import (COOKIE, CSRF_COOKIE, csrf_token, require_csrf, secure_transport,
    hash_password, verify_password, require_admin, permissions, limit_login, header_token, legacy_matches, trusted_client, valid_csrf, account_transport)


class AccessRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        async def guarded(request):
            try:
                async with asyncio.timeout(10):
                    body = bytearray()
                    async for chunk in request.stream():
                        body.extend(chunk)
                        if len(body) > 16384:
                            raise HTTPException(413, 'Account request is too large')
                    request._body = bytes(body)
                return await handler(request)
            except RequestValidationError:
                raise HTTPException(422, 'Invalid account fields. Check the required values and limits.') from None
            except TimeoutError:
                raise HTTPException(408, 'Account request timed out') from None
            except LookupError:
                raise HTTPException(404, 'Account resource not found') from None
            except ValueError as error:
                raise HTTPException(409, str(error)) from None
        return guarded


router = APIRouter(route_class=AccessRoute, tags=['access'])


def session_response(repo, user_id, response, request):
    token = secrets.token_urlsafe(32)
    repo.create_session(user_id, token)
    response.set_cookie(COOKIE, token, httponly=True, secure=request.url.scheme == 'https', samesite='strict', max_age=604800)


@router.get('/status', response_model=AccessStatus)
def access_status(request: Request, response: Response):
    repo = AccessRepository()
    mode, policy = repo.state()
    existing = request.cookies.get(CSRF_COOKIE, '')
    csrf = existing if valid_csrf(existing) else csrf_token()
    response.set_cookie(CSRF_COOKIE, csrf, httponly=True, secure=request.url.scheme == 'https', samesite='strict')
    effective = permissions(request)
    if policy.public_playlists or (policy.local_iptv and trusted_client(request, policy.local_networks)):
        effective.add('playlists')
    return AccessStatus(mode=mode, user=getattr(request.state, 'access_user', None),
                        permissions=sorted(effective), csrf=csrf, legacy_token=bool(os.environ.get('API_TOKEN')),
                        account_transport=account_transport(request))


@router.post('/bootstrap', response_model=AccountView | None)
def bootstrap(data: Bootstrap, request: Request, response: Response):
    require_csrf(request)
    limit_login(request)
    repo = AccessRepository()
    if not repo.path.exists():
        repo.initialize()
    if os.environ.get('API_TOKEN') and not legacy_matches(header_token(request)):
        raise HTTPException(401, 'Enter the existing API token before changing access')
    if data.enabled:
        secure_transport(request)
        if os.environ.get('API_TOKEN') and not data.migrate_legacy_token:
            raise HTTPException(409, 'Confirm migration: the old API token will grant playback only. Create replacement administrative credentials after signing in.')
        if data.password != data.password_confirmation:
            raise HTTPException(422, 'The passwords do not match')
        password_hash = hash_password(data.password.get_secret_value())
    else:
        password_hash = ''
    user_id = repo.bootstrap(data.username, password_hash, data.enabled)
    if user_id:
        session_response(repo, user_id, response, request)
        return repo.user_view(repo.user(user_id=user_id))
    return None


@router.post('/login', response_model=AccountView)
def login(data: Credentials, request: Request, response: Response):
    require_csrf(request)
    secure_transport(request)
    limit_login(request)
    repo = AccessRepository()
    if repo.state()[0] != 'accounts':
        raise HTTPException(409, 'User management is not enabled')
    row = repo.user(username=data.username)
    if not verify_password(row['password_hash'] if row else None, data.password.get_secret_value()) or not row or not row['enabled']:
        raise HTTPException(401, 'Invalid username or password')
    previous = request.cookies.get(COOKIE)
    if previous:
        repo.revoke_session(digest(previous))
    session_response(repo, row['id'], response, request)
    return repo.user_view(row)


@router.post('/logout', status_code=204)
def logout(request: Request, response: Response):
    require_csrf(request)
    AccessRepository().revoke_session(digest(request.cookies.get(COOKIE, '')))
    response.delete_cookie(COOKIE)


@router.put('/password', status_code=204)
def change_password(data: PasswordChange, request: Request, response: Response):
    user = getattr(request.state, 'access_user', None)
    if not user:
        raise HTTPException(401, 'Sign in to change your password')
    secure_transport(request)
    limit_login(request)
    repo = AccessRepository()
    row = repo.user(user_id=user['id'])
    if not verify_password(row['password_hash'], data.current_password.get_secret_value()):
        raise HTTPException(403, 'Current password is incorrect')
    if data.password != data.password_confirmation:
        raise HTTPException(422, 'The passwords do not match')
    repo.set_password(user['id'], hash_password(data.password.get_secret_value()))
    response.delete_cookie(COOKIE)


@router.get('/users', response_model=list[AccountView])
def users(request: Request):
    require_admin(request)
    return AccessRepository().users()


@router.post('/users', response_model=AccountView, status_code=201)
def create_user(data: AccountCreate, request: Request):
    require_admin(request)
    secure_transport(request)
    return AccessRepository().create_user(data.username, hash_password(data.password.get_secret_value()), data.administrator, data.permissions)


@router.put('/users/{user_id}', response_model=AccountView)
def update_user(user_id: str, data: AccountUpdate, request: Request):
    require_admin(request)
    return AccessRepository().update_user(user_id, data)


@router.get('/policy', response_model=AccessPolicy)
def policy(request: Request):
    require_admin(request)
    return AccessRepository().state()[1]


@router.put('/policy', response_model=AccessPolicy)
def update_policy(data: AccessPolicy, request: Request):
    require_admin(request)
    return AccessRepository().update_policy(data.model_dump(exclude_unset=True))


@router.post('/disable', status_code=204)
def disable(data: DisableAccess, request: Request, response: Response):
    user = require_admin(request)
    secure_transport(request)
    limit_login(request)
    repo = AccessRepository()
    if not verify_password(repo.user(user_id=user['id'])['password_hash'], data.current_password.get_secret_value()):
        raise HTTPException(403, 'Current password is incorrect')
    repo.disable()
    response.delete_cookie(COOKIE)


@router.get('/sessions', response_model=list[SessionView])
def sessions(request: Request):
    require_admin(request)
    return AccessRepository().sessions()


@router.delete('/sessions/{session_id}', status_code=204)
def revoke_session(session_id: str, request: Request):
    require_admin(request)
    AccessRepository().revoke_session(session_id)


@router.get('/credentials', response_model=list[CredentialView])
def credentials(request: Request):
    require_admin(request)
    return AccessRepository().credentials()


@router.post('/credentials', response_model=CredentialIssued, status_code=201)
def issue_credential(data: CredentialCreate, request: Request):
    user = require_admin(request)
    secure_transport(request)
    return AccessRepository().issue_credential(user['id'], data.label, data.kind, secrets.token_urlsafe(32))


@router.delete('/credentials/{credential_id}', status_code=204)
def revoke_credential(credential_id: str, request: Request):
    require_admin(request)
    AccessRepository().revoke_credential(credential_id)
