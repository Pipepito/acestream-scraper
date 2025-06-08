"""
Repository for channel data operations
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.models import AcestreamChannel, TVChannel


class ChannelRepository:
    """Repository for channel operations"""
    
    def __init__(self, db: Session):
        self.db = db
      def get_channels(self, 
                    skip: int = 0, 
                    limit: int = 100, 
                    active_only: bool = True,
                    search: Optional[str] = None) -> List[AcestreamChannel]:
        """Get channels with optional filtering"""
        query = self.db.query(AcestreamChannel)
        
        if active_only:
            query = query.filter(AcestreamChannel.is_active == True)
            
        if search:
            query = query.filter(AcestreamChannel.name.ilike(f"%{search}%"))
            
        return query.offset(skip).limit(limit).all()
        
    def get_filtered_channels(self,
                             search: Optional[str] = None,
                             group: Optional[str] = None,
                             only_online: bool = False,
                             include_groups: Optional[List[str]] = None,
                             exclude_groups: Optional[List[str]] = None) -> List[AcestreamChannel]:
        """
        Get channels with advanced filtering options
        
        Args:
            search: Optional search term for channel names
            group: Optional specific group to filter by
            only_online: Whether to include only online channels
            include_groups: Optional list of groups to include
            exclude_groups: Optional list of groups to exclude
            
        Returns:
            List of filtered channels
        """
        query = self.db.query(AcestreamChannel)
        
        # Apply filters
        if search:
            query = query.filter(AcestreamChannel.name.ilike(f"%{search}%"))
            
        if group:
            query = query.filter(AcestreamChannel.group == group)
            
        if only_online:
            query = query.filter(AcestreamChannel.is_active == True)
            
        if include_groups and len(include_groups) > 0:
            query = query.filter(AcestreamChannel.group.in_(include_groups))
            
        if exclude_groups and len(exclude_groups) > 0:
            query = query.filter(~AcestreamChannel.group.in_(exclude_groups))
            
        # Always sort by group and name
        query = query.order_by(AcestreamChannel.group, AcestreamChannel.name)
            
        return query.all()
        
    def get_unique_groups(self) -> List[str]:
        """
        Get a list of all unique channel groups
        
        Returns:
            List of group names
        """
        groups = self.db.query(AcestreamChannel.group).distinct().all()
        # Return only non-None/empty groups
        return [group[0] for group in groups if group[0]]
    
    def get_channel_by_id(self, channel_id: str) -> Optional[AcestreamChannel]:
        """Get a channel by ID"""
        return self.db.query(AcestreamChannel).filter(AcestreamChannel.channel_id == channel_id).first()
    
    def create_or_update_channel(self, 
                               channel_id: str, 
                               name: str, 
                               source_url: Optional[str] = None) -> AcestreamChannel:
        """Create a new channel or update existing one"""
        channel = self.get_channel_by_id(channel_id)
        
        if not channel:
            channel = AcestreamChannel(
                channel_id=channel_id,
                name=name,
                source_url=source_url,
                last_seen=datetime.utcnow(),
                is_active=True
            )
            self.db.add(channel)
        else:
            # Update existing channel
            channel.name = name
            channel.last_seen = datetime.utcnow()
            channel.is_active = True
            if source_url:
                channel.source_url = source_url
        
        self.db.commit()
        self.db.refresh(channel)
        return channel
    
    def get_tv_channels(self, skip: int = 0, limit: int = 100) -> List[TVChannel]:
        """Get TV channels"""
        return self.db.query(TVChannel).offset(skip).limit(limit).all()
    
    def get_tv_channel_by_name(self, name: str) -> Optional[TVChannel]:
        """Get a TV channel by name"""
        return self.db.query(TVChannel).filter(TVChannel.name == name).first()
    
    def create_tv_channel(self, name: str, logo_url: Optional[str] = None) -> TVChannel:
        """Create a new TV channel"""
        tv_channel = TVChannel(
            name=name,
            logo_url=logo_url
        )
        self.db.add(tv_channel)
        self.db.commit()
        self.db.refresh(tv_channel)
        return tv_channel
