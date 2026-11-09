"""Logical channel inventory; programmes retain their source membership IDs."""
from sqlalchemy import func
from app.models.models import EPGChannel, EPGChannelIdentity, EPGSource


def normalized_name(value):
    # Keep accents, country/region and quality suffixes; only case/spacing differ.
    return ' '.join(value.casefold().split())


class EPGInventoryRepository:
    def __init__(self, db):
        self.db = db

    def identity(self, xml_id, name):
        normalized = normalized_name(name)
        row = self.db.query(EPGChannelIdentity).filter_by(channel_xml_id=xml_id, normalized_name=normalized).first()
        if row is None:
            row = EPGChannelIdentity(channel_xml_id=xml_id, normalized_name=normalized)
            self.db.add(row)
            self.db.flush()
        return row.id

    def page(self, source_id, skip, limit):
        # Unmigrated/test-created memberships remain individually addressable.
        key = func.coalesce(EPGChannel.identity_id, -EPGChannel.id)
        query = self.db.query(func.min(EPGChannel.id).label('id'))
        if source_id is not None:
            query = query.filter(EPGChannel.epg_source_id == source_id)
        grouped = query.group_by(key).subquery()
        total = self.db.query(func.count()).select_from(grouped).scalar()
        rows = (self.db.query(EPGChannel).join(grouped, grouped.c.id == EPGChannel.id)
                .order_by(EPGChannel.name, EPGChannel.id).offset(skip).limit(limit).all())
        self.attach_sources(rows)
        return rows, total

    def count(self):
        return self.db.query(func.count(func.distinct(func.coalesce(EPGChannel.identity_id, -EPGChannel.id)))).scalar()

    def attach_sources(self, channels):
        identities = {row.identity_id for row in channels if row.identity_id is not None}
        ids = {row.id for row in channels if row.identity_id is None}
        if not channels:
            return
        rows = (self.db.query(EPGChannel, EPGSource).join(EPGSource)
                .filter(EPGChannel.identity_id.in_(identities) | EPGChannel.id.in_(ids))
                .order_by(EPGSource.name, EPGSource.id, EPGChannel.id).all())
        grouped = {}
        for member, source in rows:
            key = ('identity', member.identity_id) if member.identity_id is not None else ('member', member.id)
            grouped.setdefault(key, []).append(dict(channel_id=member.id, source_id=source.id,
                name=source.name, enabled=bool(source.enabled)))
        for row in channels:
            key = ('identity', row.identity_id) if row.identity_id is not None else ('member', row.id)
            row.sources = grouped.get(key, [])
