"""DB-only access for event ingestion and reviewed edits."""
from sqlalchemy import select, update, delete
from app.models.models import SportingEvent, EventObservationRecord, EventMedia, AcestreamChannel, TVChannel, EPGChannel, EPGSource, EPGProgram


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

    def target_rows(self, kind, search=None):
        if kind == 'tv':
            query = select(TVChannel.id, TVChannel.name, TVChannel.country).where(TVChannel.is_active.is_(True))
        else:
            query = select(EPGChannel.id, EPGChannel.name, EPGChannel.epg_source_id, EPGChannel.channel_xml_id,
                           EPGSource.name.label('source_name')).join(EPGSource).where(EPGSource.enabled.is_(True))
        model = TVChannel if kind == 'tv' else EPGChannel
        if search is not None:
            query = query.where(model.name.icontains(search, autoescape=True))
        return list(self.db.execute(query.order_by(model.name, model.id).limit(30 if search is not None else 20001)).mappings())

    def target(self, kind, target_id):
        if kind == 'tv':
            row = self.db.get(TVChannel, target_id)
            return dict(id=row.id, name=row.name, country=row.country) if row and row.is_active else None
        row = self.db.execute(select(EPGChannel.id, EPGChannel.name, EPGChannel.epg_source_id, EPGChannel.channel_xml_id,
                             EPGSource.name.label('source_name')).join(EPGSource)
                             .where(EPGChannel.id == target_id, EPGSource.enabled.is_(True))).mappings().first()
        return dict(row) if row else None

    def program_candidates(self, lower, upper):
        return list(self.db.execute(select(
            EPGProgram.id, EPGProgram.title, EPGProgram.subtitle, EPGProgram.start_time, EPGProgram.end_time,
            EPGProgram.epg_channel_id, EPGChannel.epg_source_id, EPGChannel.channel_xml_id,
            EPGChannel.name.label('channel_name'), EPGSource.name.label('source_name'))
            .join(EPGChannel, EPGProgram.epg_channel_id == EPGChannel.id)
            .join(EPGSource, EPGChannel.epg_source_id == EPGSource.id)
            .where(EPGSource.enabled.is_(True), EPGProgram.start_time >= lower, EPGProgram.start_time < upper)
            .order_by(EPGProgram.start_time, EPGProgram.id).limit(5001)).mappings())

    def program_tv_targets(self, source_id, xml_id):
        return list(self.db.execute(select(TVChannel.id, TVChannel.name, TVChannel.country).where(
            TVChannel.is_active.is_(True), TVChannel.epg_source_id == source_id, TVChannel.epg_id == xml_id)
            .limit(2)).mappings())

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
