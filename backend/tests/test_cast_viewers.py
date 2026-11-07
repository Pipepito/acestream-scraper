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
@pytest.mark.parametrize('anonymous', [False, True])
async def test_native_android_media_namespace_requires_receiver_launch(viewers, monkeypatch, replace, anonymous):
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
    owner = {'id': 'local:browser' if anonymous else 'owner', 'administrator': not anonymous}
    user = None if anonymous else owner
    if not replace:
        with pytest.raises(HTTPException) as error:
            await service.start(payload, user, policy, controller=owner)
        assert error.value.status_code == 409
        assert actions == []
        service.prepare.assert_not_awaited()
        client.disconnect.assert_called_once()
    else:
        status = await service.start(payload, user, policy, controller=owner)
        assert status.state == 'PLAYING'
        assert actions == [('launch', APP_MEDIA_RECEIVER), ('load', APP_MEDIA_RECEIVER)]
        service.prepare.assert_awaited_once_with(payload, user, policy, 'cast_server')


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


@pytest.mark.asyncio
async def test_unicast_discovery_requires_video_identity_and_bounded_response():
    import httpx
    from app.services.cast_scan import device_info
    import json
    identity = uuid4()
    def reply(data):
        return httpx.Response(200, stream=httpx.ByteStream(json.dumps(data).encode()))
    def response(request):
        assert str(request.url).startswith('http://192.168.1.20:8008/setup/eureka_info')
        return reply({'device_info': {'ssdp_udn': str(identity), 'name': 'Living room',
            'model_name': 'TV', 'capabilities': {'display_supported': True}}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as client:
        info = await device_info(client, '192.168.1.20')
        assert info.uuid == identity and info.friendly_name == 'Living room'
        assert await device_info(client, '169.254.169.254') is None
    for data in [{'name': 'HTTP server'}, {'device_info': {'ssdp_udn': str(identity), 'capabilities': {'display_supported': False}}}, {'padding': 'x' * 20000}]:
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: reply(data))) as client:
            assert await device_info(client, '192.168.1.20') is None
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(302, headers={'Location': 'http://169.254.169.254/'})), follow_redirects=False) as client:
        assert await device_info(client, '192.168.1.20') is None


def test_unicast_inventory_expires_but_mdns_inventory_does_not(monkeypatch):
    from pychromecast.models import CastInfo, HostServiceInfo
    discovery = CastDiscovery()
    identity = uuid4()
    info = CastInfo({HostServiceInfo('192.168.1.20', 8009)}, identity, 'TV', 'Living room', '192.168.1.20', 8009, 'cast', 'Google')
    discovery.remember_unicast(info)
    assert len(discovery.list()) == 1
    discovery.devices[str(identity)] = (info, time.monotonic() - 301, None)
    assert discovery.list() == []
    discovery.devices[str(identity)] = (info, time.monotonic() - 301, 'mdns-name')
    assert len(discovery.list()) == 1


@pytest.mark.asyncio
async def test_known_tv_is_revalidated_after_expiry_without_subnet_scan(monkeypatch):
    from app.services.cast_scan import CastScanner
    from pychromecast.models import CastInfo, HostServiceInfo
    from unittest.mock import AsyncMock
    clock = [1000.0]
    monkeypatch.setattr(time, 'monotonic', lambda: clock[0])
    discovery = CastDiscovery()
    identity = uuid4()
    info = CastInfo({HostServiceInfo('192.168.1.20', 8009)}, identity, 'TV', 'Living room', '192.168.1.20', 8009, 'cast', 'Google')
    discovery.remember_unicast(info)
    clock[0] += 301
    assert discovery.list() == []
    probe = AsyncMock(return_value=info)
    monkeypatch.setattr('app.services.cast_scan.device_info', probe)
    scanner = CastScanner()
    await scanner.refresh_known(discovery)
    assert discovery.list()[0].id == str(identity)
    assert probe.call_args.args[1] == '192.168.1.20'
    await scanner.refresh_known(discovery)
    assert probe.await_count == 1
    # A different device at the same address cannot inherit the identity.
    clock[0] += 301
    from dataclasses import replace
    probe.return_value = replace(info, uuid=uuid4())
    await scanner.refresh_known(discovery)
    assert discovery.list() == []
    # Failed checks do not prolong retention indefinitely.
    clock[0] += 86401
    assert discovery.known_unicast() == []


