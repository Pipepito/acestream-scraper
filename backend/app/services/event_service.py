"""Reviewed, incremental event ingestion. No network or media checks during import."""
from collections import OrderedDict
from datetime import date as calendar_date, datetime, timezone, timedelta
import hashlib
import json
import secrets
import threading
import time
from urllib.parse import urlsplit
from uuid import uuid4

from app.models.models import SportingEvent, EventObservationRecord, EventMedia
from app.repositories.event_repository import EventRepository
from app.schemas.events import (EventFields, EventImport, EventObservation, EventPreview,
    EventView, BroadcastView, ProvenanceView, EventList)

_PREVIEWS = OrderedDict()
_LOCK = threading.RLock()
_MAX_EVENTS = 2000


def observation_key(source_id, external_id):
    return hashlib.sha256(json.dumps([source_id, external_id]).encode()).hexdigest()[:32]


def media_id(observation_id, broadcast):
    # Source identity includes the private URL and headers: rotating signed URLs
    # cannot join a stale shared session, nor collide with ordinary channel IDs.
    data = ['event', observation_id, broadcast.id, broadcast.url, broadcast.headers]
    return 'url:' + hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:40]


def fields(observation):
    return EventFields.model_validate({k: getattr(observation, k) for k in EventFields.model_fields}).model_dump(mode='json')


def validate_inventory(event_count, observations):
    if (event_count > _MAX_EVENTS or len(observations) > 4000
            or sum(len(o.payload['broadcasts']) for o in observations.values()) > 10000
            or sum(len(json.dumps(o.payload).encode()) for o in observations.values()) > 16 * 1024 * 1024):
        raise ValueError('Event inventory limit reached; existing events were preserved')


def dashboard_rank(data, start, now, tz, window_days):
    """Rank the full saved inventory before pagination; dates never imply times."""
    if data['state'] in ('finished', 'cancelled'):
        return None
    end = datetime.fromisoformat(data['ends_at'].replace('Z', '+00:00')) if data.get('ends_at') else None
    if end and end <= now:
        return None
    if data['state'] == 'live' and start and start <= now:
        if end or start >= now - timedelta(hours=24):
            return (0, start)
    today = now.astimezone(tz).date()
    last_day = today + timedelta(days=window_days)
    if start:
        if start >= now and start.astimezone(tz).date() < last_day:
            return (1, start)
    elif data.get('scheduled_date'):
        day = calendar_date.fromisoformat(data['scheduled_date'])
        if today <= day < last_day:
            return (2, day)
    return None


