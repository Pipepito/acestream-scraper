from datetime import datetime
from app.extensions import db

class EPGSource(db.Model):
    """Model for storing EPG guide URLs."""
    __tablename__ = 'epg_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(100), nullable=True)
    enabled = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    error_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f"<EPGSource {self.id}: {self.name or self.url}>"
        
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'name': self.name,
            'enabled': self.enabled,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'error_count': self.error_count,
            'last_error': self.last_error
        }