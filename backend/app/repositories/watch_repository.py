"""Bounded catalogue reads for the independent watch-only interface."""
from datetime import datetime, timezone, timedelta
from app.models.models import AcestreamChannel, EPGProgram, EPGChannel, EPGSource, SportingEvent
from app.models.recordings import Recording, RecordingArtifact
from app.schemas.watch import WatchChannels, WatchChannel, WatchProgramme, WatchEvent, WatchRecording


class WatchRepository:
    def __init__(self, db):
        self.db = db

    def imported_stream(self, content_id):
        return self.db.query(AcestreamChannel.id).filter(AcestreamChannel.id == content_id.lower(), AcestreamChannel.is_active.is_(True)).first() is not None

    def channels(self, search='', offset=0, limit=100):
        query = self.db.query(AcestreamChannel).filter(AcestreamChannel.is_active.is_(True))
        if search:
            query = query.filter(AcestreamChannel.name.ilike('%' + search.replace('%', '\\%').replace('_', '\\_') + '%', escape='\\'))
        total = query.count()
        rows = query.order_by(AcestreamChannel.name, AcestreamChannel.id).offset(offset).limit(limit).all()
        return WatchChannels(total=total, items=[WatchChannel(id=r.id, name=r.name or r.id, category=r.group,
            tv_channel_id=r.tv_channel_id, online=r.is_online) for r in rows])

    def guide(self, offset=0):
        now = datetime.now(timezone.utc)
        rows = self.db.query(EPGProgram, EPGChannel.name).join(EPGChannel).join(EPGSource, EPGChannel.epg_source_id == EPGSource.id).filter(EPGSource.enabled.is_(True), EPGProgram.end_time > now,
            EPGProgram.start_time < now + timedelta(days=1)).order_by(EPGProgram.start_time, EPGProgram.id).offset(offset).limit(100).all()
        return [WatchProgramme(id=p.id, channel=name, title=p.title, start=p.start_time, end=p.end_time) for p, name in rows]

    def events(self, offset=0):
        rows = self.db.query(SportingEvent).filter(SportingEvent.archived.is_(False)).order_by(SportingEvent.id).offset(offset).limit(100).all()
        result = []
        for row in rows:
            fields = {**row.fields, **(row.correction or {})}
            result.append(WatchEvent(id=row.id, title=fields.get('title', 'Event'), starts_at=fields.get('starts_at'),
                competition=fields.get('competition', ''), state=fields.get('state', '')))
        return result

    def recordings(self, offset=0):
        rows = self.db.query(Recording).filter(Recording.state.in_(('completed', 'partial'))).order_by(Recording.created_at.desc()).offset(offset).limit(100).all()
        ids = [r.id for r in rows]
        files = self.db.query(RecordingArtifact.recording_id, RecordingArtifact.id).filter(RecordingArtifact.recording_id.in_(ids), RecordingArtifact.state == 'ready').all()
        return [WatchRecording(id=r.id, title=r.snapshot.get('title', 'Recording'), channel=r.snapshot.get('channel_name', ''),
            state=r.state, files=[fid for rid, fid in files if rid == r.id]) for r in rows]