class EventService:
    def __init__(self, db):
        self.repo = EventRepository(db)
        from app.services.event_broadcast_service import EventBroadcastService
        self.broadcasts = EventBroadcastService(self.repo)
        from app.services.event_epg_service import EventEPGService
        self.epg = EventEPGService(self.repo)

    def _channels(self, observations, events=()):
        ids = {cid for event in events for cid in (event.broadcast_mappings or {}).values() if isinstance(cid, str)}
        for row in observations:
            for broadcast in row.payload['broadcasts']:
                if broadcast.get('channel_id'):
                    ids.add(broadcast['channel_id'].lower())
                elif (broadcast.get('url') or '').startswith('acestream://'):
                    ids.add(broadcast['url'][11:].lower())
        return self.repo.channels(ids)

    def _view(self, event, observations, channels=None):
        channels = self._channels(observations, [event]) if channels is None else channels
        broadcasts = []
        provenance = []
        for row in observations:
            obs = EventObservation.model_validate(row.payload)
            provenance.append(ProvenanceView(source_id=obs.source_id, source_name=obs.source_name,
                source_kind=obs.source_kind, external_id=obs.external_id, updated_at=row.updated_at))
            for b in obs.broadcasts:
                mapping = (event.broadcast_mappings or {}).get(f'{row.id}:{b.id}')
                target = self.broadcasts.reviewed_target(mapping) if isinstance(mapping, dict) else self.broadcasts.match(b) if not mapping else None
                if isinstance(mapping, dict):
                    b = b.model_copy(update={'channel_id': None, 'url': None})
                if isinstance(mapping, str):
                    b = b.model_copy(update={'channel_id': mapping, 'url': None})
                cid = None
                compatibility = 'unresolved'
                reason = 'Choose a channel to link this broadcaster.'
                if target:
                    compatibility = 'linked'
                    reason = 'Linked TV channel' if target.kind == 'tv' else 'Linked EPG channel'
                elif isinstance(mapping, dict):
                    reason = 'Previously linked channel changed, is missing or is disabled'
                    compatibility = 'unavailable'
                channel = None
                if b.channel_id:
                    channel = channels.get(b.channel_id.lower())
                    if channel and channel.is_active:
                        cid, compatibility, reason = b.channel_id.lower(), 'playable', 'Reviewed channel mapping'
                    else:
                        compatibility, reason = 'unavailable', 'Mapped channel is missing or disabled'
                elif b.url:
                    parsed = urlsplit(b.url)
                    if parsed.scheme == 'acestream':
                        cid, compatibility, reason = parsed.netloc.lower(), 'playable', 'AceStream'
                        channel = channels.get(cid)
                    elif parsed.path.lower().endswith(('.m3u8', '.ts')):
                        cid, compatibility, reason = media_id(row.id, b), 'playable', 'Guarded HTTP playback'
                    else:
                        compatibility, reason = 'unsupported', 'Website or unsupported media; a compatible resolver is required'
                broadcasts.append(BroadcastView(target=target, manually_mapped=bool(mapping), id=f'{row.id}:{b.id}', label=b.label, language=b.language,
                    quality=b.quality, country=b.country, source_name=obs.source_name,
                    origin=urlsplit(b.url).hostname or '' if b.url else '', content_id=cid,
                    compatibility=compatibility, reason=reason,
                    is_online=channel.is_online if channel else None,
                    checked_at=channel.last_checked if channel else None))
        return EventView(epg_matches=self.epg.match(event.correction or event.fields), has_artwork=any(o.payload.get('artwork_url') for o in observations), **(event.correction or event.fields), id=event.id, revision=event.revision,
            corrected=bool(event.correction), followed=event.followed, archived=event.archived,
            broadcasts=broadcasts, provenance=provenance)

    def get(self, event_id):
        event = self.repo.get(event_id)
        if event is None:
            raise LookupError('Event not found')
        return self._view(event, self.repo.observations(event_id))

    def interests(self):
        from app.schemas.events import EventInterestChoices
        data = [row.correction or row.fields for row in self.repo.inventory() if not row.archived]
        return EventInterestChoices(sports=sorted({d['sport'] for d in data if d['sport']})[:2000],
            competitions=sorted({d['competition'] for d in data if d['competition']})[:2000],
            teams=sorted({name for d in data for name in d['participants']})[:2000])

    def list(self, *, interests=None, window_days=None, search='', sport='', competition='', source='', date=None, zone='UTC',
             upcoming=False, followed=False, archived=False, offset=0, limit=50, selection='agenda'):
        from zoneinfo import ZoneInfo
        from app.services.event_providers import matches_interests
        tz = ZoneInfo(zone)
        now = datetime.now(timezone.utc)
        today = now.astimezone(tz).date()
        rows = self.repo.inventory()
        all_obs = self.repo.observations()
        grouped = {}
        for obs in all_obs:
            grouped.setdefault(obs.event_id, []).append(obs)
        selected = []
        for row in rows:
            data = row.correction or row.fields
            start = datetime.fromisoformat(data['starts_at'].replace('Z', '+00:00')) if data.get('starts_at') else None
            rank = dashboard_rank(data, start, now, tz, window_days or 7) if selection == 'dashboard' else None
            if selection == 'dashboard' and (row.archived or rank is None):
                continue
            local_day = start.astimezone(tz).date() if start else calendar_date.fromisoformat(data['scheduled_date']) if data.get('scheduled_date') else None
            if (row.archived != archived or (interests and not matches_interests(data, interests))
                    or (selection == 'agenda' and upcoming and window_days and local_day and local_day >= today + timedelta(days=window_days)) or (followed and not row.followed)
                    or (sport and sport.casefold() not in data['sport'].casefold())
                    or (competition and competition.casefold() not in data['competition'].casefold())
                    or (search and search.casefold() not in ' '.join([data['title'], *data['participants']]).casefold())
                    or (source and not any(source.casefold() in obs.payload['source_name'].casefold() for obs in grouped.get(row.id, [])))
                    or (date and local_day != date)
                    or (selection == 'agenda' and upcoming and (local_day is not None and local_day < today or data['state'] in ('finished', 'cancelled')))):
                continue
            selected.append((rank if selection == 'dashboard' else (start is None, start or datetime.max.replace(tzinfo=timezone.utc)), row))
        selected.sort(key=lambda item: (*item[0], item[1].id))
        page = selected[offset:offset + limit]
        channels = self._channels([obs for _, row in page for obs in grouped.get(row.id, [])], [row for _, row in page])
        return EventList(total=len(selected), events=[self._view(row, grouped.get(row.id, []), channels)
            for _, row in page])

    def preview(self, request: EventImport, *, context=None, background=False):
        rows = {r.id: r for r in self.repo.inventory()}
        observations = {r.id: r for r in self.repo.observations()}
        revisions = {key: row.revision for key, row in rows.items()}
        proposed = {}
        now = datetime.now(timezone.utc)
        for obs in request.observations:
            key = observation_key(obs.source_id, obs.external_id)
            existing = observations.get(key)
            if existing and obs.event_id and obs.event_id != existing.event_id:
                raise ValueError('An existing source identity cannot be moved to another event')
            if obs.event_id and obs.event_id not in rows:
                raise ValueError('The reviewed event association no longer exists')
            eid = existing.event_id if existing else obs.event_id or uuid4().hex
            if eid not in proposed:
                row = rows.get(eid)
                proposed[eid] = SportingEvent(id=eid, owner_id=row.owner_id if row else key, revision=row.revision if row else 0,
                    broadcast_mappings=row.broadcast_mappings if row else None, fields=dict(row.fields) if row else fields(obs), correction=row.correction if row else None,
                    followed=row.followed if row else False, archived=row.archived if row else False)
            # The first source owns schedule fields; linked observations contribute
            # broadcasts and provenance without silently overruling its schedule.
            if proposed[eid].owner_id == key:
                proposed[eid].fields = fields(obs)
            prior = EventObservation.model_validate(existing.payload) if existing else None
            if prior:
                # Missing variants in a partial refresh are retained. An explicit
                # same-ID replacement updates a URL; nothing deletes shared media.
                incoming = {b.id: b for b in obs.broadcasts}
                obs = obs.model_copy(update={'broadcasts': [*incoming.values(),
                    *(b for b in prior.broadcasts if b.id not in incoming)]})
                if len(obs.broadcasts) > 50:
                    raise ValueError('Event has more than 50 retained broadcasts; split the source')
            observations[key] = EventObservationRecord(id=key, event_id=eid,
                source_id=obs.source_id, external_id=obs.external_id,
                payload=obs.model_dump(mode='json'), updated_at=now)
        validate_inventory(len(set(rows) | set(proposed)), observations)
        channels = self._channels(observations.values(), proposed.values())
        views = [self._view(e, [o for o in observations.values() if o.event_id == e.id], channels) for e in proposed.values()]
        token = secrets.token_urlsafe(32)
        with _LOCK:
            while not background and len(_PREVIEWS) >= 4:
                _PREVIEWS.popitem(last=False)
            _PREVIEWS[token] = (time.monotonic() + 900, proposed, observations, revisions, context)
        return EventPreview(token=token, events=views, warnings=[
            'Import is not proof of live play or media signal.',
            'Missing events and broadcasts are retained. Existing manual corrections are preserved.'])

    def apply(self, request):
        with _LOCK:
            preview = _PREVIEWS.get(request.token)
            if not preview or preview[0] <= time.monotonic():
                raise ValueError('Preview expired; preview the schedule again')
            _, proposed, observations, revisions, context = preview
            selected = set(request.selected_ids)
            if (not selected and not (context and context.get('adapter', {}).get('provider_options'))) or not selected <= proposed.keys():
                raise ValueError('Select events from this preview')
            try:
                existing_obs = {r.id: r for r in self.repo.observations()}
                if any(key in existing_obs and existing_obs[key].event_id != row.event_id
                       for key, row in observations.items() if row.event_id in selected):
                    raise ValueError('Events changed; preview the schedule again')
                merged = {**existing_obs, **{key: row for key, row in observations.items() if row.event_id in selected}}
                validate_inventory(len({r.id for r in self.repo.inventory()} | selected), merged)
                for eid in selected:
                    event = proposed[eid]
                    if eid in revisions:
                        self.repo.reserve_revision(eid, revisions[eid], fields=event.fields)
                    else:
                        self.repo.add(SportingEvent(id=eid, owner_id=event.owner_id, revision=1, fields=event.fields,
                            followed=False, archived=False))
                self.repo.flush()
                for key, row in observations.items():
                    if row.event_id not in selected:
                        continue
                    existing = existing_obs.get(key)
                    if existing:
                        existing.payload, existing.updated_at = row.payload, row.updated_at
                    else:
                        self.repo.add(EventObservationRecord(id=key, event_id=row.event_id,
                            source_id=row.source_id, external_id=row.external_id,
                            payload=row.payload, updated_at=row.updated_at))
                    self.repo.flush()
                    retained_media = []
                    for b in EventObservation.model_validate(row.payload).broadcasts:
                        if b.url and urlsplit(b.url).scheme in ('http', 'https') and urlsplit(b.url).path.lower().endswith(('.m3u8', '.ts')):
                            cid = media_id(key, b)
                            retained_media.append(cid)
                            if not self.repo.media(cid):
                                self.repo.add(EventMedia(content_id=cid, observation_id=key, url=b.url, headers=b.headers))
                    self.repo.retain_media(key, retained_media)
                if context and context.get('kind') == 'catalogue':
                    from app.repositories.catalogue_repository import CatalogueRepository
                    # Reserve the same revision in this transaction, so a refresh
                    # or removal racing apply cannot publish stale media.
                    CatalogueRepository(self.repo.db).reserve_event_revision(context['id'], context['revision'], context['source_id'])
                elif context:
                    from app.services.event_source_service import save_reviewed_source
                    save_reviewed_source(self.repo.db, context, selected, observations, request.refresh_source)
                self.repo.commit()
            except Exception:
                self.repo.rollback()
                raise
            del _PREVIEWS[request.token]
        return [self.get(eid) for eid in dict.fromkeys(request.selected_ids)]

    def update(self, event_id, request):
        values = {}
        if 'correction' in request.model_fields_set:
            values['correction'] = request.correction.model_dump(mode='json') if request.correction else None
        for key in ('followed', 'archived'):
            if getattr(request, key) is not None:
                values[key] = getattr(request, key)
        if request.archived is not None:
            row = self.repo.get(event_id)
            if row and request.archived != row.archived:
                values['archived_at'] = datetime.now(timezone.utc) if request.archived else None
        try:
            self.repo.reserve_revision(event_id, request.revision, **values)
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise
        return self.get(event_id)


    def map_broadcast(self, event_id, request):
        event = self.repo.get(event_id)
        if event is None:
            raise LookupError('Event not found')
        broadcasts = {f'{row.id}:{b["id"]}' for row in self.repo.observations(event_id) for b in row.payload['broadcasts']}
        if request.broadcast_id not in broadcasts:
            raise ValueError('Broadcast changed; reload the event')
        mappings = dict(event.broadcast_mappings or {})
        if request.target_kind:
            target = self.repo.target(request.target_kind, request.target_id)
            if not target:
                raise ValueError('Choose an existing active TV channel or enabled EPG channel')
            mappings[request.broadcast_id] = {**target, 'kind': request.target_kind}
        elif request.channel_id:
            channel = self.repo.channel(request.channel_id.lower())
            if not channel or not channel.is_active:
                raise ValueError('Choose an existing active stream')
            mappings[request.broadcast_id] = channel.id
        else:
            mappings.pop(request.broadcast_id, None)
        try:
            self.repo.reserve_revision(event_id, request.revision, broadcast_mappings=mappings)
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise
        return self.get(event_id)


    def artwork(self, event_id):
        if not self.repo.get(event_id):
            raise LookupError('Event not found')
        url = next((row.payload.get('artwork_url') for row in self.repo.observations(event_id) if row.payload.get('artwork_url')), None)
        if not url:
            raise LookupError('No artwork supplied')
        self.repo.rollback()
        from app.services.event_artwork import fetch_artwork
        return fetch_artwork(url)
