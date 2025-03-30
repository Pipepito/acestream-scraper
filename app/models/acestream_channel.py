from datetime import datetime
from app.extensions import db

class AcestreamChannel(db.Model):
    """Model for storing acestream channels."""
    __tablename__ = 'acestream_channels'

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_processed = db.Column(db.DateTime)
    status = db.Column(db.String(32), default='active')
    
    # Keep source_url as a text field for reference, no foreign key
    source_url = db.Column(db.Text)
    
    # Add new foreign key column for scraped_urls.id
    scraped_url_id = db.Column(db.Integer, db.ForeignKey('scraped_urls.id'), nullable=True)
    
    group = db.Column(db.String(256))
    logo = db.Column(db.Text)
    tvg_id = db.Column(db.String(256))
    tvg_name = db.Column(db.String(256))
    m3u_source = db.Column(db.Text)
    original_url = db.Column(db.Text)
    is_online = db.Column(db.Boolean, default=False)
    last_checked = db.Column(db.DateTime)
    check_error = db.Column(db.Text)
    
    def __repr__(self):
        return f'<AcestreamChannel {self.name or self.id}>'
    
    @property
    def is_active(self):
        return self.status == 'active'

    def to_dict(self):
        """Convert the channel to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'added_on': self.added_at.isoformat() if self.added_at else None,
            'last_processed': self.last_processed.isoformat() if self.last_processed else None,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'is_online': self.is_online,
            'check_error': self.check_error,
            'group': self.group,
            'source_url': self.source_url,
            'scraped_url_id': self.scraped_url_id
        }