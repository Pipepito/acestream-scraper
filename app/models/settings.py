from sqlalchemy import Column, String
from app.extensions import db
from datetime import datetime


class Setting(db.Model):
    """Model for storing application settings."""
    
    __tablename__ = 'settings'
    
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'