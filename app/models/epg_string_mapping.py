from app.extensions import db

class EPGStringMapping(db.Model):
    """Model for mapping text patterns to EPG channel IDs."""
    __tablename__ = 'epg_string_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    search_pattern = db.Column(db.String(255), nullable=False, unique=True)
    epg_channel_id = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f"<EPGStringMapping {self.id}: '{self.search_pattern}' -> {self.epg_channel_id}>"
        
    def to_dict(self):
        return {
            'id': self.id,
            'search_pattern': self.search_pattern,
            'epg_channel_id': self.epg_channel_id
        }