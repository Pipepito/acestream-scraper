import asyncio
import logging
import aiohttp
from datetime import datetime, timezone
from typing import Optional
from ..models import AcestreamChannel
from ..extensions import db
from ..utils.config import Config

logger = logging.getLogger(__name__)

class ChannelStatusService:
    """Service for checking Acestream channel status."""
    
    def __init__(self):
        config = Config()
        self.ace_engine_url = config.ace_engine_url
        self.timeout = 10
        
    async def check_channel(self, channel: AcestreamChannel) -> bool:
        """
        Check if a channel is alive by querying the Acestream engine.
        Returns True if channel is online, False otherwise.
        """
        try:
            channel.last_checked = datetime.now(timezone.utc)
            
            # Build status check URL
            status_url = f"{self.ace_engine_url}/ace/getstream"
            params = {
                'id': channel.id,
                'format': 'json',
                'method': 'get_status'
            }
            
            logger.info(f"Checking channel {channel.id} ({channel.name}) status at {status_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(status_url, 
                                     params=params,
                                     timeout=self.timeout) as response:
                    if response.status == 200:
                        try:
                            data = await response.json()
                            
                            if isinstance(data, dict):
                                response_data = data.get('response', {})
                                error = data.get('error')
                                
                                # Check for "got newer download" message - consider channel valid
                                if error and "got newer download" in str(error).lower():
                                    channel.is_online = True
                                    channel.check_error = None
                                    logger.info(f"Channel {channel.id} ({channel.name}) is online (newer version available)")
                                    return True
                                
                                # Channel is considered online if:
                                # 1. No error is present
                                # 2. We have response data
                                # 3. is_live flag is 1 (or True)
                                if (error is None and 
                                    response_data and 
                                    response_data.get('is_live') == 1):
                                    channel.is_online = True
                                    channel.check_error = None
                                    logger.info(f"Channel {channel.id} ({channel.name}) is online")
                                    return True
                                
                                # Channel exists but is not available
                                channel.is_online = False
                                channel.check_error = error if error else "Channel is not live"
                                logger.info(f"Channel {channel.id} ({channel.name}) is offline: {channel.check_error}")
                                return False
                                
                            channel.is_online = False
                            channel.check_error = "Invalid response format"
                            return False
                                
                        except ValueError as e:
                            channel.is_online = False
                            channel.check_error = f"Invalid response format: {str(e)}"
                            return False
                    
                    channel.is_online = False
                    channel.check_error = f"HTTP {response.status}"
                    return False
            
        except Exception as e:
            channel.is_online = False
            channel.check_error = str(e)
            return False
            
        finally:
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"Database error for channel {channel.id}: {str(e)}")
                db.session.rollback()
                raise
                
    async def check_channels(self, channels: list[AcestreamChannel], concurrency: int = 5):
        """Check multiple channels concurrently."""
        semaphore = asyncio.Semaphore(concurrency)
        
        async def check_with_semaphore(channel):
            async with semaphore:
                return await self.check_channel(channel)
        
        tasks = [check_with_semaphore(channel) for channel in channels]
        return await asyncio.gather(*tasks)

async def check_channel_status(channel: AcestreamChannel) -> dict:
    """Check status of a single channel."""
    service = ChannelStatusService()
    is_online = await service.check_channel(channel)
    
    return {
        'is_online': is_online,
        'last_checked': channel.last_checked,
        'error': channel.check_error
    }