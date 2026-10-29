"""DB-only DVR operations. Caller owns commit/rollback."""
from sqlalchemy import select
from app.models.models import EPGChannel, EPGProgram, EPGSource, TVChannel, Setting
from app.models.recordings import Recording, RecordingArtifact, RecordingAttempt
from app.repositories.import_exclusion_repository import ImportExclusionRepository

PENDING = ('scheduled', 'starting', 'recording', 'recovering', 'finalizing')


class RecordingRepository:
    def __init__(self, db):
        self.db = db

    def claim(self):
        ImportExclusionRepository(self.db).claim()

    def get(self, rid):
        return self.db.get(Recording, rid)

    def by_key(self, key):
        return self.db.scalar(select(Recording).where(Recording.idempotency_key == key))

    def pending(self):
        return self.db.query(Recording).filter(Recording.state.in_(PENDING)).order_by(Recording.start_time, Recording.id).all()

    def list(self, state=None, search=None, tv_channel_id=None):
        query = self.db.query(Recording)
        if state:
            query = query.filter(Recording.state == state)
        if search:
            query = query.filter(Recording.snapshot['title'].as_string().ilike('%' + search.replace('%', '\\%').replace('_', '\\_') + '%', escape='\\'))
        if tv_channel_id:
            query = query.filter(Recording.tv_channel_id == tv_channel_id)
        return query.order_by(Recording.created_at.desc(), Recording.id)

    def files(self, rid):
        return self.db.query(RecordingArtifact).outerjoin(RecordingAttempt, RecordingArtifact.attempt_id == RecordingAttempt.id).filter(RecordingArtifact.recording_id == rid).order_by(RecordingAttempt.ordinal.asc().nullslast(), RecordingArtifact.id).all()

    def attempts(self, rid):
        return self.db.query(RecordingAttempt).filter_by(recording_id=rid).order_by(RecordingAttempt.ordinal).all()

    def file(self, rid, fid):
        return self.db.scalar(select(RecordingArtifact).where(RecordingArtifact.id == fid, RecordingArtifact.recording_id == rid))

    def channel(self, cid):
        return self.db.get(TVChannel, cid)

    def programme(self, pid):
        return self.db.query(EPGProgram, EPGChannel, EPGSource).select_from(EPGProgram).join(EPGChannel, EPGProgram.epg_channel_id == EPGChannel.id).join(EPGSource, EPGChannel.epg_source_id == EPGSource.id).filter(EPGProgram.id == pid).first()

    def setting(self, key, default=None):
        row = self.db.query(Setting).filter_by(key=key).first()
        return row.value if row else default

    def set_setting(self, key, value):
        row = self.db.query(Setting).filter_by(key=key).first()
        if row is None:
            row = Setting(key=key)
            self.db.add(row)
        row.value = value

    def current_programme(self, cid, now):
        channel = self.channel(cid)
        if channel is None:
            return None
        rows = self.db.query(EPGProgram).join(EPGChannel).filter(
            EPGChannel.epg_source_id == channel.epg_source_id, EPGChannel.channel_xml_id == channel.epg_id,
            EPGProgram.start_time <= now, EPGProgram.end_time > now).limit(2).all()
        return rows[0] if len(rows) == 1 else None
