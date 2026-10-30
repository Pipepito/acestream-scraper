"""Capability separation and receiver cleanup without network or a physical TV."""
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4
import pytest
from fastapi import HTTPException
from app.schemas.access import AccessPolicy
from app.schemas.player import PlayerSessionCreate
from app.services.viewer_service import ViewerService
from app.services.cast_service import CastDiscovery, CastService, OwnedCast, receiver_address


class FakePlayer:
    def __init__(self):
        self.session = SimpleNamespace(id=uuid4().hex, state='ready', compatibility=False)
        self.leave = Mock()
        self.touch = Mock()
        self.opened = 0

    async def open_session(self, *args, **kwargs):
        self.opened += 1
        return self.session

    def get(self, identity):
        return self.session if identity == self.session.id else None


@pytest.fixture
def viewers(monkeypatch):
    monkeypatch.setattr('app.repositories.access_repository.AccessRepository.state', lambda self: ('accounts', AccessPolicy(public_features=['live', 'cast'])))
    return ViewerService(FakePlayer())


@pytest.mark.asyncio
async def test_viewer_capabilities_cannot_control_other_viewers(viewers):
    payload = PlayerSessionCreate(content_id='a' * 40)
    first, control, media = await viewers.create(payload, permission='cast')
    second, other_control, _ = await viewers.create(payload)
    assert first.session_id == second.session_id
    for identity, token, is_media in [(first.id, media, False), (first.id, control, True), (second.id, control, False), (first.id, other_control, False)]:
        with pytest.raises(HTTPException) as error:
            await viewers.authorize(identity, token, media=is_media)
        assert error.value.status_code == 404
    assert await viewers.authorize(first.id, media, media=True) is first
    viewers.release(first.id)
    viewers.release(first.id)
    viewers.player.leave.assert_called_once_with(first.session_id)
    assert second.id in viewers.leases


@pytest.mark.asyncio
async def test_revocation_and_idle_expiry_release_once(viewers, monkeypatch):
    lease, control, _ = await viewers.create(PlayerSessionCreate(content_id='a' * 40), permission='cast')
    monkeypatch.setattr('app.repositories.access_repository.AccessRepository.state', lambda self: ('accounts', AccessPolicy(public_features=['live'])))
    with pytest.raises(HTTPException) as error:
        await viewers.authorize(lease.id, control)
    assert error.value.status_code == 403
    await viewers.tick()
    viewers.player.leave.assert_called_once()
    lease, _, _ = await viewers.create(PlayerSessionCreate(content_id='a' * 40))
    lease.last_access = time.monotonic() - 91
    await viewers.tick()
    assert not viewers.leases


@pytest.mark.asyncio
async def test_concurrent_admission_is_bounded(viewers):
    event = asyncio.Event()
    async def pending(*args, **kwargs):
        await event.wait()
        return viewers.player.session
    viewers.player.open_session = pending
    viewers._pending = 255
    task = asyncio.create_task(viewers.create(PlayerSessionCreate(content_id='a' * 40)))
    await asyncio.sleep(0)
    with pytest.raises(HTTPException) as error:
        await viewers.create(PlayerSessionCreate(content_id='b' * 40))
    assert error.value.status_code == 409
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert viewers._pending == 255


def test_discovery_rejects_public_metadata_and_audio_only_targets():
    assert receiver_address('192.168.1.20')
    for address in ['169.254.169.254', '127.0.0.1', '8.8.8.8', 'tv.example', '::1']:
        assert not receiver_address(address)
    discovery = CastDiscovery()
    identity = uuid4()
    info = SimpleNamespace(port=8009, properties={b'id': str(identity).encode(), b'ca': b'1', b'fn': b'Test TV'}, parsed_addresses=lambda: ['192.168.1.20'])
    zc = SimpleNamespace(get_service_info=lambda *args, **kwargs: info)
    discovery.update_service(zc, 'type', 'name')
    assert discovery.list()[0].id == str(identity)
    discovery.remove_service(zc, 'type', 'name')
    info.properties[b'ca'] = b'4'
    discovery.update_service(zc, 'type', 'name')
    assert discovery.list() == []


@pytest.mark.asyncio
@pytest.mark.parametrize('ours', [True, False])
async def test_stop_never_interrupts_unrelated_receiver_media(viewers, monkeypatch, ours):
    monkeypatch.setattr('app.services.cast_service.viewer_service', viewers)
    lease, _, _ = await viewers.create(PlayerSessionCreate(content_id='a' * 40), permission='cast')
    media = SimpleNamespace(status=SimpleNamespace(content_id='owned-url' if ours else 'someone-else'), stop=Mock())
    client = SimpleNamespace(media_controller=media, disconnect=Mock())
    cast = OwnedCast('id', 'device', 'TV', 'owner', lease.id, client, 'owned-url', time.monotonic())
    service = CastService()
    service.active[cast.id] = cast
    await service._stop(cast)
    assert media.stop.call_count == int(ours)
    client.disconnect.assert_called_once()
    viewers.player.leave.assert_called_once()
    assert not service.active


@pytest.mark.asyncio
async def test_unavailable_access_store_releases_viewers(viewers, monkeypatch):
    lease, _, _ = await viewers.create(PlayerSessionCreate(content_id='a' * 40))
    def unavailable(self):
        raise RuntimeError('private storage detail')
    monkeypatch.setattr('app.repositories.access_repository.AccessRepository.state', unavailable)
    await viewers.tick()
    assert lease.id not in viewers.leases
    viewers.player.leave.assert_called_once()
