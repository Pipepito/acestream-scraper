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
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import AcestreamChannel
from app.repositories.channel_repository import ChannelRepository
from app.services.stream_bitrate_service import probe_media

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

    async def _verify_broadcast(self, engine_url: str, data: Dict[str, Any], timeout: float):
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
                        media = await probe_media(engine_url, response.get('playback_url'))
                        return True, 'Broadcast data is arriving', media
                    previous_downloaded = downloaded
                await asyncio.sleep(min(1.0, max(0, deadline - asyncio.get_running_loop().time())))
        finally:
            if command_url:
                try:
                    await self._fetch_engine_response(command_url, {'method': 'stop'}, 3.0)
                except Exception:
                    logger.warning('Could not stop channel status probe session')

    async def check_channel_status(
        self, channel: AcestreamChannel, *, identifier: str = 'id', persist: bool = True
    ) -> Dict[str, Any]:
        """Check current data transfer in an isolated, bounded playback session."""
        online = False
        media = None
        try:
            engine_url = self._get_engine_url()
            status_url = f"{engine_url}/ace/getstream"
            params = {identifier: channel.id, 'format': 'json', 'pid': uuid4().hex}
            timeout = self._get_timeout()
            try:
                http_status, data, parse_error = await self._fetch_engine_response(status_url, params, timeout)
            except asyncio.TimeoutError:
                logger.warning('Channel probe start timed out; retrying once channel_id=%s', channel.id)
                http_status, data, parse_error = await self._fetch_engine_response(status_url, params, timeout * 2)
            if http_status != 200:
                message = f'HTTP {http_status}'
            elif parse_error or not isinstance(data, dict):
                message = 'Invalid response format'
            else:
                online, message, media = await self._verify_broadcast(engine_url, data, timeout)
        except asyncio.TimeoutError:
            message = 'Request timeout'
        except Exception:
            message = 'Could not verify broadcast with the engine'
            logger.warning('Channel broadcast probe failed channel_id=%s', channel.id)
        check_time = datetime.now(timezone.utc)
        error = None if online else message
        if persist:
            self.channel_repository.update_channel_status(channel.id, online, error, bitrate_bps=media.get("bitrate_bps") if media else None,
                audio_tracks=media.get("audio_tracks") if media else None)
        return {
            'channel_id': channel.id,
            'is_online': online,
            'status': 'online' if online else 'offline',
            'message': message,
            'last_checked': check_time,
            'error': error,
        }

    async def check_multiple_channels(
        self,
        channels: List[AcestreamChannel],
        concurrency: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Check multiple channels concurrently with rate limiting

        Args:
            channels: List of channels to check
            concurrency: Number of concurrent checks

        Returns:
            List of status results
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def check_with_semaphore(channel):
            async with semaphore:
                try:
                    result = await self.check_channel_status(channel)
                    # Add delay between requests to avoid overwhelming the engine
                    await asyncio.sleep(1)
                    return result
                except Exception as e:
                    logger.error("Error checking channel channel_id=%s error=%s", channel.id, e)
                    return {
                        'channel_id': channel.id,
                        'is_online': False,
                        'status': 'error',
                        'message': str(e),
                        'last_checked': datetime.now(timezone.utc),
                        'error': str(e)
                    }

        # Process channels in batches to manage memory and connections
        batch_size = 10
        all_results = []

        for i in range(0, len(channels), batch_size):
            batch = channels[i:i + batch_size]
            tasks = [asyncio.create_task(check_with_semaphore(channel)) for channel in batch]

            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                # Filter out exceptions and add valid results
                for result in batch_results:
                    if not isinstance(result, Exception):
                        all_results.append(result)
                    else:
                        logger.error("Task exception result=%s", result)
            except Exception as e:
                logger.error("Error processing status batch error=%s", e)
            finally:
                # Cancel any remaining tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()

            # Add delay between batches
            if i + batch_size < len(channels):
                await asyncio.sleep(2)

        return all_results

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
