"""DB-only access for event ingestion and reviewed edits."""
from datetime import datetime, timezone
import hashlib
import json

from sqlalchemy import select, update, delete
from app.models.models import (SportingEvent, EventObservationRecord, EventMedia, EventBroadcasterAlias,
    AcestreamChannel, TVChannel, EPGChannel, EPGSource, EPGProgram)


def alias_key(source_id, normalized_label):
    return hashlib.sha256(json.dumps([source_id, normalized_label]).encode()).hexdigest()[:32]


class EventRepository:
    def __init__(self, db):
        self.db = db

    def aliases_for(self, source_ids):
        ids = list(source_ids)
        if not ids:
            return {}
        rows = self.db.scalars(select(EventBroadcasterAlias).where(EventBroadcasterAlias.source_id.in_(ids)))
        return {(row.source_id, row.normalized_label): row for row in rows}

    def alias(self, source_id, normalized_label):
        return self.db.get(EventBroadcasterAlias, alias_key(source_id, normalized_label))

    def alias_by_id(self, alias_id):
        return self.db.get(EventBroadcasterAlias, alias_id)

    def list_aliases(self):
        return list(self.db.scalars(select(EventBroadcasterAlias).order_by(
            EventBroadcasterAlias.source_id, EventBroadcasterAlias.normalized_label)))

    def upsert_alias(self, source_id, label, normalized_label, target):
        now = datetime.now(timezone.utc)
        row = self.alias(source_id, normalized_label)
        if row is None:
            row = EventBroadcasterAlias(id=alias_key(source_id, normalized_label), source_id=source_id, label=label,
                                        normalized_label=normalized_label, target=target, created_at=now, updated_at=now)
            self.db.add(row)
        else:
            row.label, row.target, row.updated_at = label, target, now
        self.db.flush()
        return row

    def delete_alias(self, alias_id):
        row = self.db.get(EventBroadcasterAlias, alias_id)
        if row is None:
            return False
        self.db.delete(row)
        self.db.flush()
        return True

    def clear_event_entries(self, source_id, normalized_label, normalize):
        """Drop per-event entries for this source's broadcasts whose normalized label matches.

        ``normalize(label) -> str`` is supplied by the service so this layer stays free of
        name rules. Returns the number of events changed; nothing is committed here.
        """
        by_event = {}
        for obs in self.db.scalars(select(EventObservationRecord).where(EventObservationRecord.source_id == source_id)):
            by_event.setdefault(obs.event_id, []).append(obs)
        changed = 0
        for event_id, rows in by_event.items():
            event = self.db.get(SportingEvent, event_id)
            if not event or not event.broadcast_mappings:
                continue
            keys = {f'{obs.id}:{b["id"]}' for obs in rows for b in obs.payload['broadcasts']
                    if normalize(b.get('label') or '') == normalized_label}
            remaining = {key: value for key, value in event.broadcast_mappings.items() if key not in keys}
            if len(remaining) != len(event.broadcast_mappings):
                # JSON mutations must be assigned as a fresh value.
                event.broadcast_mappings = remaining or None
                changed += 1
        self.db.flush()
        return changed

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
