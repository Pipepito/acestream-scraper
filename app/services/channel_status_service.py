import asyncio
import logging
import aiohttp
import threading
from datetime import datetime, timezone
from typing import Optional, List, Union, Dict, Any
from ..models import AcestreamChannel
from ..extensions import db
from ..utils.config import Config
from ..repositories.channel_repository import ChannelRepository

logger = logging.getLogger(__name__)

class ChannelStatusService:
    """Service for checking Acestream channel status."""
    
    def __init__(self):
        config = Config()
        self.ace_engine_url = config.ace_engine_url
        self.timeout = 10
        self.repo = ChannelRepository()  # Create single repository instance
        
    async def check_channel(self, channel: AcestreamChannel) -> bool:
        """Check if a channel is alive by querying the Acestream engine."""
        from flask import current_app
        
        try:
            check_time = datetime.now(timezone.utc)
            
            # Build status check URL
            status_url = f"{self.ace_engine_url}/ace/getstream"
            params = {
                'id': channel.id,
                'format': 'json',
                'method': 'get_status'
            }
            
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
                                
                                # Perform database updates within app context
                                with current_app.app_context():
                                    # Check for "got newer download" message
                                    if error and "got newer download" in str(error).lower():
                                        self.repo.update_channel_status(channel.id, True, check_time)
                                        return True
                                    
                                    # Check regular online status
                                    if (error is None and 
                                        response_data and 
                                        response_data.get('is_live') == 1):
                                        self.repo.update_channel_status(channel.id, True, check_time)
                                        return True
                                    
                                    # Channel exists but not available
                                    error_msg = error if error else "Channel is not live"
                                    self.repo.update_channel_status(channel.id, False, check_time, error_msg)
                                    logger.info(f"Channel {channel.id} ({channel.name}) is offline: {error_msg}")
                                    return False
                                    
                            with current_app.app_context():
                                self.repo.update_channel_status(channel.id, False, check_time, "Invalid response format")
                            return False
                                
                        except ValueError as e:
                            with current_app.app_context():
                                self.repo.update_channel_status(channel.id, False, check_time, f"Invalid response format: {str(e)}")
                            return False
                    
                    with current_app.app_context():
                        self.repo.update_channel_status(channel.id, False, check_time, f"HTTP {response.status}")
                    return False
            
        except Exception as e:
            logger.error(f"Error checking channel {channel.id}: {e}")
            with current_app.app_context():
                self.repo.update_channel_status(channel.id, False, check_time, str(e))
            return False
            
    async def check_channels(self, channels: List[AcestreamChannel], concurrency: int = 2):
        """Check multiple channels concurrently with rate limiting."""
        semaphore = asyncio.Semaphore(concurrency)
        
        async def check_with_semaphore(channel):
            async with semaphore:
                try:
                    # Check the channel
                    result = await self.check_channel(channel)
                    await asyncio.sleep(2)
                    return result
                except Exception as e:
                    logger.error(f"Error checking channel {channel.id}: {e}")
                    return False
        
        chunk_size = 2
        results = []
        
        for i in range(0, len(channels), chunk_size):
            chunk = channels[i:i + chunk_size]
            tasks = [asyncio.create_task(check_with_semaphore(channel)) for channel in chunk]
            
            try:
                chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
                results.extend([r for r in chunk_results if not isinstance(r, Exception)])
            except Exception as e:
                logger.error(f"Error processing chunk: {e}", exc_info=True)
            finally:
                for task in tasks:
                    if not task.done():
                        task.cancel()
            
            await asyncio.sleep(2)
        
        return results

async def check_channel_status(channel_id_or_obj: Union[str, AcestreamChannel, Dict[str, Any]]) -> dict:
    """
    Check status of a single channel.
    
    Args:
        channel_id_or_obj: Can be channel ID string, channel object or dict with channel data
    """
    from flask import current_app
    
    # Determine what we're working with and get channel ID
    channel_id = None
    channel_name = None
    
    if isinstance(channel_id_or_obj, str):
        channel_id = channel_id_or_obj
    elif isinstance(channel_id_or_obj, dict):
        channel_id = channel_id_or_obj.get('id')
        channel_name = channel_id_or_obj.get('name', 'Unknown')
    elif hasattr(channel_id_or_obj, 'id'):
        channel_id = channel_id_or_obj.id
        channel_name = getattr(channel_id_or_obj, 'name', 'Unknown')
    
    if not channel_id:
        raise ValueError("Missing channel ID")
        
    # Create a new service instance
    service = ChannelStatusService()
    
    # We need to get a fresh channel object in a new session
    with current_app.app_context():
        repo = ChannelRepository()
        channel = repo.get_by_id(channel_id)
        if not channel:
            raise ValueError(f"Channel {channel_id} not found")
            
        # Now check the channel
        is_online = await service.check_channel(channel)
        
        # Get the fresh state after the check
        updated_channel = repo.get_by_id(channel_id)
        
        # Return the results
        return {
            'id': channel_id,
            'name': channel_name or updated_channel.name,
            'is_online': is_online, 
            'status': 'online' if is_online else 'offline',
            'last_checked': updated_channel.last_checked,
            'error': updated_channel.check_error
        }

def start_background_check(channels: list[AcestreamChannel]) -> dict:
    """Start background channel status check."""
    from flask import current_app
    
    # Capture the app instance before starting the thread
    app = current_app._get_current_object()
    
    async def run_checks():
        service = ChannelStatusService()
        try:
            batch_size = 30
            total_processed = 0
            
            for i in range(0, len(channels), batch_size):
                batch = channels[i:i + batch_size]
                with app.app_context():
                    await service.check_channels(batch, concurrency=5)
                total_processed += len(batch)
                logger.info(f"Processed {total_processed}/{len(channels)} channels")
                await asyncio.sleep(3)
                
        except Exception as e:
            logger.error(f"Error in background check: {e}", exc_info=True)
    
    def run_background():
        # Create new event loop for the background thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(run_checks())
            logger.info("Background check completed successfully")
        except Exception as e:
            logger.error(f"Background thread error: {e}", exc_info=True)
        finally:
            try:
                loop.close()
            except Exception as e:
                logger.error(f"Error closing loop: {e}")
    
    # Start background thread
    thread = threading.Thread(target=run_background)
    thread.daemon = True
    thread.start()
    
    logger.info(f"Started background check for {len(channels)} channels")
    return {
        'message': 'Status check started',
        'total_channels': len(channels)
    }