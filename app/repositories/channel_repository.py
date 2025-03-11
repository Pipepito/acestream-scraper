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

    def create(self, channel_id: str, name: str, **kwargs) -> Optional[AcestreamChannel]:
        """Create a new channel."""
        try:
            channel = AcestreamChannel(
                id=channel_id,
                name=name,
                added_at=datetime.now(timezone.utc),
                status='active',
                **kwargs
            )
            self._db.session.add(channel)
            self._db.session.commit()
            return channel
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error creating channel {channel_id}: {e}")
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

    def update_or_create(self, channel_id: str, name: str, source_url: str, metadata: dict = None) -> Optional[AcestreamChannel]:
        """Update an existing channel or create a new one."""
        try:
            channel = self.get_by_id(channel_id)
            if not channel:
                channel = self.model(id=channel_id)
                self._db.session.add(channel)

            # Update basic fields
            channel.name = name
            channel.last_processed = datetime.now(timezone.utc)
            channel.status = 'active'
            channel.source_url = source_url

            # Update metadata if provided
            if metadata:
                channel.group = metadata.get('group')
                channel.logo = metadata.get('logo')
                channel.tvg_id = metadata.get('tvg_id')
                channel.tvg_name = metadata.get('tvg_name')
                channel.m3u_source = metadata.get('m3u_source')
                channel.original_url = metadata.get('original_url')

            self._db.session.commit()
            return channel
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error updating/creating channel {channel_id}: {e}")
            return None

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