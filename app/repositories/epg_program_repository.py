from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import and_, or_
from app.extensions import db
from app.models.epg_program import EPGProgram
from sqlalchemy.dialects.sqlite import insert
import logging

logger = logging.getLogger(__name__)

class EPGProgramRepository:
    """Repository for managing EPG program data."""
    
    def create(self, program_data: Dict[str, Any]) -> EPGProgram:
        """Create a new EPG program."""
        program = EPGProgram(**program_data)
        db.session.add(program)
        db.session.commit()
        return program
    
    def bulk_insert(self, programs_data: List[Dict[str, Any]]) -> int:
        """Bulk insert EPG programs for better performance."""
        try:
            if not programs_data:
                return 0
            
            # SQLite-specific upsert (INSERT OR REPLACE)
            # This will replace any existing records that would violate the unique constraint
            stmt = insert(EPGProgram).prefix_with('OR REPLACE')
            db.session.execute(stmt, programs_data)
            db.session.commit()
            
            logger.info(f"Bulk inserted {len(programs_data)} EPG programs")
            return len(programs_data)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error in bulk_insert: {str(e)}")
            raise
    
    def get_by_id(self, program_id: int) -> Optional[EPGProgram]:
        """Get program by ID."""
        return EPGProgram.query.get(program_id)
    
    def get_programs_for_channel(self, epg_channel_id: int, start_time: datetime = None, end_time: datetime = None) -> List[EPGProgram]:
        """Get all programs for a specific EPG channel within a time range."""
        query = EPGProgram.query.filter(EPGProgram.epg_channel_id == epg_channel_id)
        
        if start_time:
            query = query.filter(EPGProgram.end_time > start_time)
        
        if end_time:
            query = query.filter(EPGProgram.start_time < end_time)
        
        return query.order_by(EPGProgram.start_time).all()
    
    def get_current_program(self, epg_channel_id: int, current_time: datetime = None) -> Optional[EPGProgram]:
        """Get the current program for a channel."""
        if current_time is None:
            current_time = datetime.utcnow()
        
        return EPGProgram.query.filter(
            EPGProgram.epg_channel_id == epg_channel_id,
            EPGProgram.start_time <= current_time,
            EPGProgram.end_time > current_time
        ).first()
    
    def delete_by_channel_id(self, epg_channel_id: int) -> int:
        """Delete all programs for a specific EPG channel."""
        count = EPGProgram.query.filter(EPGProgram.epg_channel_id == epg_channel_id).count()
        EPGProgram.query.filter(EPGProgram.epg_channel_id == epg_channel_id).delete()
        db.session.commit()
        return count
    
    def delete_by_source_id(self, epg_source_id: int) -> int:
        """Delete all programs for channels from a specific EPG source."""
        from app.models.epg_channel import EPGChannel
        from sqlalchemy import select
        
        # First get the list of channel IDs from the source
        channel_ids = db.session.query(EPGChannel.id).filter(
            EPGChannel.epg_source_id == epg_source_id
        ).all()
        channel_ids = [c[0] for c in channel_ids]
        
        if not channel_ids:
            return 0
        
        # Count programs
        count = EPGProgram.query.filter(
            EPGProgram.epg_channel_id.in_(channel_ids)
        ).count()
        
        # Delete programs for these channels
        EPGProgram.query.filter(
            EPGProgram.epg_channel_id.in_(channel_ids)
        ).delete(synchronize_session=False)
        
        db.session.commit()
        return count
    
    def delete_old_programs(self, cutoff_date: datetime) -> int:
        """Delete programs older than the cutoff date."""
        count = EPGProgram.query.filter(EPGProgram.end_time < cutoff_date).count()
        EPGProgram.query.filter(EPGProgram.end_time < cutoff_date).delete()
        db.session.commit()
        return count
    
    def get_programs_count_by_channel(self, epg_channel_id: int) -> int:
        """Get the count of programs for a specific channel."""
        return EPGProgram.query.filter(EPGProgram.epg_channel_id == epg_channel_id).count()
    
    def update(self, program: EPGProgram) -> EPGProgram:
        """Update an existing program."""
        program.updated_at = datetime.utcnow()
        db.session.commit()
        return program
    
    def delete(self, program: EPGProgram) -> bool:
        """Delete a specific program."""
        try:
            db.session.delete(program)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting program {program.id}: {str(e)}")
            return False
