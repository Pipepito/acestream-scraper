from typing import List, Optional, Dict
from app.models.epg_channel import EPGChannel
from app.extensions import db

class EPGChannelRepository:
    """Repository for EPG channel operations."""
    
    def get_all(self) -> List[EPGChannel]:
        """Get all EPG channels."""
        return EPGChannel.query.all()
    
    def get_by_id(self, id: int) -> Optional[EPGChannel]:
        """Get EPG channel by ID."""
        return EPGChannel.query.get(id)
    
    def get_by_source_id(self, source_id: int) -> List[EPGChannel]:
        """Get all channels for a specific EPG source."""
        return EPGChannel.query.filter_by(epg_source_id=source_id).all()
    
    def get_by_channel_xml_id(self, channel_xml_id: str) -> List[EPGChannel]:
        """Get channels with matching XML ID (across all sources)."""
        return EPGChannel.query.filter_by(channel_xml_id=channel_xml_id).all()
    
    def get_by_source_and_channel_xml_id(self, source_id: int, channel_xml_id: str) -> Optional[EPGChannel]:
        """Get channel by source ID and XML channel ID."""
        return EPGChannel.query.filter_by(epg_source_id=source_id, channel_xml_id=channel_xml_id).first()
    
    def create(self, channel_data: Dict) -> EPGChannel:
        """Create a new EPG channel."""
        channel = EPGChannel(**channel_data)
        db.session.add(channel)
        db.session.commit()
        return channel
    
    def update(self, channel: EPGChannel) -> EPGChannel:
        """Update an existing EPG channel."""
        db.session.commit()
        return channel
    
    def delete(self, channel: EPGChannel) -> None:
        """Delete an EPG channel."""
        db.session.delete(channel)
        db.session.commit()
    
    def create_or_update(self, source_id: int, channel_xml_id: str, data: Dict) -> EPGChannel:
        """Create or update an EPG channel."""
        channel = self.get_by_source_and_channel_xml_id(source_id, channel_xml_id)
        
        if channel:
            # Update existing channel
            for key, value in data.items():
                setattr(channel, key, value)
        else:
            # Create new channel
            data['epg_source_id'] = source_id
            data['channel_xml_id'] = channel_xml_id
            channel = EPGChannel(**data)
            db.session.add(channel)
        
        db.session.commit()
        return channel
    
    def bulk_insert(self, channels_data: List[Dict]) -> int:
        """
        Bulk insert multiple EPG channels.
        
        Args:
            channels_data: List of dictionaries with channel data
            
        Returns:
            Number of channels inserted
        """
        if not channels_data:
            return 0
            
        # Create list of EPGChannel objects
        new_channels = [EPGChannel(**data) for data in channels_data]
        
        # Add all channels to session
        db.session.add_all(new_channels)
        db.session.commit()
        
        return len(new_channels)
    
    def delete_by_source_id(self, source_id: int) -> int:
        """Delete all channels for a specific source."""
        count = EPGChannel.query.filter_by(epg_source_id=source_id).delete()
        db.session.commit()
        return count
