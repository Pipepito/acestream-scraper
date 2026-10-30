"""Guide identities and bounded programme snapshots for reviewed event overlays."""
import hashlib
from sqlalchemy import select
from app.models.models import EPGChannel, EPGSource, EPGProgram, TVChannel, SportingEvent


class EventOverlayRepository:
    def __init__(self, db):
        self.db = db

    def guide(self, target):
        query = select(EPGChannel).join(EPGSource).where(EPGSource.enabled.is_(True))
        if target.kind == 'epg':
            query = query.where(EPGChannel.id == target.id)
        else:
            tv = self.db.get(TVChannel, target.id)
            if not tv or not tv.is_active or not tv.epg_source_id or not tv.epg_id:
                return None
            query = query.where(EPGChannel.epg_source_id == tv.epg_source_id,
                                EPGChannel.channel_xml_id == tv.epg_id)
        row = self.db.scalar(query)
        if not row:
            return None
        source = self.db.get(EPGSource, row.epg_source_id)
        return dict(id=row.id, source_id=row.epg_source_id, xml_id=row.channel_xml_id, name=row.name,
                    source_identity=hashlib.sha256(source.url.encode()).hexdigest())

    def programmes(self, channel_id, start, end):
        return list(self.db.scalars(select(EPGProgram).where(EPGProgram.epg_channel_id == channel_id,
            EPGProgram.start_time < end, EPGProgram.end_time > start)
            .order_by(EPGProgram.start_time, EPGProgram.id).limit(501)))

    def events(self):
        return list(self.db.scalars(select(SportingEvent).where(SportingEvent.guide_overlays.is_not(None))
                                   .order_by(SportingEvent.id).limit(2001)))
