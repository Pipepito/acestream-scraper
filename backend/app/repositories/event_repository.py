"""DB-only access for event ingestion and reviewed edits."""
from sqlalchemy import select, update, delete
from app.models.models import SportingEvent, EventObservationRecord, EventMedia, AcestreamChannel


class EventRepository:
    def __init__(self, db):
        self.db = db

    def inventory(self):
        return list(self.db.scalars(select(SportingEvent).order_by(SportingEvent.id)))

    def get(self, event_id):
        return self.db.get(SportingEvent, event_id)

    def observations(self, event_id=None):
        query = select(EventObservationRecord).order_by(EventObservationRecord.id)
        if event_id:
            query = query.where(EventObservationRecord.event_id == event_id)
        return list(self.db.scalars(query))

    def channel(self, content_id):
        return self.db.get(AcestreamChannel, content_id)

    def channels(self, content_ids):
        ids = list(content_ids)
        found = {}
        for offset in range(0, len(ids), 500):
            found.update((row.id, row) for row in self.db.scalars(
                select(AcestreamChannel).where(AcestreamChannel.id.in_(ids[offset:offset + 500]))))
        return found

    def media(self, content_id):
        return self.db.get(EventMedia, content_id)

    def retain_media(self, observation_id, content_ids):
        # Open players already own immutable source copies; removing obsolete
        # lookup records prevents future starts from using stale signed URLs.
        self.db.execute(delete(EventMedia).where(
            EventMedia.observation_id == observation_id,
            EventMedia.content_id.not_in(content_ids)))

    def reserve_revision(self, event_id, revision, **values):
        result = self.db.execute(update(SportingEvent).where(
            SportingEvent.id == event_id, SportingEvent.revision == revision
        ).values(revision=revision + 1, **values).execution_options(synchronize_session=False))
        if result.rowcount != 1:
            raise ValueError('Events changed; preview or reload before saving')

    def add(self, row):
        self.db.add(row)

    def flush(self):
        self.db.flush()

    def commit(self):
        self.db.commit()
        self.db.expire_all()

    def rollback(self):
        self.db.rollback()
