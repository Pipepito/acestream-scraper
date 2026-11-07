"""DB-only saved definition, execution-state and membership operations."""
from app.models.models import SavedSearch, SavedSearchChannel, _utcnow
from app.repositories.import_exclusion_repository import ImportExclusionRepository


class SavedSearchRepository:
    def __init__(self, db):
        self.db = db

    def claim(self):
        ImportExclusionRepository(self.db).claim()

    def get(self, sid):
        return self.db.get(SavedSearch, sid)

    def list(self):
        return self.db.query(SavedSearch).order_by(SavedSearch.id)

    def find_fingerprint(self, fingerprint):
        return self.db.query(SavedSearch.id).filter_by(fingerprint=fingerprint).scalar()

    def scheduled(self):
        return self.db.query(SavedSearch).filter_by(refresh_enabled=True).order_by(
            SavedSearch.last_attempt_at.asc(), SavedSearch.id).limit(100).all()

    def membership(self, sid, cid):
        row = self.db.get(SavedSearchChannel, (sid, cid))
        if row is None:
            row = SavedSearchChannel(saved_search_id=sid, channel_id=cid)
            self.db.add(row)
        row.last_discovered_at = _utcnow()

    def delete(self, row):
        self.db.query(SavedSearchChannel).filter_by(saved_search_id=row.id).delete()
        self.db.delete(row)

    def interrupt_orphans(self):
        for row in self.db.query(SavedSearch).filter(SavedSearch.run_state.in_(['waiting', 'running'])):
            row.run_state = None
            row.last_result = None
            row.last_outcome = 'interrupted'
            row.last_finished_at = _utcnow()
            row.error_code = 'interrupted'
            row.error_message = 'Application stopped before this run completed. Run again when ready.'
        self.db.commit()
