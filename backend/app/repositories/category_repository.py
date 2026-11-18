"""Bounded database reads/claims for category browsing; no classifier or image IO."""
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from app.models.models import TVChannel, EPGChannel, EPGProgram, EPGSource, EPGProgramCategory
from app.repositories.channel_repository import ChannelRepository


class CategoryRepository:
    def __init__(self, db):
        self.db = db

    def catalogue(self, filters):
        query = ChannelRepository(self.db).filtered_tv_query(filters)
        from sqlalchemy.orm import load_only
        rows = query.options(load_only(TVChannel.id, TVChannel.category, TVChannel.epg_id,
                                      TVChannel.epg_source_id)).order_by(TVChannel.id).limit(50_001).all()
        if len(rows) > 50_000:
            raise ValueError('Category catalogue exceeds 50000 channels; narrow the filters')
        return rows

    def selected_channels(self, ids):
        return self.db.query(TVChannel).filter(TVChannel.id.in_(ids)).options(
            selectinload(TVChannel.acestream_channels)).order_by(TVChannel.id).all()

    def guide_lookup(self, channels, *, enabled_only=False):
        source_ids = {c.epg_source_id for c in channels if c.epg_source_id is not None}
        xml_ids = {c.epg_id for c in channels if c.epg_id}
        if not source_ids or not xml_ids:
            return {}
        query = self.db.query(EPGChannel).filter(EPGChannel.epg_source_id.in_(source_ids), EPGChannel.channel_xml_id.in_(xml_ids))
        if enabled_only:
            query = query.join(EPGSource).filter(EPGSource.enabled.is_(True))
        result = {}
        for row in query.order_by(EPGChannel.id):
            key = row.epg_source_id, row.channel_xml_id
            # Conflicting guide identities are never resolved by first row.
            result[key] = None if key in result else row
        return result

    def programmes(self, guide_ids, lower, upper, *, limit=100_000):
        result = []
        for offset in range(0, len(guide_ids), 400):
            rows = self.db.query(EPGProgram).filter(EPGProgram.epg_channel_id.in_(guide_ids[offset:offset + 400]),
                EPGProgram.start_time < upper, EPGProgram.end_time > lower).order_by(
                    EPGProgram.epg_channel_id, EPGProgram.start_time, EPGProgram.id).limit(limit + 1 - len(result)).all()
            result.extend(rows)
            if len(result) > limit:
                raise ValueError('Guide category window exceeds its limit; narrow the channel selection')
        return result

    def claim(self, channel_id, revision=None):
        query = self.db.query(TVChannel).filter(TVChannel.id == channel_id)
        if revision is not None:
            query = query.filter(TVChannel.category_revision == revision)
        if query.update({TVChannel.category_revision: TVChannel.category_revision}, synchronize_session=False) != 1:
            raise ValueError('Channel category changed; reload and review again')
        self.db.expire_all()

    def coverage(self, source_id, lower, upper, skip, limit):
        query = self.db.query(EPGProgramCategory.label, EPGChannel.epg_source_id,
            func.count(EPGProgramCategory.program_id.distinct()), func.count(EPGProgram.epg_channel_id.distinct())).join(
                EPGProgram, EPGProgram.id == EPGProgramCategory.program_id).join(EPGChannel).filter(
                EPGProgram.start_time < upper, EPGProgram.end_time > lower)
        if source_id is not None:
            query = query.filter(EPGChannel.epg_source_id == source_id)
        query = query.group_by(EPGProgramCategory.label, EPGChannel.epg_source_id)
        return query.count(), query.order_by(func.count(EPGProgramCategory.program_id.distinct()).desc(),
                                            EPGChannel.epg_source_id, EPGProgramCategory.label).offset(skip).limit(limit).all()
