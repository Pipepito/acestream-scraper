from datetime import datetime
from app.extensions import db

class EPGChannel(db.Model):
    """Model for storing channel info from EPG XML sources."""
    __tablename__ = 'epg_channels'
    
    id = db.Column(db.Integer, primary_key=True)
    epg_source_id = db.Column(db.Integer, db.ForeignKey('epg_sources.id'), nullable=False)
    channel_xml_id = db.Column(db.String(255), nullable=False)  # Original ID from XML
    name = db.Column(db.String(255), nullable=False)
    icon_url = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define composite unique constraint on source_id and channel_xml_id
    __table_args__ = (
        db.UniqueConstraint('epg_source_id', 'channel_xml_id', name='_epg_source_channel_uc'),
    )
    
    # Relationships
    epg_source = db.relationship('EPGSource', backref='epg_channels', lazy=True)
    
    def __repr__(self):
        return f"<EPGChannel {self.id}: {self.name} ({self.channel_xml_id})>"
        
    def to_dict(self):
        return {
            'id': self.id,
            'epg_source_id': self.epg_source_id,
            'channel_xml_id': self.channel_xml_id,
            'name': self.name,
            'icon_url': self.icon_url,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
