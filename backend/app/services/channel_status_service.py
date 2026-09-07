"""
Service for checking Acestream channel status
"""
import asyncio
import logging
import aiohttp
import math
import re
from urllib.parse import urlparse
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import AcestreamChannel
from app.repositories.channel_repository import ChannelRepository
from app.services.stream_bitrate_service import probe_media
from app.services.probe_queue import ProbePriority, probe_queue

logger = logging.getLogger(__name__)



class ChannelStatusService:
    """Service for checking Acestream channel status via engine API"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.channel_repository = ChannelRepository(db)
        from app.repositories.settings_repository import SettingsRepository
        self.settings_repo = SettingsRepository(db)
        self.timeout = 10
        self.engine_unavailable = False

    def _get_timeout(self) -> float:
        """Engine status timeout in seconds, configurable via the
        acestream_check_timeout setting (default 10)."""
        raw = self.settings_repo.get_setting(
            self.settings_repo.ACESTREAM_CHECK_TIMEOUT,
            self.settings_repo.DEFAULT_ACESTREAM_CHECK_TIMEOUT,
        )
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return float(self.timeout)
        return min(value, 120.0) if math.isfinite(value) and value > 0 else float(self.timeout)

    async def _fetch_engine_response(self, status_url: str, params: Dict[str, str], timeout: float):
        """Query the engine once. Returns (http_status, parsed_json_or_None,
        parse_error_message_or_None). Raises asyncio.TimeoutError on timeout."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                status_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=False,
            ) as response:
                if response.status != 200:
                    return response.status, None, None
                try:
                    return response.status, await response.json(), None
                except Exception as e:
                    return response.status, None, f"Invalid response format: {str(e)}"

    def _get_engine_url(self) -> str:
        url = self.settings_repo.get_setting(self.settings_repo.ACE_ENGINE_URL, None)
        if not url:
            raise RuntimeError("Acestream Engine URL is not set in the database. Please configure it via the settings API.")
        url = url.strip()
        if not url.startswith('http'):
            url = f"http://{url}"
        return url.rstrip('/')

    @staticmethod
    def _session_url(engine_url: str, value: Any, kind: str) -> Optional[str]:
        """Keep session requests on the configured engine, including remote engines
        which advertise localhost URLs. Never follow arbitrary upstream targets.
        """
        if not isinstance(value, str):
            return None
        path = urlparse(value).path
        if not re.fullmatch(rf"/ace/{kind}/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+", path):
            return None
        return f"{engine_url}{path}"

    async def _verify_broadcast(self, engine_url: str, data: Dict[str, Any], timeout: float, channel_id: str = ""):
        response = data.get('response')
        if not isinstance(response, dict):
            return False, 'Invalid response format', None
        stat_url = self._session_url(engine_url, response.get('stat_url'), 'stat')
        command_url = self._session_url(engine_url, response.get('command_url'), 'cmd')
        try:
            if data.get('error'):
                return False, 'Engine could not start the stream', None
            if not stat_url or not command_url:
                return False, 'Engine did not provide a verifiable playback session', None
            deadline = asyncio.get_running_loop().time() + timeout
            previous_downloaded = None
            while True:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    return False, 'No broadcast data received before timeout', None
                http_status, stats, parse_error = await self._fetch_engine_response(stat_url, {}, remaining)
                if http_status != 200 or parse_error or not isinstance(stats, dict):
                    return False, 'Could not read stream statistics', None
                state = stats.get('response')
                if stats.get('error') or not isinstance(state, dict):
                    return False, 'Engine could not read stream statistics', None
                if state.get('status') in ('error', 'err', 'idle', 'stopped'):
                    return False, 'Stream is not broadcasting', None
                downloaded = state.get('downloaded')
                if (isinstance(downloaded, (int, float)) and not isinstance(downloaded, bool)
                        and math.isfinite(downloaded) and downloaded >= 0):
                    # Metadata (is_live), connected peers, a cached byte total,
                    # and catalogue status cannot prove current emission.
                    if (previous_downloaded is not None and downloaded > previous_downloaded
                            and state.get('status') in ('dl', 'prebuf', 'buf')):
                        playback_url = self._session_url(engine_url, response.get('playback_url'), 'r')
                        media = None if self._in_use(channel_id) else await probe_media(engine_url, playback_url)
                        if media and media.get('signal_verified') is True:
                            return True, 'Media signal verified', media
                        return False, 'ID found, but no media signal verified before timeout', media
                    previous_downloaded = downloaded
                await asyncio.sleep(min(1.0, max(0, deadline - asyncio.get_running_loop().time())))
        finally:
            if command_url and not self._in_use(channel_id):
                try:
                    await self._fetch_engine_response(command_url, {'method': 'stop'}, 3.0)
                except Exception:
                    logger.warning('Could not stop channel status probe session')

    @staticmethod
    def _in_use(channel_id: str) -> bool:
        from app.services.stream_relay import relay_registry
        from app.services.player_service import player_service
        key = channel_id.lower()
        return any(relay.content_id.lower() == key for relay in relay_registry.active()) or any(
            session.content_id.lower() == key and session.state in ('starting', 'ready')
            for session in player_service.list_sessions()
        )

    @staticmethod
    def _skipped_result(channel: AcestreamChannel) -> Dict[str, Any]:
        return {
            'channel_id': channel.id, 'is_online': channel.is_online is True,
            'network_status': channel.network_status,
            'status': 'skipped', 'message': 'Source is in use; keeping its previous status',
            'last_checked': channel.last_checked or datetime.now(timezone.utc), 'error': None,
        }

    def _recent_result(self, channel_id: str, since: datetime) -> Optional[Dict[str, Any]]:
        # A scan's ORM inventory can be minutes old. Read committed status in a
        # fresh session, off the event loop, so other callers' results are seen.
        with Session(bind=self.db.get_bind()) as db:
            snapshot = ChannelRepository(db).get_status_snapshot(channel_id)
        if not snapshot or not snapshot['last_checked'] or snapshot['last_checked'] < since:
            return None
        return {
            'channel_id': channel_id, 'is_online': snapshot['is_online'] is True,
            'network_status': snapshot.get('network_status'),
            'status': 'skipped', 'message': 'Recently checked; using the latest channel status',
            'last_checked': snapshot['last_checked'], 'error': None,
        }

    async def check_channel_status(
        self, channel: AcestreamChannel, *, identifier: str = 'id', persist: bool = True,
        priority: ProbePriority = ProbePriority.MANUAL, scan_started_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        submitted = datetime.now(timezone.utc)
        since = submitted if priority == ProbePriority.MANUAL else submitted - timedelta(seconds=30)
        if priority == ProbePriority.BACKGROUND and scan_started_at is not None:
            since = min(since, scan_started_at)
        if self._in_use(channel.id):
            return self._skipped_result(channel)
        ticket = probe_queue.enqueue(priority)
        probed = False
        try:
            await probe_queue.acquire(ticket)
            if self._in_use(channel.id):
                return self._skipped_result(channel)
            if persist and identifier == 'id':
                recent = await asyncio.to_thread(self._recent_result, channel.id, since)
                if recent:
                    return recent
            self.engine_unavailable = False
            probed = True
            return await self._check_channel_status(channel, identifier=identifier, persist=persist)
        finally:
            probe_queue.cancel(ticket)
            probe_queue.release(ticket, probed=probed, engine_unavailable=self.engine_unavailable)

    async def _engine_ready(self, engine_url: str) -> bool:
        try:
            status, data, error = await self._fetch_engine_response(
                f"{engine_url}/server/api",
                {'api_version': '3', 'method': 'get_status'}, 3.0,
            )
            return status == 200 and not error and isinstance(data, dict) and isinstance(data.get('result'), dict) and not data.get('error')
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def _wait_for_engine(self, engine_url: str) -> bool:
        deadline = asyncio.get_running_loop().time() + 60.0
        while True:
            if await self._engine_ready(engine_url):
                return True
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                return False
            await asyncio.sleep(min(2.0, remaining))

    def _engine_unavailable_result(self, channel: AcestreamChannel) -> Dict[str, Any]:
        self.engine_unavailable = True
        result = self._skipped_result(channel)
        result['message'] = 'Engine unavailable; keeping the previous channel status until a later check'
        return result

    async def _check_channel_status(
        self, channel: AcestreamChannel, *, identifier: str = 'id', persist: bool = True
    ) -> Dict[str, Any]:
        """Check current data transfer using a bounded probe with a unique PID."""
        online = False
        media = None
        engine_url = None
        network_status = 'unknown'
        try:
            engine_url = self._get_engine_url()
            if not await self._wait_for_engine(engine_url):
                return self._engine_unavailable_result(channel)
            if self._in_use(channel.id):
                return self._skipped_result(channel)
            status_url = f"{engine_url}/ace/getstream"
            params = {identifier: channel.id, 'format': 'json', 'pid': uuid4().hex}
            timeout = self._get_timeout()
            try:
                http_status, data, parse_error = await self._fetch_engine_response(status_url, params, timeout)
            except asyncio.TimeoutError:
                logger.warning('Channel probe start timed out; retrying once channel_id=%s', channel.id)
                if not await self._wait_for_engine(engine_url):
                    return self._engine_unavailable_result(channel)
                if self._in_use(channel.id):
                    return self._skipped_result(channel)
                http_status, data, parse_error = await self._fetch_engine_response(status_url, params, timeout * 2)
            if isinstance(data, dict):
                error_text = str(data.get('error') or '').strip().lower()
                if error_text in {'not found', 'content not found', 'content id not found', 'unknown content id'}:
                    network_status = 'not_found'
                elif not data.get('error') and isinstance(data.get('response'), dict):
                    response = data['response']
                    if self._session_url(engine_url, response.get('stat_url'), 'stat') and self._session_url(engine_url, response.get('command_url'), 'cmd'):
                        network_status = 'found'
            if http_status != 200:
                message = f'HTTP {http_status}'
            elif parse_error or not isinstance(data, dict):
                message = 'Invalid response format'
            else:
                online, message, media = await self._verify_broadcast(engine_url, data, timeout, channel.id)
                if network_status == 'not_found':
                    message = 'Engine reports this content ID was not found'
        except asyncio.TimeoutError:
            message = 'Request timeout'
        except Exception:
            message = 'Could not verify broadcast with the engine'
            logger.warning('Channel broadcast probe failed channel_id=%s', channel.id)
        if self._in_use(channel.id):
            return self._skipped_result(channel)
        if not online and (not engine_url or not await self._engine_ready(engine_url)):
            return self._engine_unavailable_result(channel)
        check_time = datetime.now(timezone.utc)
        error = None if online else message
        if persist:
            self.channel_repository.update_channel_status(channel.id, online, error, bitrate_bps=media.get("bitrate_bps") if media else None,
                audio_tracks=media.get("audio_tracks") if media else None, network_status=network_status)
        return {
            'channel_id': channel.id,
            'network_status': network_status,
            'is_online': online,
            'status': 'online' if online else 'offline',
            'message': message,
            'last_checked': check_time,
            'error': error,
        }

    async def check_multiple_channels(
        self, channels: List[AcestreamChannel], concurrency: int = 3,
    ) -> List[Dict[str, Any]]:
        """Bulk work queues one source at a time behind interactive requests.

        ``concurrency`` remains accepted for API compatibility; all callers use
        the single engine slot and its global cooldown.
        """
        started = datetime.now(timezone.utc)
        results = []
        for channel in channels:
            try:
                results.append(await self.check_channel_status(
                    channel, priority=ProbePriority.BACKGROUND, scan_started_at=started,
                ))
            except Exception:
                logger.warning('Channel status check failed channel_id=%s', channel.id)
                results.append({
                    'channel_id': channel.id, 'is_online': channel.is_online is True,
                    'status': 'error', 'message': 'Could not check channel status',
                    'last_checked': channel.last_checked or datetime.now(timezone.utc),
                    'error': 'Could not check channel status',
                })
        return results

    def get_channel_status_summary(self) -> Dict[str, Any]:
        """
        Get summary of channel statuses

        Returns:
            Dict with status counts and summary
        """
        channels = self.channel_repository.get_channels(limit=10000)

        total = len(channels)
        online = sum(1 for c in channels if c.is_online is True)
        offline = sum(1 for c in channels if c.is_online is False)
        unknown = sum(1 for c in channels if c.is_online is None)
        active_channels = sum(1 for c in channels if c.is_active is True)

        # Get recent checks (last 24 hours)
        recent_threshold = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        recent_checks = sum(
            1 for c in channels
            if c.last_checked and c.last_checked >= recent_threshold
        )

        return {
            'total_channels': total,
            'active_channels': active_channels,
            'online': online,
            'online_channels': online,  # Duplicate for test compatibility
            'offline': offline,
            'offline_channels': offline,  # Test expects this field name
            'unknown': unknown,
            'recent_checks': recent_checks,
            'last_checked_channels': recent_checks,  # Test expects this field name
            'online_percentage': round((online / total * 100) if total > 0 else 0, 1),
            'checked_percentage': round((recent_checks / total * 100) if total > 0 else 0, 1)
        }
