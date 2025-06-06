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
    source_url = Column(String(2048), nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship with TVChannel
    tv_channel_id = Column(Integer, ForeignKey("tv_channels.id"), nullable=True)
    tv_channel = relationship("TVChannel", back_populates="acestream_channels")


class TVChannel(Base):
    """Model for TV channels"""
    __tablename__ = "tv_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    logo_url = Column(String(2048), nullable=True)
    
    # Relationships
    acestream_channels = relationship("AcestreamChannel", back_populates="tv_channel")
    epg_channels = relationship("EPGChannel", back_populates="tv_channel")
