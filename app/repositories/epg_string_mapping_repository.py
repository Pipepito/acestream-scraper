from typing import List, Optional
from app.models.epg_string_mapping import EPGStringMapping
from app.extensions import db

class EPGStringMappingRepository:
    def get_all(self) -> List[EPGStringMapping]:
        """Get all string pattern mappings."""
        return EPGStringMapping.query.all()
    
    def get_by_id(self, id: int) -> Optional[EPGStringMapping]:
        """Get string mapping by ID."""
        return EPGStringMapping.query.get(id)
    
    def create(self, mapping: EPGStringMapping) -> EPGStringMapping:
        """Create a new string mapping."""
        db.session.add(mapping)
        db.session.commit()
        return mapping
    
    def update(self, mapping: EPGStringMapping) -> EPGStringMapping:
        """Update an existing string mapping."""
        db.session.commit()
        return mapping
    
    def delete(self, mapping: EPGStringMapping) -> None:
        """Delete a string mapping."""
        db.session.delete(mapping)
        db.session.commit()