"""Server Cast ownership; discovery itself sends no HTTP requests to advertisements."""
import asyncio
from contextlib import suppress
from dataclasses import dataclass
import ipaddress
import threading
import time
from uuid import UUID, uuid4

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from app.schemas.cast import CastDevice, CastStatus
from app.services.viewer_service import viewer_service
from app.services.watch_service import imported_stream

_LAN = tuple(ipaddress.ip_network(n) for n in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16', 'fc00::/7'))


def receiver_address(host):
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(address in network for network in _LAN)


class CastDiscovery:
    def __init__(self):
        self.zc = None
        self.browser = None
        self.devices = {}
        self.lock = threading.RLock()

    def start(self):
        from zeroconf import Zeroconf, ServiceBrowser
        with self.lock:
            if self.browser is None:
                self.zc = Zeroconf()
                self.browser = ServiceBrowser(self.zc, '_googlecast._tcp.local.', self)

    def add_service(self, zc, service_type, name):
        self.update_service(zc, service_type, name)

    def update_service(self, zc, service_type, name):
        from pychromecast.models import CastInfo, HostServiceInfo
        info = zc.get_service_info(service_type, name, timeout=1000)
        if info is None or info.port != 8009:
            return
        properties = {k.decode('utf-8', 'replace'): v.decode('utf-8', 'replace') for k, v in info.properties.items() if k and v}
        try:
            identity = UUID(properties.get('id', ''))
            # Google Cast capability bit 1 means video output.
            if not int(properties.get('ca', '0')) & 1:
                return
        except (ValueError, TypeError):
            return
        addresses = info.parsed_addresses()
        host = next((host for host in addresses if receiver_address(host)), None)
        if not host:
            return
        cast_info = CastInfo({HostServiceInfo(host, 8009)}, identity, properties.get('md', '')[:100],
                             properties.get('fn', 'TV')[:100], host, 8009, 'cast', 'Google')
        with self.lock:
            if len(self.devices) < 128 or str(identity) in self.devices:
                self.devices[str(identity)] = (cast_info, time.monotonic(), name)

    def remove_service(self, zc, service_type, name):
        with self.lock:
            for key, value in list(self.devices.items()):
                if value[2] == name:
                    del self.devices[key]

    def list(self):
        with self.lock:
            # Zeroconf owns TTL expiry and calls remove_service. Unchanged
            # announcements need not trigger update_service every five minutes.
            return [CastDevice(id=key, name=value[0].friendly_name or 'TV', model=value[0].model_name or '') for key, value in self.devices.items()]

    def get(self, identity):
        self.list()
        with self.lock:
            value = self.devices.get(identity)
        if not value or not receiver_address(value[0].host):
            raise HTTPException(404, 'TV is no longer discoverable; refresh the device list')
        return value[0]

    def close(self):
        # Do not hold our listener lock while Zeroconf joins its callbacks.
        if self.browser:
            self.browser.cancel()
        if self.zc:
            self.zc.close()
        self.browser = self.zc = None
        self.devices.clear()


@dataclass
class OwnedCast:
    id: str
    device_id: str
    device_name: str
    owner_id: str
    viewer_id: str
    client: object
    media_url: str
    last_playing: float


async def settled_thread(call, *args, **kwargs):
    """Collect late library replies before releasing ownership on cancellation."""
    task = asyncio.create_task(run_in_threadpool(call, *args, **kwargs))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        with suppress(Exception):
            await task
        raise


class CastService:
    def __init__(self):
        self.discovery = CastDiscovery()
        self.active: dict[str, OwnedCast] = {}
        self.lock = asyncio.Lock()

    async def devices(self):
        await run_in_threadpool(self.discovery.start)
        return self.discovery.list()

    async def prepare(self, payload, user, policy, permission):
        if not await run_in_threadpool(imported_stream, payload.content_id):
            raise HTTPException(404, 'Channel is not available')
        if payload.compatibility and not policy.compatibility_conversion:
            raise HTTPException(403, 'Compatibility conversion is disabled in Settings')
        if payload.compatibility:
            from app.services.recording_coordinator import recording_coordinator
            if recording_coordinator.activity():
                raise HTTPException(409, 'Recording takes priority; try original video or wait for capture to finish')
        return await viewer_service.create(payload, user, detached=True, permission=permission, compatibility=payload.compatibility)

    async def start(self, payload, user, policy):
        import pychromecast
        if not policy.cast_media_url:
            raise HTTPException(409, 'Set the receiver-accessible application URL in Settings → Access')
        async with self.lock:
            info = self.discovery.get(payload.device_id)
            previous = next((cast for cast in self.active.values() if cast.device_id == payload.device_id), None)
            if previous and previous.owner_id != user['id'] and not user['administrator']:
                raise HTTPException(403, 'This TV is controlled by another account')
            if previous and not payload.replace:
                raise HTTPException(409, 'Confirm replacement of the current TV playback')
            if previous:
                await self._stop(previous)
            if len(self.active) >= 16:
                raise HTTPException(409, 'Cast receiver limit reached')
            client = pychromecast.get_chromecast_from_cast_info(info, None, tries=1, retry_wait=1, timeout=5)
            lease = None
            cast = None
            try:
                await settled_thread(client.wait, timeout=5)
                if client.status and client.status.app_id not in (None, '', 'E8C28D3C') and not payload.replace:
                    raise HTTPException(409, 'The TV is already in use. Confirm replacement to cast this stream.')
                lease, _, media = await self.prepare(payload, user, policy, 'cast_server')
                deadline = time.monotonic() + 60
                while time.monotonic() < deadline:
                    session = viewer_service.player.get(lease.session_id)
                    if not session or session.state in ('error', 'stopped'):
                        raise HTTPException(409, 'The stream could not start')
                    if viewer_service.player.hls_ready(session):
                        break
                    lease.last_access = time.monotonic()
                    viewer_service.player.touch(lease.session_id)
                    await asyncio.sleep(.25)
                else:
                    raise HTTPException(504, 'Stream preparation timed out')
                url = f'{policy.cast_media_url}/api/v1/viewers/{lease.id}/media/index.m3u8?cap={media}'
                cast = OwnedCast(uuid4().hex, payload.device_id, info.friendly_name or 'TV', user['id'], lease.id, client, url, time.monotonic())
                await settled_thread(client.media_controller.play_media, url, 'application/vnd.apple.mpegurl', stream_type='LIVE')
                await settled_thread(client.media_controller.block_until_active, timeout=10)
                loaded_deadline = time.monotonic() + 5
                while not self.owns_media(cast) and time.monotonic() < loaded_deadline:
                    await asyncio.sleep(.1)
                if not self.owns_media(cast):
                    raise HTTPException(502, 'The TV did not load this stream')
                self.active[cast.id] = cast
                return self.status(cast)
            except BaseException:
                if cast and self.owns_media(cast):
                    with suppress(Exception):
                        await settled_thread(client.media_controller.stop, timeout=5)
                if lease:
                    viewer_service.release(lease.id)
                with suppress(Exception):
                    await settled_thread(client.disconnect, timeout=5)
                raise

    @staticmethod
    def owns_media(cast):
        return cast.client.media_controller.status.content_id == cast.media_url

    def status(self, cast):
        return CastStatus(id=cast.id, device_id=cast.device_id, device_name=cast.device_name,
            state=cast.client.media_controller.status.player_state or 'CONNECTING', viewer_id=cast.viewer_id,
            volume=cast.client.status.volume_level if cast.client.status else None)

    async def _stop(self, cast):
        self.active.pop(cast.id, None)
        try:
            if self.owns_media(cast):
                await settled_thread(cast.client.media_controller.stop, timeout=5)
        finally:
            viewer_service.release(cast.viewer_id)
            with suppress(Exception):
                await settled_thread(cast.client.disconnect, timeout=5)

    async def command(self, cast_id, command, user):
        async with self.lock:
            cast = self.active.get(cast_id)
            if not cast or (cast.owner_id != user['id'] and not user['administrator']):
                raise HTTPException(404, 'Cast session not found')
            if not self.owns_media(cast):
                await self._stop(cast)
                raise HTTPException(409, 'The receiver is now playing something else')
            if command.action == 'stop':
                await self._stop(cast)
                return
            if command.action == 'volume':
                if command.volume is None:
                    raise HTTPException(422, 'Supply a volume between 0 and 1')
                await settled_thread(cast.client.set_volume, command.volume)
            else:
                await settled_thread(getattr(cast.client.media_controller, command.action), timeout=5)

    async def tick(self):
        if self.lock.locked():
            return
        async with self.lock:
            for cast in list(self.active.values()):
                lease = viewer_service.leases.get(cast.viewer_id)
                state = cast.client.media_controller.status.player_state
                no_media = bool(lease and state != 'PAUSED' and time.monotonic() - (lease.last_media or cast.last_playing) > 90)
                disconnected = not cast.client.socket_client.is_connected or cast.client.socket_client.is_stopped
                session = viewer_service.player.get(lease.session_id) if lease else None
                if session and session.compatibility:
                    from app.services.recording_coordinator import recording_coordinator
                    if recording_coordinator.activity():
                        await self._stop(cast)
                        continue
                if state == 'PLAYING':
                    cast.last_playing = time.monotonic()
                if not lease or not session or session.state in ('error', 'stopped') or disconnected or no_media or not self.owns_media(cast) or not await viewer_service.valid_owner(lease) or state == 'IDLE' or time.monotonic() - cast.last_playing > 600:
                    with suppress(Exception):
                        await self._stop(cast)
                elif state in ('PLAYING', 'PAUSED', 'BUFFERING'):
                    lease.last_access = time.monotonic()
                    viewer_service.player.touch(lease.session_id)

    async def close(self):
        async with self.lock:
            for cast in list(self.active.values()):
                with suppress(Exception):
                    await self._stop(cast)
        await run_in_threadpool(self.discovery.close)


cast_service = CastService()
