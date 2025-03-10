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
    source_url = db.Column(db.Text, db.ForeignKey('scraped_urls.url'))
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