from typing import List, Optional
from datetime import datetime
from app.models.epg_source import EPGSource
from app.extensions import db

class EPGSourceRepository:
    def get_all(self) -> List[EPGSource]:
        """Get all EPG sources."""
        return EPGSource.query.all()
    
    def get_enabled(self) -> List[EPGSource]:
        """Get all enabled EPG sources."""
        return EPGSource.query.filter_by(enabled=True).all()
    
    def get_by_id(self, id: int) -> Optional[EPGSource]:
        """Get EPG source by ID."""
        return EPGSource.query.get(id)
    
    def create(self, source: EPGSource) -> EPGSource:
        """Create a new EPG source."""
        db.session.add(source)
        db.session.commit()
        return source
    
    def update(self, source: EPGSource) -> EPGSource:
        """Update an existing EPG source."""
        db.session.commit()
        return source
    
    def delete(self, source: EPGSource) -> None:
        """Delete an EPG source."""
        db.session.delete(source)
        db.session.commit()
    
    def toggle_enabled(self, source: EPGSource) -> EPGSource:
        """Toggle enabled status of an EPG source."""
        source.enabled = not source.enabled
        db.session.commit()
        return source
    
    def update_last_updated(self, source: EPGSource) -> EPGSource:
        """Update last_updated timestamp."""
        source.last_updated = datetime.utcnow()
        db.session.commit()
        return source