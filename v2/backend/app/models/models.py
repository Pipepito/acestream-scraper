"""
SQLAlchemy models for the application
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.config.database import Base


class ScrapedURL(Base):
    """Model for tracking URLs that have been scraped"""
    __tablename__ = "scraped_urls"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), unique=True, index=True, nullable=False)
    last_scraped = Column(DateTime, default=datetime.utcnow)
    status = Column(String(255), default="pending")
    error = Column(Text, nullable=True)
    
    def update_status(self, status: str, error: str = None) -> None:
        """Update the status of this URL"""
        self.status = status
        self.error = error
        self.last_scraped = datetime.utcnow()


class AcestreamChannel(Base):
    """Model for Acestream channels"""
    __tablename__ = "acestream_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255))
    group = Column(String(255), nullable=True, index=True)
    logo = Column(String(2048), nullable=True)
    tvg_id = Column(String(255), nullable=True)
    tvg_name = Column(String(255), nullable=True)
    source_url = Column(String(2048), nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    original_url = Column(String(2048), nullable=True)
    epg_update_protected = Column(Boolean, default=False)
    
    # Relationship with TVChannel
    tv_channel_id = Column(Integer, ForeignKey("tv_channels.id"), nullable=True)
    tv_channel = relationship("TVChannel", back_populates="acestream_channels")


class EPGSource(Base):
    """Model for EPG sources"""
    __tablename__ = "epg_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(2048), nullable=False)
    name = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)
    last_updated = Column(DateTime, nullable=True)
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # Relationships
    tv_channels = relationship("TVChannel", back_populates="epg_source")
    epg_channels = relationship("EPGChannel", back_populates="epg_source")


class TVChannel(Base):
    """Model for TV channels"""
    __tablename__ = "tv_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String(2048), nullable=True)
    category = Column(String(255), nullable=True)
    country = Column(String(255), nullable=True)
    language = Column(String(255), nullable=True)
    website = Column(String(2048), nullable=True)
    epg_id = Column(String(255), nullable=True)
    epg_source_id = Column(Integer, ForeignKey("epg_sources.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_favorite = Column(Boolean, default=False)
    channel_number = Column(Integer, nullable=True)
      # Relationships
    acestream_channels = relationship("AcestreamChannel", back_populates="tv_channel")
    epg_source = relationship("EPGSource", back_populates="tv_channels")


class EPGChannel(Base):
    """Model for EPG channels"""
    __tablename__ = "epg_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    epg_source_id = Column(Integer, ForeignKey("epg_sources.id"), nullable=False)
    channel_xml_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    icon_url = Column(String(2048), nullable=True)
    language = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    epg_source = relationship("EPGSource", back_populates="epg_channels")
    programs = relationship("EPGProgram", back_populates="epg_channel", cascade="all, delete-orphan")
    string_mappings = relationship("EPGStringMapping", back_populates="epg_channel", cascade="all, delete-orphan")


class EPGProgram(Base):
    """Model for EPG programs"""
    __tablename__ = "epg_programs"
    
    id = Column(Integer, primary_key=True, index=True)
    epg_channel_id = Column(Integer, ForeignKey("epg_channels.id"), nullable=False)
    program_xml_id = Column(String(255), nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    image_url = Column(String(2048), nullable=True)
    
    # Relationships
    epg_channel = relationship("EPGChannel", back_populates="programs")


class EPGStringMapping(Base):
    """Model for EPG string mappings"""
    __tablename__ = "epg_string_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    epg_channel_id = Column(Integer, ForeignKey("epg_channels.id"), nullable=False)
    search_pattern = Column(String(255), nullable=False)
    is_exclusion = Column(Boolean, default=False)
    
    # Relationships
    epg_channel = relationship("EPGChannel", back_populates="string_mappings")
    
    # Relationships
    acestream_channels = relationship("AcestreamChannel", back_populates="tv_channel")
    epg_channels = relationship("EPGChannel", back_populates="tv_channel")
