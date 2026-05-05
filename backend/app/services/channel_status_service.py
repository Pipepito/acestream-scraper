"""
Service for checking Acestream channel status
"""
import asyncio
import logging
import aiohttp
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.models import AcestreamChannel
from app.repositories.channel_repository import ChannelRepository

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
        self._next_player_id = 0

    def _get_engine_url(self) -> str:
        url = self.settings_repo.get_setting(self.settings_repo.ACE_ENGINE_URL, None)
        if not url:
            raise RuntimeError("Acestream Engine URL is not set in the database. Please configure it via the settings API.")
        url = url.strip()
        if not url.startswith('http'):
            url = f"http://{url}"
        return url.rstrip('/')

    async def check_channel_status(self, channel: AcestreamChannel) -> Dict[str, Any]:
        """
        Check if a single channel is online by querying the Acestream engine

        Args:
            channel: The channel to check

        Returns:
            Dict with status information
        """
        check_time = datetime.now(timezone.utc)

        try:
            # Generate unique player ID
            self._next_player_id = (self._next_player_id + 1) % 100000

            # Always fetch the latest engine_url from DB
            engine_url = self._get_engine_url()
            status_url = f"{engine_url}/ace/getstream"
            params = {
                'id': channel.id,
                'format': 'json',
                'method': 'get_status',
                'pid': str(self._next_player_id)
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    status_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:

                    if response.status == 200:
                        try:
                            data = await response.json()

                            if isinstance(data, dict):
                                response_data = data.get('response', {})
                                error = data.get('error')

                                # Check for "got newer download" message (indicates channel exists)
                                if error and "got newer download" in str(error).lower():
                                    self.channel_repository.update_channel_status(
                                        channel.id, True, None
                                    )
                                    return {
                                        'channel_id': channel.id,
                                        'is_online': True,
                                        'status': 'online',
                                        'message': 'Channel is available',
                                        'last_checked': check_time,
                                        'error': None
                                    }

                                # Check regular online status
                                if (error is None and
                                    response_data and
                                    response_data.get('is_live') == 1):
                                    self.channel_repository.update_channel_status(
                                        channel.id, True, None
                                    )
                                    return {
                                        'channel_id': channel.id,
                                        'is_online': True,
                                        'status': 'online',
                                        'message': 'Channel is live',
                                        'last_checked': check_time,
                                        'error': None
                                    }

                                # Channel exists but not available
                                error_msg = error if error else "Channel is not live"
                                self.channel_repository.update_channel_status(
                                    channel.id, False, str(error_msg)
                                )
                                return {
                                    'channel_id': channel.id,
                                    'is_online': False,
                                    'status': 'offline',
                                    'message': error_msg,
                                    'last_checked': check_time,
                                    'error': error_msg
                                }

                            # Invalid response format
                            error_msg = "Invalid response format"
                            self.channel_repository.update_channel_status(
                                channel.id, False, error_msg
                            )
                            return {
                                'channel_id': channel.id,
                                'is_online': False,
                                'status': 'offline',
                                'message': error_msg,
                                'last_checked': check_time,
                                'error': error_msg
                            }

                        except Exception as e:
                            error_msg = f"Invalid response format: {str(e)}"
                            self.channel_repository.update_channel_status(
                                channel.id, False, error_msg
                            )
                            return {
                                'channel_id': channel.id,
                                'is_online': False,
                                'status': 'offline',
                                'message': error_msg,
                                'last_checked': check_time,
                                'error': error_msg
                            }

                    # HTTP error
                    error_msg = f"HTTP {response.status}"
                    self.channel_repository.update_channel_status(
                        channel.id, False, error_msg
                    )
                    return {
                        'channel_id': channel.id,
                        'is_online': False,
                        'status': 'offline',
                        'message': error_msg,
                        'last_checked': check_time,
                        'error': error_msg
                    }

        except asyncio.TimeoutError:
            error_msg = "Request timeout"
            self.channel_repository.update_channel_status(
                channel.id, False, error_msg
            )
            logger.warning(
                "Timeout checking channel channel_id=%s channel_name=%s",
                channel.id,
                channel.name,
            )
            return {
                'channel_id': channel.id,
                'is_online': False,
                'status': 'offline',
                'message': error_msg,
                'last_checked': check_time,
                'error': error_msg
            }
        except Exception as e:
            error_msg = str(e)
            self.channel_repository.update_channel_status(
                channel.id, False, error_msg
            )
            logger.error("Error checking channel channel_id=%s error=%s", channel.id, e)
            return {
                'channel_id': channel.id,
                'is_online': False,
                'status': 'offline',
                'message': error_msg,
                'last_checked': check_time,
                'error': error_msg
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
