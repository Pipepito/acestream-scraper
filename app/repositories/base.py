import logging
from typing import TypeVar, Generic, Type, Optional, List
from sqlalchemy.exc import SQLAlchemyError
from ..extensions import db

T = TypeVar('T')
logger = logging.getLogger(__name__)

class BaseRepository(Generic[T]):
    """Base repository implementing common database operations."""
    
    def __init__(self, model_class: Type[T]):
        self.model = model_class
        self._db = db
    
    def get_all(self) -> List[T]:
        """Get all records."""
        return self.model.query.all()
    
    def get_by_id(self, id) -> Optional[T]:
        """Get a record by ID."""
        return self.model.query.get(id)
    
    def add(self, entity: T) -> T:
        """Add a new record."""
        try:
            self._db.session.add(entity)
            self._db.session.commit()
            return entity
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error adding entity: {e}")
            raise
    
    def update(self, entity: T) -> T:
        """Update an existing record."""
        try:
            self._db.session.add(entity)
            self._db.session.commit()
            return entity
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error updating entity: {e}")
            raise
    
    def delete(self, entity: T) -> bool:
        """Delete a record."""
        try:
            self._db.session.delete(entity)
            self._db.session.commit()
            return True
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error deleting entity: {e}")
            return False
    
    def commit(self):
        """Commit changes to the database."""
        try:
            self._db.session.commit()
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error committing changes: {e}")
            raise