def test_scan_infers_client_lan_without_scanning_container_network(monkeypatch):
    from starlette.requests import Request
    from app.services.cast_scan import scan_networks
    monkeypatch.setattr('app.config.settings.get_settings', lambda: SimpleNamespace(FORWARDED_ALLOW_IPS=''))
    monkeypatch.setattr('ifaddr.get_adapters', lambda: [SimpleNamespace(ips=[SimpleNamespace(ip='172.17.0.2'), SimpleNamespace(ip='127.0.0.1')])])
    def request(host):
        return Request({'type': 'http', 'method': 'GET', 'scheme': 'http', 'path': '/', 'headers': [],
            'client': (host, 1234), 'state': {'peer': (host, 1234)}})
    assert scan_networks(request('192.168.1.30')) == ['192.168.1.0/24']
    assert scan_networks(request('::ffff:192.168.1.30')) == ['192.168.1.0/24']
    assert scan_networks(request('8.8.8.8')) == []


def test_local_browsers_have_separate_non_admin_ownership():
    from app.services.access_service import csrf_token
    from app.services.cast_settings import controller
    from starlette.requests import Request
    def request(token):
        return Request({'type': 'http', 'headers': [(b'cookie', f'scraper_csrf={token}'.encode())]})
    token = csrf_token()
    first = controller(request(token))
    assert first == controller(request(token))
    assert first['id'] != controller(request(csrf_token()))['id']
    assert first['administrator'] is False
    with pytest.raises(HTTPException):
        controller(request('forged-cookie'))


@pytest.mark.asyncio
async def test_another_local_browser_cannot_control_owned_cast():
    from app.schemas.cast import CastCommand
    service = CastService()
    service.active['owned'] = SimpleNamespace(owner_id='local:first')
    with pytest.raises(HTTPException) as error:
        await service.command('owned', CastCommand(action='stop'), {'id': 'local:second', 'administrator': False})
    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_unicast_discovery_supports_legacy_android_tv_identity():
    import httpx
    import json
    from app.services.cast_scan import device_info
    identity = uuid4()
    data = {'name': 'Older Android TV', 'ssdp_udn': str(identity), 'cast_build_revision': '1.56.123456'}
    def reply(request):
        return httpx.Response(200, stream=httpx.ByteStream(json.dumps(data).encode()))
    async with httpx.AsyncClient(transport=httpx.MockTransport(reply)) as client:
        found = await device_info(client, '192.168.1.20')
        assert found.uuid == identity and found.friendly_name == data['name']
        assert found.model_name == 'Google Cast'
        del data['cast_build_revision']
        assert await device_info(client, '192.168.1.20') is None


@pytest.mark.asyncio
async def test_malformed_nested_discovery_data_does_not_abort_other_receivers():
    import httpx
    from app.services.cast_scan import device_info
    body = b'[' * 2000 + b'0' + b']' * 2000
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=httpx.ByteStream(body)))) as client:
        assert await device_info(client, '192.168.1.20') is None


@pytest.mark.asyncio
async def test_cancelled_scan_waits_for_all_probe_cleanup(monkeypatch):
    from app.services.cast_scan import CastScanner
    entered = asyncio.Event()
    active = set()
    async def pending(client, host):
        active.add(host)
        entered.set()
        try:
            await asyncio.sleep(60)
        finally:
            active.remove(host)
    monkeypatch.setattr('app.services.cast_scan.scan_networks', lambda request: ['192.168.1.0/30'])
    monkeypatch.setattr('app.services.cast_scan.device_info', pending)
    discovery = SimpleNamespace(start=Mock(), list=Mock(return_value=[]))
    task = asyncio.create_task(CastScanner().discover(None, discovery))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert active == set()
