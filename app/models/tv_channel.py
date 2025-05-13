from datetime import datetime
from sqlalchemy.sql import func
from app.extensions import db

class TVChannel(db.Model):
    """Model for storing TV channels that can have multiple Acestream streams."""
    __tablename__ = 'tv_channels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    logo_url = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(128), nullable=True)
    country = db.Column(db.String(128), nullable=True)
    language = db.Column(db.String(128), nullable=True)
    website = db.Column(db.Text, nullable=True)
    epg_id = db.Column(db.String(256), nullable=True)
    epg_source_id = db.Column(db.Integer, db.ForeignKey('epg_sources.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)
    channel_number = db.Column(db.Integer, nullable=True)
    
    # Relationships
    acestream_channels = db.relationship('AcestreamChannel', backref='tv_channel', lazy='dynamic')
    epg_source = db.relationship('EPGSource', backref='tv_channels', lazy=True)
    
    def __repr__(self):
        return f'<TVChannel {self.name}>'
        
    def to_dict(self):
        """Convert the TV channel to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'logo_url': self.logo_url,
            'category': self.category,
            'country': self.country,
            'language': self.language,
            'website': self.website,
            'epg_id': self.epg_id,
            'epg_source_id': self.epg_source_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'is_favorite': self.is_favorite,
            'channel_number': self.channel_number,
            'acestream_channels_count': self.acestream_channels.count()
        }
