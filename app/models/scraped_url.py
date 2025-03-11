from datetime import datetime, timezone
from app.extensions import db

class ScrapedURL(db.Model):
    """Model for tracking scraped URLs."""
    __tablename__ = 'scraped_urls'

    url = db.Column(db.Text, primary_key=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_processed = db.Column(db.DateTime)
    status = db.Column(db.String(32), default='pending')
    enabled = db.Column(db.Boolean, default=True)
    error_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text)
    
    channels = db.relationship('AcestreamChannel', backref='source', lazy='dynamic')
    
    def __repr__(self):
        return f'<ScrapedURL {self.url}>'
    
    def update_status(self, status: str, error: str = None):
        """Update URL status and error information."""
        self.status = status
        self.last_processed = datetime.now(timezone.utc)
        
        if error:
            self.error_count = (self.error_count or 0) + 1
            self.last_error = error
        else:
            self.error_count = 0
            self.last_error = None