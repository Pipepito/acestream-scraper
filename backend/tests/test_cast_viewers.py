"""Capability separation and receiver cleanup without network or a physical TV."""
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
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


@pytest.mark.asyncio
@pytest.mark.parametrize('replace', [False, True])
async def test_native_android_media_namespace_requires_receiver_launch(viewers, monkeypatch, replace):
    from pychromecast.config import APP_MEDIA_RECEIVER
    from pychromecast.controllers.media import MediaController
    from app.schemas.cast import CastStart

    # Use the real controller: Android's native TV app supports the namespace
    # but cannot load the URL. LOAD must follow an authorized receiver launch.
    media = MediaController()
    receiver = SimpleNamespace(app_id='AndroidNativeApp')
    actions = []

    def launch(app_id, *, force_launch=False, callback_function=None):
        actions.append(('launch', app_id))
        receiver.app_id = app_id
        callback_function(True, None)

    def send(namespace, data, **kwargs):
        actions.append(('load', receiver.app_id))
        assert receiver.app_id == APP_MEDIA_RECEIVER
        assert data['media']['hlsSegmentFormat'] == 'ts'
        assert data['media']['hlsVideoSegmentFormat'] == 'mpeg2_ts'
        media.status.content_id = data['media']['contentId']
        media.status.player_state = 'PLAYING'
        media.session_active_event.set()
        kwargs['callback_function'](True, {'type': 'MEDIA_STATUS'})

    receiver.launch_app = launch
    media.registered(SimpleNamespace(receiver_controller=receiver,
        app_namespaces=[media.namespace], send_app_message=send))
    client = SimpleNamespace(media_controller=media, status=SimpleNamespace(
        app_id='AndroidNativeApp', volume_level=.5), wait=Mock(), disconnect=Mock())
    monkeypatch.setattr('pychromecast.get_chromecast_from_cast_info', lambda *args, **kwargs: client)
    monkeypatch.setattr('app.services.cast_service.viewer_service', viewers)
    viewers.player.hls_ready = lambda session, **kwargs: True
    service = CastService()
    monkeypatch.setattr(service.discovery, 'get', lambda identity: SimpleNamespace(friendly_name='TV'))
    lease = SimpleNamespace(id='viewer', session_id=viewers.player.session.id, permission='cast_server')
    service.prepare = AsyncMock(return_value=(lease, 'control', 'media'))
    payload = CastStart(content_id='a' * 40, device_id='device', replace=replace)
    policy = AccessPolicy(cast_media_url='http://app.test')
    if not replace:
        with pytest.raises(HTTPException) as error:
            await service.start(payload, {'id': 'owner', 'administrator': True}, policy)
        assert error.value.status_code == 409
        assert actions == []
        service.prepare.assert_not_awaited()
        client.disconnect.assert_called_once()
    else:
        status = await service.start(payload, {'id': 'owner', 'administrator': True}, policy)
        assert status.state == 'PLAYING'
        assert actions == [('launch', APP_MEDIA_RECEIVER), ('load', APP_MEDIA_RECEIVER)]


@pytest.mark.parametrize('segment_seconds, before, ready', [(1, 19, 20), (2, 9, 10), (6, 3, 4), (10, 1, 2)])
def test_cast_waits_for_live_buffer_without_delaying_browser_start(tmp_path, segment_seconds, before, ready):
    from app.services.player_service import PlayerService

    player = PlayerService()
    session = SimpleNamespace(id='session', dir=tmp_path)
    player.sessions[session.id] = session
    service = ViewerService(player)
    browser = SimpleNamespace(session_id=session.id, permission='live')
    casts = [SimpleNamespace(session_id=session.id, permission=p) for p in ('cast', 'cast_server')]
    playlist = tmp_path / 'index.m3u8'
    playlist.write_text('#EXTM3U\nseg00000.ts\nseg00001.ts\n')
    assert service.hls_ready(browser)
    assert not any(service.hls_ready(lease) for lease in casts)
    def manifest(count):
        return '#EXTM3U\n' + ''.join(f'#EXTINF:{segment_seconds},\nseg{i:05d}.ts\n' for i in range(count))
    playlist.write_text(manifest(before))
    assert not any(service.hls_ready(lease) for lease in casts)
    playlist.write_text(manifest(ready))
    assert all(service.hls_ready(lease) for lease in casts)
    argv = player.ffmpeg_argv('http://engine.test/stream', tmp_path)
    assert int(argv[argv.index('-hls_list_size') + 1]) == 30


@pytest.mark.parametrize('duration', ['nan', 'inf', '-20', 'invalid'])
def test_cast_buffer_ignores_invalid_durations_and_unfinished_entries(tmp_path, duration):
    from app.services.player_service import PlayerService

    player = PlayerService()
    session = SimpleNamespace(dir=tmp_path)
    (tmp_path / 'index.m3u8').write_text(
        f'#EXTM3U\n#EXTINF:{duration},\nseg00000.ts\n'
        '#EXTINF:2,\nseg00001.ts\n#EXTINF:30,\n')
    assert player.hls_ready(session)
    assert not player.hls_ready(session, minimum_seconds=20)
