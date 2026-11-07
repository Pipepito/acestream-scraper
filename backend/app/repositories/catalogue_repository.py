"""Catalogue persistence and optimistic revision ownership."""
from sqlalchemy import update
from app.models.models import W3UCatalogue


class CatalogueRepository:
    def __init__(self, db):
        self.db = db

    def get(self, catalogue_id):
        return self.db.get(W3UCatalogue, catalogue_id)

    def list(self):
        return self.db.query(W3UCatalogue.id, W3UCatalogue.name, W3UCatalogue.revision,
            W3UCatalogue.source_url, W3UCatalogue.snapshot['partial'].as_boolean().label('partial'),
            W3UCatalogue.refresh_enabled, W3UCatalogue.updated_at).order_by(W3UCatalogue.id).all()

    def enabled_ids(self):
        return [row[0] for row in self.db.query(W3UCatalogue.id).filter(
            W3UCatalogue.refresh_enabled.is_(True), W3UCatalogue.source_url.isnot(None)).all()]

    def save(self, catalogue_id, expected_revision, values):
        if catalogue_id is None:
            row = W3UCatalogue(**values, revision=1)
            self.db.add(row)
            self.db.flush()
            return row
        changed = self.db.execute(update(W3UCatalogue).where(
            W3UCatalogue.id == catalogue_id, W3UCatalogue.revision == expected_revision
        ).values(**values, revision=expected_revision + 1))
        if changed.rowcount != 1:
            raise ValueError('Catalogue changed or was removed. Preview it again before saving.')
        self.db.expire_all()
        return self.get(catalogue_id)

    def delete(self, catalogue_id):
        row = self.get(catalogue_id)
        if row is None:
            return False
        self.db.delete(row)
        self.db.commit()
        return True


    def reserve_event_revision(self, catalogue_id, expected_revision, source_id):
        changed = self.db.execute(update(W3UCatalogue).where(
            W3UCatalogue.id == catalogue_id, W3UCatalogue.revision == expected_revision,
            W3UCatalogue.snapshot['_event_source_id'].as_string() == source_id
        ).values(revision=expected_revision + 1))
        if changed.rowcount != 1:
            raise ValueError('Catalogue changed or was removed. Preview the event again.')
        self.db.expire_all()
