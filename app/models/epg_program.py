from datetime import datetime
from app.extensions import db

class EPGProgram(db.Model):
    """Model for storing program schedule data from EPG XML sources."""
    __tablename__ = 'epg_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    epg_channel_id = db.Column(db.Integer, db.ForeignKey('epg_channels.id'), nullable=False)
    
    # Program identification
    program_xml_id = db.Column(db.String(255), nullable=True)  # Optional ID from XML
    
    # Program schedule
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    # Program details
    title = db.Column(db.String(500), nullable=False)
    subtitle = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(50), nullable=True)
    
    # Additional metadata
    episode_number = db.Column(db.String(100), nullable=True)  # Can be like "S01E05" or "1/10"
    rating = db.Column(db.String(20), nullable=True)
    icon_url = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define composite unique constraint to prevent duplicate programs
    __table_args__ = (
        db.UniqueConstraint('epg_channel_id', 'start_time', 'title', name='_epg_channel_program_uc'),
        db.Index('idx_epg_program_time_range', 'epg_channel_id', 'start_time', 'end_time'),
    )
    
    # Relationships
    epg_channel = db.relationship('EPGChannel', backref='programs', lazy=True)
    
    def __repr__(self):
        return f"<EPGProgram {self.id}: {self.title} ({self.start_time}-{self.end_time})>"
        
    def to_dict(self):
        return {
            'id': self.id,
            'epg_channel_id': self.epg_channel_id,
            'program_xml_id': self.program_xml_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'title': self.title,
            'subtitle': self.subtitle,
            'description': self.description,
            'category': self.category,
            'language': self.language,
            'episode_number': self.episode_number,
            'rating': self.rating,
            'icon_url': self.icon_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_programs_for_channel_in_range(epg_channel_id, start_time, end_time):
        """Get all programs for a channel within a time range."""
        return EPGProgram.query.filter(
            EPGProgram.epg_channel_id == epg_channel_id,
            EPGProgram.end_time > start_time,
            EPGProgram.start_time < end_time
        ).order_by(EPGProgram.start_time).all()
    
    @staticmethod
    def get_current_program_for_channel(epg_channel_id, current_time=None):
        """Get the current program for a channel."""
        if current_time is None:
            current_time = datetime.utcnow()
            
        return EPGProgram.query.filter(
            EPGProgram.epg_channel_id == epg_channel_id,
            EPGProgram.start_time <= current_time,
            EPGProgram.end_time > current_time
        ).first()
