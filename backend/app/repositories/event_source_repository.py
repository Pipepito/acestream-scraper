"""Persistence for schedule refresh and retention settings."""
from sqlalchemy import select, update, delete
from app.models.models import EventScheduleSource, SportingEvent, EventObservationRecord, EventMedia, Setting


class EventSourceRepository:
    def __init__(self, db):
        self.db = db

    def all(self):
        return list(self.db.scalars(select(EventScheduleSource).order_by(EventScheduleSource.name, EventScheduleSource.id)))

    def get(self, source_id):
        return self.db.get(EventScheduleSource, source_id)

    def by_identity(self, identity):
        return self.db.scalar(select(EventScheduleSource).where(EventScheduleSource.source_identity == identity))

    def update(self, source_id, revision, **values):
        result = self.db.execute(update(EventScheduleSource).where(
            EventScheduleSource.id == source_id, EventScheduleSource.revision == revision
        ).values(revision=revision + 1, **values).execution_options(synchronize_session=False))
        if result.rowcount != 1:
            raise ValueError('Schedule source changed; review it again')

    def delete(self, source_id, revision):
        result = self.db.execute(delete(EventScheduleSource).where(
            EventScheduleSource.id == source_id, EventScheduleSource.revision == revision))
        if result.rowcount != 1:
            raise ValueError('Schedule source changed; reload before deleting')

    def observations(self, identity):
        return list(self.db.scalars(select(EventObservationRecord).where(EventObservationRecord.source_id == identity)))

    def retention(self):
        return self.db.scalar(select(Setting).where(Setting.key == 'event_retention'))

    def save_retention(self, value):
        setting = self.retention()
        if setting:
            setting.value = value
        else:
            self.db.add(Setting(key='event_retention', value=value))

    def delete_event(self, event_id):
        observations = list(self.db.scalars(select(EventObservationRecord).where(EventObservationRecord.event_id == event_id)))
        for row in observations:
            source = self.by_identity(row.source_id)
            if source and row.external_id in source.reviewed_ids:
                source.reviewed_ids = [key for key in source.reviewed_ids if key != row.external_id]
                source.revision += 1
        observation_ids = select(EventObservationRecord.id).where(EventObservationRecord.event_id == event_id)
        self.db.execute(delete(EventMedia).where(EventMedia.observation_id.in_(observation_ids)))
        self.db.execute(delete(EventObservationRecord).where(EventObservationRecord.event_id == event_id))
        self.db.execute(delete(SportingEvent).where(SportingEvent.id == event_id))
