"""Explicit XMLTV overlays, projected without changing imported EPG programmes.

Saved overlays are snapshots. A changed schedule or resolved guide identity
suspends them until reviewed again; ordinary source refreshes do not authorize a
new schedule. Export clips the underlying programme around the accepted window.
"""
from datetime import datetime, timedelta
import hashlib
import json
from types import SimpleNamespace

from app.repositories.event_overlay_repository import EventOverlayRepository
from app.schemas.events import EventOverlayPreview, EventOverlayView
from app.services.event_service import EventService


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def programme(row):
    return dict(title=row.title, starts_at=row.start_time, ends_at=row.end_time)


class EventOverlayService:
    def __init__(self, db):
        self.db = db
        self.events = EventService(db)
        self.repo = EventOverlayRepository(db)

    def context(self, event, broadcast_id):
        if event.archived or event.state in ('cancelled', 'postponed') or not event.starts_at:
            raise ValueError('Overlay needs an unarchived event with a confirmed start')
        broadcast = next((b for b in event.broadcasts if b.id == broadcast_id), None)
        if not broadcast or not broadcast.target:
            raise ValueError('Link this broadcast to an unambiguous TV or EPG channel first')
        guide = self.repo.guide(broadcast.target)
        if not guide:
            raise ValueError('This channel needs an enabled, source-qualified EPG assignment')
        snapshot = dict(guide=guide, target=broadcast.target.model_dump(),
                        title=event.title, start=event.starts_at.isoformat(),
                        end=event.ends_at.isoformat() if event.ends_at else None,
                        competition=event.competition, sport=event.sport)
        return snapshot

    def active(self, event, saved):
        try:
            return saved['context'] == self.context(event, saved['broadcast_id'])
        except ValueError:
            return False

    def list(self, event_id):
        event = self.events.get(event_id, include_epg_matches=False)
        row = self.events.repo.get(event_id)
        return [EventOverlayView(broadcast_id=s['broadcast_id'], channel=s['context']['target'],
            programme=s['programme'], active=self.active(event, s)) for s in row.guide_overlays or []]

    def active_entries(self):
        rows = self.repo.events()
        if len(rows) > 2000:
            raise ValueError('Overlay inventory exceeds its limit')
        entries = []
        for row in rows:
            if not row.guide_overlays:
                continue
            event = self.events.get(row.id, include_epg_matches=False)
            entries.extend((row.id, saved) for saved in row.guide_overlays if self.active(event, saved))
        return entries

    def prepare(self, event_id, request):
        event = self.events.get(event_id, include_epg_matches=False)
        if event.revision != request.revision:
            raise ValueError('Event changed; reload and preview the overlay again')
        context = self.context(event, request.broadcast_id)
        end = request.ends_at
        if not event.starts_at < end <= event.starts_at + timedelta(hours=12):
            raise ValueError('Choose an overlay end after start and within 12 hours')
        base = self.repo.programmes(context['guide']['id'], event.starts_at, end)
        if len(base) > 500:
            raise ValueError('Too many affected programmes; narrow the overlay window')
        for other_id, saved in self.active_entries():
            if other_id == event_id and saved['broadcast_id'] == request.broadcast_id:
                continue
            p = saved['programme']
            if saved['context']['guide'] == context['guide'] and datetime.fromisoformat(p['starts_at']) < end and datetime.fromisoformat(p['ends_at']) > event.starts_at:
                raise ValueError('Another reviewed event overlay occupies this channel and time')
        payload = dict(broadcast_id=request.broadcast_id, context=context,
                       programme=dict(title=event.title, starts_at=event.starts_at.isoformat(), ends_at=end.isoformat()))
        fingerprint = self.preview_fingerprint(payload, event.revision)
        preview = EventOverlayPreview(fingerprint=fingerprint, channel=context['target'],
            programme=payload['programme'], affected=[programme(p) for p in base])
        return payload, preview

    def preview(self, event_id, request):
        return self.prepare(event_id, request)[1]

    def apply(self, event_id, request):
        try:
            # Claim the SQLite writer before re-reading the complete preview scope.
            self.events.repo.reserve_revision(event_id, request.revision)
            self.db.expire_all()
            checked = request.model_copy(update={'revision': request.revision + 1})
            payload, _ = self.prepare(event_id, checked)
            # Compare using the reviewed revision; the write claim itself isn't a change.
            row = self.events.repo.get(event_id)
            # Fingerprint computation is independent of the reservation revision.
            if request.expected_fingerprint != self.preview_fingerprint(payload, request.revision):
                raise ValueError('Guide or event changed; preview the overlay again')
            saved = [s for s in row.guide_overlays or [] if s['broadcast_id'] != request.broadcast_id]
            if len(saved) >= 50:
                raise ValueError('At most 50 overlays per event')
            row.guide_overlays = [*saved, payload]
            self.db.commit()
            self.db.expire_all()
            return self.list(event_id)
        except Exception:
            self.db.rollback()
            raise

    def preview_fingerprint(self, payload, revision):
        p = payload['programme']
        base = self.repo.programmes(payload['context']['guide']['id'],
                                   datetime.fromisoformat(p['starts_at']), datetime.fromisoformat(p['ends_at']))
        return digest(dict(payload=payload, revision=revision,
            affected=[dict(id=p.id, **programme(p), subtitle=p.subtitle, description=p.description,
                           category=p.category, image_url=p.image_url) for p in base]))

    def remove(self, event_id, revision, broadcast_id):
        try:
            self.events.repo.reserve_revision(event_id, revision)
            self.db.expire_all()
            row = self.events.repo.get(event_id)
            row.guide_overlays = [s for s in row.guide_overlays or [] if s['broadcast_id'] != broadcast_id]
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def project(self, programs, lower, upper):
        result = {key: list(rows) for key, rows in programs.items()}
        entries = self.active_entries()
        # Conflicting persisted snapshots are withheld, never resolved by row order.
        for _, saved in entries:
            key = saved['context']['guide']['id']
            if key not in result:
                continue
            p = saved['programme']
            start, end = datetime.fromisoformat(p['starts_at']), datetime.fromisoformat(p['ends_at'])
            if start < lower or end > upper:
                continue
            if any(other is not saved and other['context']['guide']['id'] == key
                   and datetime.fromisoformat(other['programme']['starts_at']) < end
                   and datetime.fromisoformat(other['programme']['ends_at']) > start for _, other in entries):
                continue
            clipped = []
            for base in result[key]:
                if base.end_time <= start or base.start_time >= end:
                    clipped.append(base)
                    continue
                if base.start_time < start:
                    # Detached DTOs avoid mutating SQLAlchemy instrumentation.
                    before = SimpleNamespace(**{field: getattr(base, field) for field in
                        ('start_time', 'end_time', 'title', 'subtitle', 'description', 'category', 'image_url')})
                    before.end_time = start
                    clipped.append(before)
                if base.end_time > end:
                    after = SimpleNamespace(**{field: getattr(base, field) for field in
                        ('start_time', 'end_time', 'title', 'subtitle', 'description', 'category', 'image_url')})
                    after.start_time = end
                    clipped.append(after)
            clipped.append(SimpleNamespace(start_time=start, end_time=end, title=p['title'], subtitle=None,
                description='Reviewed event overlay. End time confirmed by the operator.',
                category=saved['context']['sport'] or None, image_url=None))
            result[key] = sorted(clipped, key=lambda row: row.start_time)
        return result
