from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
import logging
from ..models import AcestreamChannel
from ..extensions import db
from .base import BaseRepository

logger = logging.getLogger(__name__)

class ChannelRepository(BaseRepository[AcestreamChannel]):
    def __init__(self):
        super().__init__(AcestreamChannel)
        
    def get_by_id(self, channel_id: str) -> Optional[AcestreamChannel]:
        """Get a channel by ID."""
        try:
            return self.model.query.get(channel_id)
        except SQLAlchemyError as e:
            logger.error(f"Error getting channel {channel_id}: {e}")
            return None

    def create(self, channel_id, name, source_url=None, scraped_url_id=None, **kwargs):
        """Create a new channel."""
        try:
            channel = AcestreamChannel(
                id=channel_id,
                name=name,
                source_url=source_url,
                scraped_url_id=scraped_url_id,
                **kwargs  # Support additional fields like group, logo, etc.
            )
            self._db.session.add(channel)
            self._db.session.commit()
            return channel
        except Exception as e:
            self._db.session.rollback()
            logger.error(f"Error creating channel: {e}", exc_info=True)
            return None

    def update(self, channel: AcestreamChannel, **kwargs) -> Optional[AcestreamChannel]:
        """Update an existing channel."""
        try:
            for key, value in kwargs.items():
                setattr(channel, key, value)
            self._db.session.commit()
            return channel
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error updating channel {channel.id}: {e}")
            return None

    def delete(self, channel_id: str) -> bool:
        """Delete a channel by ID."""
        try:
            channel = self.get_by_id(channel_id)
            if channel:
                self._db.session.delete(channel)
                self._db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error deleting channel {channel_id}: {e}")
            return False

    def get_active(self) -> List[AcestreamChannel]:
        """Get all active channels."""
        try:
            return self.model.query.filter_by(status='active').all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active channels: {e}")
            return []

    def get_channel_sources(self) -> List[str]:
        """Get all unique channel sources."""
        try:
            sources = self._db.session.query(AcestreamChannel.source_url)\
            .filter(AcestreamChannel.source_url.isnot(None))\
            .distinct()\
            .all()
            return [source[0] for source in sources if source[0]]
        except SQLAlchemyError as e:
            logger.error(f"Error getting channel sources: {e}")
            return []
    
    def get_by_source(self, source_url: str) -> List[AcestreamChannel]:
        """Get all channels from a specific source URL."""
        try:
            return self.model.query.filter_by(source_url=source_url).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting channels for source {source_url}: {e}")
            return []

    def delete_by_source(self, source_url: str) -> bool:
        """Delete all channels from a specific source URL."""
        try:
            self.model.query.filter_by(source_url=source_url).delete()
            self._db.session.commit()
            return True
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error deleting channels for source {source_url}: {e}")
            return False

    def update_or_create(self, channel_id: str, name: str, source_url: str = None, metadata: dict = None) -> AcestreamChannel:
        """Update an existing channel or create a new one."""
        channel = self.model.query.filter_by(id=channel_id).first()
        
        if channel:
            channel.name = name
            if source_url:
                channel.source_url = source_url
            channel.last_updated = datetime.now()
        else:
            channel = self.model(
                id=channel_id,
                name=name,
                source_url=source_url,
                status='active',
                is_online=True,
            )
        
        # Update metadata fields if provided
        if metadata:
            if 'tvg_id' in metadata:
                channel.tvg_id = metadata['tvg_id']
            if 'tvg_name' in metadata:
                channel.tvg_name = metadata['tvg_name']
            if 'logo' in metadata:
                channel.logo = metadata['logo']
            if 'group' in metadata:
                channel.group = metadata['group']
        
        # Add the channel to the session
        self._db.session.add(channel)
        
        return channel

    def update_status(self, channel_id: str, is_online: bool, error: str = None) -> Optional[AcestreamChannel]:
        """Update channel status after checking availability."""
        try:
            channel = self.get_by_id(channel_id)
            if channel:
                channel.is_online = is_online
                channel.last_checked = datetime.now(timezone.utc)
                channel.check_error = error
                self._db.session.commit()
                return channel
            return None
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error updating status for channel {channel_id}: {e}")
            return None

    def search(self, term: str) -> List[AcestreamChannel]:
        """Search channels by name."""
        try:
            if not term:
                return self.get_active()
            return self.model.query.filter(
                self.model.name.ilike(f'%{term}%')
            ).filter_by(status='active').all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching channels with term '{term}': {e}")
            return []

    def remove_offline_channels(self) -> int:
        """Remove all offline channels and return count of removed channels."""
        try:
            result = self.model.query.filter_by(is_online=False).delete()
            self._db.session.commit()
            return result
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error removing offline channels: {e}")
            return 0

    def update_channel_status(self, channel_id: str, is_online: bool, check_time: datetime, error: str = None) -> bool:
        """Update a single channel's status."""
        try:
            # Use execute directly with autocommit
            result = self._db.session.execute(
                """UPDATE acestream_channels 
                   SET is_online = :is_online,
                       last_checked = :check_time,
                       check_error = :error
                   WHERE id = :channel_id""",
                {
                    'channel_id': channel_id,
                    'is_online': is_online,
                    'check_time': check_time,
                    'error': error
                }
            )
            self._db.session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error updating status for channel {channel_id}: {e}")
            try:
                self._db.session.rollback()
            except:
                pass
            return False
            
    def commit(self):
        """Commit the current transaction."""
        try:
            self._db.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error committing transaction: {e}")
            raise
            
    def rollback(self):
        """Rollback the current transaction."""
        try:
            self._db.session.rollback()
        except SQLAlchemyError as e:
            logger.error(f"Error rolling back transaction: {e}")
            raise

    def get_all(self, tv_channel_id=None) -> List[AcestreamChannel]:
        """
        Get all channels with optional filtering by TV channel association.
        
        Args:
            tv_channel_id: If provided, filter channels by this TV channel ID. 
                          If None, return only channels not assigned to any TV channel.
                          If not specified, return all channels.
        
        Returns:
            List of AcestreamChannel objects
        """
        try:
            query = self.model.query
            
            # Filter by TV channel ID if specified
            if tv_channel_id is not None:
                # Check if we're looking for unassigned channels
                if tv_channel_id is None:
                    query = query.filter(self.model.tv_channel_id.is_(None))
                else:
                    query = query.filter(self.model.tv_channel_id == tv_channel_id)
                
            return query.order_by(self.model.name).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting channels: {e}")
            return []