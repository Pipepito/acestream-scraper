from datetime import datetime
from ..extensions import db

class AcestreamChannel(db.Model):
    """Model for storing acestream channels."""
    __tablename__ = 'acestream_channels'

    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_processed = db.Column(db.DateTime)
    status = db.Column(db.String(32), default='active')
    source_url = db.Column(db.Text, db.ForeignKey('scraped_urls.url'))  # Add this line
    
    def __repr__(self):
        return f'<AcestreamChannel {self.name or self.id}>'
    
    @property
    def is_active(self):
        return self.status == 'active'

class ScrapedURL(db.Model):
    """Model for tracking scraped URLs."""
    __tablename__ = 'scraped_urls'

    url = db.Column(db.Text, primary_key=True)
    status = db.Column(db.String(32))
    last_processed = db.Column(db.DateTime)
    error_count = db.Column(db.Integer, default=0)  # New field to track errors
    last_error = db.Column(db.Text)  # New field to store error messages
    
    def __repr__(self):
        return f'<ScrapedURL {self.url}>'
    
    def update_status(self, status: str, error: str = None):
        """Update URL status and error information."""
        self.status = status
        self.last_processed = datetime.utcnow()
        
        if error:
            self.error_count += 1
            self.last_error = error
        else:
            self.error_count = 0
            self.last_error = None