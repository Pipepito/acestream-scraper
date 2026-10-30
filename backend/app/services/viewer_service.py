"""Independent viewer leases over shared player sessions; tokens never authorize peers."""
import asyncio
import logging
from dataclasses import dataclass
import secrets
import time
from uuid import uuid4
from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.repositories.access_repository import AccessRepository, digest
from app.services.player_service import player_service, PlayerLimitReached


@dataclass
class ViewerLease:
    id: str
    session_id: str
    control_hash: str
    media_hash: str
    owner_id: str | None
    owner_password: str | None
    permission: str
    last_access: float
    detached: bool = False
    last_media: float = 0


class ViewerService:
    def __init__(self, player=None):
        self.player = player or player_service
        self.leases: dict[str, ViewerLease] = {}
        self._pending = 0

    async def create(self, payload, user=None, *, detached=False, permission='live', compatibility=False):
        if len(self.leases) + self._pending >= 256:
            raise HTTPException(409, 'Too many active viewers')
        self._pending += 1
        try:
            password = None
            if user:
                row = await run_in_threadpool(AccessRepository().user, user_id=user['id'])
                if not row or not row['enabled']:
                    raise HTTPException(403, 'Playback permission was revoked')
                password = digest(row['password_hash'])
            session = await self.player.open_session(payload.content_id.lower(), audio_index=payload.audio_index,
                subtitle_index=payload.subtitle_index, compatibility=compatibility)
        except PlayerLimitReached:
            raise HTTPException(409, 'Player capacity reached; stop another stream before trying again') from None
        finally:
            self._pending -= 1
        control, media = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        lease = ViewerLease(uuid4().hex, session.id, digest(control), digest(media), user['id'] if user else None,
                            password, permission, time.monotonic(), detached)
        lease.last_media = time.monotonic()
        self.leases[lease.id] = lease
        return lease, control, media

    async def valid_owner(self, lease):
        try:
            return await self._valid_owner(lease)
        except Exception:
            logging.getLogger(__name__).warning('Access storage could not verify a viewer; releasing playback')
            return False

    async def _valid_owner(self, lease):
        repo = AccessRepository()
        mode, policy = await run_in_threadpool(repo.state)
        if lease.owner_id:
            row = await run_in_threadpool(repo.user, user_id=lease.owner_id)
            if not row or not row['enabled'] or digest(row['password_hash']) != lease.owner_password:
                return False
            view = repo.user_view(row)
            needed = {lease.permission, 'live'}
            return view['administrator'] or needed.issubset(view['permissions'])
        return mode == 'open' or (mode == 'accounts' and {lease.permission, 'live'}.issubset(policy.public_features))

    async def authorize(self, viewer_id, token, *, media=False):
        lease = self.leases.get(viewer_id)
        if not lease or not token or not secrets.compare_digest(digest(token), lease.media_hash if media else lease.control_hash):
            raise HTTPException(404, 'Viewer not found or permission expired')
        if not await self.valid_owner(lease):
            self.release(viewer_id)
            raise HTTPException(403, 'Playback permission was revoked')
        if not self.player.get(lease.session_id):
            self.release(viewer_id)
            raise HTTPException(410, 'Playback ended')
        lease.last_access = time.monotonic()
        if media:
            lease.last_media = lease.last_access
        self.player.touch(lease.session_id)
        return lease

    def release(self, viewer_id):
        lease = self.leases.pop(viewer_id, None)
        if lease:
            self.player.leave(lease.session_id)

    async def tick(self):
        for lease in list(self.leases.values()):
            if time.monotonic() - lease.last_access > 90 or not await self.valid_owner(lease):
                self.release(lease.id)

    def close(self):
        for viewer_id in list(self.leases):
            self.release(viewer_id)


viewer_service = ViewerService()
