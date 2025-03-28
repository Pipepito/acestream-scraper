from datetime import datetime, timezone
from app.extensions import db
import uuid

class ScrapedURL(db.Model):
    """Model for tracking scraped URLs."""
    __tablename__ = 'scraped_urls'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url = db.Column(db.String(500), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')
    last_processed = db.Column(db.DateTime, nullable=True)
    error_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.String(500), nullable=True)
    enabled = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    url_type = db.Column(db.String(20), default='regular')  # 'regular', 'zeronet', etc.
    
    channels = db.relationship('AcestreamChannel', backref='source', lazy='dynamic')
    
    def __repr__(self):
        return f'<ScrapedURL {self.url}>'
    
    def update_status(self, status, error=None):
        """Update the URL status and error information."""
        self.status = status
        self.last_processed = datetime.now(timezone.utc)
        
        if status == 'failed' or status == 'error':
            self.error_count += 1
            self.last_error = error