"""Inventory reads for reviewed and automatic guide matching."""
from sqlalchemy.orm import selectinload
from app.models.models import AcestreamChannel, EPGChannel, EPGSource, TVChannel


class EPGMatchRepository:
    def __init__(self, db):
        self.db = db

    def guide_query(self, source_id=None):
        query = self.db.query(EPGChannel).join(EPGSource).filter(EPGSource.enabled.is_(True))
        if source_id is not None:
            query = query.filter(EPGChannel.epg_source_id == source_id)
        return query

    def stream_query(self):
        return self.db.query(AcestreamChannel).filter(
            AcestreamChannel.tv_channel_id.is_(None),
            AcestreamChannel.is_active.is_(True),
            AcestreamChannel.epg_update_protected.is_not(True),
        )

    def imported_guide_ids(self):
        # Identity constraints span every imported source, including disabled
        # sources and sources outside the user's current preview filter.
        return {xml_id for (xml_id,) in self.db.query(EPGChannel.channel_xml_id).distinct()
                if xml_id}

    def inventory(self, source_id, budget):
        guides, streams = self.guide_query(source_id), self.stream_query()
        if guides.count() * streams.count() > budget:
            raise ValueError('Channel inventory exceeds the guide matching comparison budget.')
        return (guides.options(selectinload(EPGChannel.epg_source)).order_by(EPGChannel.id).all(),
                streams.order_by(AcestreamChannel.id).all(),
                self.db.query(TVChannel).all())

    def coverage(self):
        from sqlalchemy import and_, func
        linked = (self.db.query(func.count(func.distinct(AcestreamChannel.id)))
                  .join(TVChannel, AcestreamChannel.tv_channel_id == TVChannel.id)
                  .join(EPGChannel, and_(EPGChannel.epg_source_id == TVChannel.epg_source_id,
                                        EPGChannel.channel_xml_id == TVChannel.epg_id))
                  .join(EPGSource, EPGSource.id == EPGChannel.epg_source_id)
                  .filter(EPGSource.enabled.is_(True), TVChannel.is_active.is_(True)).scalar())
        return {'streams': self.db.query(AcestreamChannel).count(),
                'linked_streams': linked,
                'guide_channels': self.guide_query().count()}
