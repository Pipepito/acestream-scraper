from typing import List, Dict, Optional, Union
from sqlalchemy.sql import text
from app.models.tv_channel import TVChannel
from app.models.acestream_channel import AcestreamChannel
from app.extensions import db

class TVChannelRepository:
    """Repository for TV Channel operations."""

    def get_by_id(self, channel_id: int) -> Optional[TVChannel]:
        """
        Get a TV channel by its ID.
        
        Args:
            channel_id: The ID of the TV channel
            
        Returns:
            TVChannel object if found, None otherwise
        """
        return TVChannel.query.filter_by(id=channel_id).first()

    def get_by_id(self, id: int) -> Optional[TVChannel]:
        """
        Get a TV channel by ID
        
        Args:
            id: The TV channel ID
            
        Returns:
            TVChannel or None if not found
        """
        return TVChannel.query.get(id)
        
    def get_with_acestreams(self, id: int) -> Optional[Dict]:
        """
        Get a TV channel by ID with associated acestream data
        
        Args:
            id: The TV channel ID
            
        Returns:
            Dictionary with TV channel data and acestreams or None if not found
        """
        channel = self.get_by_id(id)
        if not channel:
            return None
            
        # Get acestreams
        acestreams = AcestreamChannel.query.filter_by(tv_channel_id=id).all()
        
        # Convert to dict
        result = channel.to_dict()
        result['acestream_channels'] = [stream.to_dict() for stream in acestreams]
        
        return result

    def get_all(self, is_active: bool = None) -> List[TVChannel]:
        """
        Get all TV channels.
        
        Args:
            is_active: Filter by active status if provided
            
        Returns:
            List of TVChannel objects
        """
        query = TVChannel.query
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
            
        return query.order_by(TVChannel.name).all()
    
    def filter_channels(self, 
                        category: str = None, 
                        country: str = None, 
                        language: str = None, 
                        search_term: str = None,
                        page: int = 1,
                        per_page: int = 20,
                        favorites_only: bool = False) -> tuple:
        """
        Filter TV channels by various criteria.
        
        Args:
            category: Filter by category
            country: Filter by country
            language: Filter by language
            search_term: Search in name and description
            page: Page number for pagination
            per_page: Number of items per page
            favorites_only: Show only favorite channels
            
        Returns:
            Tuple of (list of TV channels, total number of matches, number of pages)
        """
        query = TVChannel.query
        
        if category:
            query = query.filter_by(category=category)
        if country:
            query = query.filter_by(country=country)
        if language:
            query = query.filter_by(language=language)
        if search_term:
            query = query.filter(
                db.or_(
                    TVChannel.name.ilike(f'%{search_term}%'),
                    TVChannel.description.ilike(f'%{search_term}%')
                )
            )
        if favorites_only:
            query = query.filter_by(is_favorite=True)
            
        # Count total before pagination
        total = query.count()
        total_pages = (total + per_page - 1) // per_page  # Ceiling division
        
        # Apply pagination
        channels = query.order_by(TVChannel.name).paginate(
            page=page, per_page=per_page, error_out=False
        ).items
        
        return channels, total, total_pages

    def create(self, channel_data: Dict) -> TVChannel:
        """
        Create a new TV channel.
        
        Args:
            channel_data: Dictionary containing channel attributes
            
        Returns:
            Created TVChannel object
        """
        channel = TVChannel(**channel_data)
        db.session.add(channel)
        db.session.commit()
        return channel

    def update(self, channel_id: int, channel_data: Dict) -> Optional[TVChannel]:
        """
        Update an existing TV channel.
        
        Args:
            channel_id: ID of the channel to update
            channel_data: Dictionary with updated attributes
            
        Returns:
            Updated TVChannel object or None if not found
        """
        channel = self.get_by_id(channel_id)
        if not channel:
            return None
            
        for key, value in channel_data.items():
            if hasattr(channel, key):
                setattr(channel, key, value)
                
        db.session.commit()
        return channel

    def delete(self, channel_id: int) -> bool:
        """
        Delete a TV channel.
        
        Args:
            channel_id: ID of the channel to delete
            
        Returns:
            True if deleted, False if not found
        """
        channel = self.get_by_id(channel_id)
        if not channel:
            return False
            
        # Unlink associated acestream channels
        AcestreamChannel.query.filter_by(tv_channel_id=channel_id).update({'tv_channel_id': None})
        
        # Delete the channel
        db.session.delete(channel)
        db.session.commit()
        return True

    def get_channels_with_streams(self, is_online: bool = None) -> List[Dict]:
        """
        Get TV channels with associated acestream streams.
        
        Args:
            is_online: Filter associated acestreams by online status if provided
            
        Returns:
            List of dictionaries with channel data and associated streams
        """
        result = []
        channels = self.get_all(is_active=True)
        
        for channel in channels:
            channel_dict = channel.to_dict()
            
            # Get associated acestream channels
            acestream_query = AcestreamChannel.query.filter_by(tv_channel_id=channel.id)
            if is_online is not None:
                acestream_query = acestream_query.filter_by(is_online=is_online)
                
            acestreams = acestream_query.all()
            channel_dict['acestream_channels'] = [stream.to_dict() for stream in acestreams]
            result.append(channel_dict)
            
        return result

    def assign_acestream(self, channel_id: int, acestream_id: str) -> bool:
        """
        Assign an acestream channel to a TV channel.
        
        Args:
            channel_id: TV channel ID
            acestream_id: Acestream channel ID
            
        Returns:
            True if successful, False otherwise
        """
        channel = self.get_by_id(channel_id)
        if not channel:
            return False
            
        acestream = AcestreamChannel.query.get(acestream_id)
        if not acestream:
            return False
            
        acestream.tv_channel_id = channel_id
        db.session.commit()
        return True

    def remove_acestream(self, channel_id: int, acestream_id: str) -> bool:
        """
        Remove an acestream channel from a TV channel.
        
        Args:
            channel_id: TV channel ID
            acestream_id: Acestream channel ID to remove
            
        Returns:
            True if successful, False otherwise
        """
        acestream = AcestreamChannel.query.get(acestream_id)
        if not acestream or acestream.tv_channel_id != channel_id:
            return False
            
        acestream.tv_channel_id = None
        db.session.commit()
        return True
        
    def get_categories(self) -> List[str]:
        """
        Get all unique categories used by TV channels.
        
        Returns:
            List of category strings
        """
        categories = db.session.query(TVChannel.category) \
                      .filter(TVChannel.category.isnot(None)) \
                      .distinct() \
                      .all()
        return [c[0] for c in categories]
        
    def get_countries(self) -> List[str]:
        """
        Get all unique countries used by TV channels.
        
        Returns:
            List of country strings
        """
        countries = db.session.query(TVChannel.country) \
                     .filter(TVChannel.country.isnot(None)) \
                     .distinct() \
                     .all()
        return [c[0] for c in countries]
        
    def get_languages(self) -> List[str]:
        """
        Get all unique languages used by TV channels.
        
        Returns:
            List of language strings
        """
        languages = db.session.query(TVChannel.language) \
                     .filter(TVChannel.language.isnot(None)) \
                     .distinct() \
                     .all()
        return [l[0] for l in languages]

    def set_favorite(self, channel_id: int, is_favorite: bool = True) -> Optional[TVChannel]:
        """
        Set or unset a TV channel as favorite.
        
        Args:
            channel_id: ID of the channel to update
            is_favorite: True to mark as favorite, False to unmark
            
        Returns:
            Updated TVChannel object or None if not found
        """
        channel = self.get_by_id(channel_id)
        if not channel:
            return None
            
        channel.is_favorite = is_favorite
        db.session.commit()
        return channel
        
    def set_channel_number(self, channel_id: int, channel_number: int) -> Optional[TVChannel]:
        """
        Set a channel number for a TV channel.
        
        Args:
            channel_id: ID of the channel to update
            channel_number: Channel number to set
            
        Returns:
            Updated TVChannel object or None if not found
        """
        channel = self.get_by_id(channel_id)
        if not channel:
            return None
            
        channel.channel_number = channel_number
        db.session.commit()
        return channel
    
    def toggle_favorite(self, channel_id: int) -> Optional[Dict]:
        """
        Toggle the favorite status of a TV channel.
        
        Args:
            channel_id: ID of the channel to update
            
        Returns:
            Dict with updated channel and new status or None if not found
        """
        channel = self.get_by_id(channel_id)
        if not channel:
            return None
            
        # Toggle the status
        channel.is_favorite = not channel.is_favorite
        db.session.commit()
        
        return {
            'channel': channel.to_dict(),
            'is_favorite': channel.is_favorite
        }
    
    def get_favorites(self) -> List[TVChannel]:
        """
        Get all favorite TV channels.
        
        Returns:
            List of favorite TVChannel objects
        """
        return TVChannel.query.filter_by(is_favorite=True).order_by(TVChannel.channel_number, TVChannel.name).all()

    def bulk_update(self, channel_ids: List[int], update_data: Dict) -> Dict:
        """
        Bulk update multiple TV channels at once.
        
        Args:
            channel_ids: List of TV channel IDs to update
            update_data: Dictionary with fields to update
            
        Returns:
            Dictionary with result message and count of updated channels
        """
        try:
            # Get all channels in a single query
            channels = TVChannel.query.filter(TVChannel.id.in_(channel_ids)).all()
            
            if not channels:
                return {'message': 'No matching channels found', 'updated_count': 0}
                
            # Update all channels with the same values
            for channel in channels:
                for field, value in update_data.items():
                    setattr(channel, field, value)
                    
            # Commit changes
            db.session.commit()
            
            return {
                'message': f'Successfully updated {len(channels)} channels',
                'updated_count': len(channels)
            }
        except Exception as e:
            db.session.rollback()
            raise e
