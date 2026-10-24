"""Bounded, guarded fetching of reviewed normalized event schedules.

No transport-specific W3U or Telegram collection is duplicated here. Those
collectors submit EventImport observations through the shared review boundary.
"""
import asyncio
from datetime import datetime, timezone, timedelta
import json
import hashlib
import time
from urllib.parse import urlsplit
from uuid import uuid4

import aiohttp
from app.models.models import EventScheduleSource
from app.repositories.event_source_repository import EventSourceRepository
from app.schemas.events import EventImport, EventApply, EventSourceView, EventRefreshResult, EventRetention, EventRefreshQueued
from app.services.event_service import EventService, _LOCK, _PREVIEWS
from app.utils.outbound_http import source_session

MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_SOURCES = 20
REFRESH_BUDGET_SECONDS = 120


async def fetch_schedule(url, *, timeout=15, adapter=None):
    # aiohttp's total deadline includes DNS, every redirect and body delivery.
    try:
        async with source_session(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, max_redirects=5) as response:
                response.raise_for_status()
                data = bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    data.extend(chunk)
                    if len(data) > MAX_SOURCE_BYTES:
                        raise ValueError('Schedule is larger than 2 MiB')
        if adapter and adapter.get('format') == 'schema_org':
            from app.services.event_guide_adapter import parse_guide
            request = parse_guide(data.decode('utf-8-sig'),
                source_id='guide:' + hashlib.sha256(url.encode()).hexdigest()[:32],
                source_name=urlsplit(url).hostname, zone=adapter['timezone'])
        else:
            request = EventImport.model_validate(json.loads(data))
        if len({o.source_id for o in request.observations}) != 1:
            raise ValueError('A schedule URL must contain one stable source identity')
        return request
    except Exception:
        # Neither network exceptions nor Pydantic input are safe for public/log output.
        raise ValueError('Could not load this guide. Check its format, stable event IDs, explicit dates and source timezone (including DST); limit 2 MiB / 15 seconds. Existing events were preserved.') from None


def save_reviewed_source(db, context, selected, observations, enabled):
    """Called inside the same transaction as accepted event rows."""
    repo = EventSourceRepository(db)
    current = repo.by_identity(context['identity'])
    if (current.id if current else None) != context['id'] or (current.revision if current else None) != context['revision']:
        raise ValueError('Schedule source changed; review it again')
    accepted = {row.external_id for row in observations.values()
                if row.event_id in selected and row.source_id == context['identity']}
    accepted |= set(current.reviewed_ids) if current else set()
    if len(accepted) > 2000:
        raise ValueError('Source review limit reached; create a separate source identity')
    values = dict(adapter=context['adapter'], name=context['name'], url=context['url'], enabled=enabled, reviewed_ids=sorted(accepted))
    if current:
        repo.update(current.id, current.revision, **values)
    else:
        if len(repo.all()) >= MAX_SOURCES:
            raise ValueError('At most 20 schedule sources can be saved')
        db.add(EventScheduleSource(id=uuid4().hex, source_identity=context['identity'], revision=1, **values))


class EventSourceService:
    def __init__(self, db):
        self.db = db
        self.repo = EventSourceRepository(db)

    @staticmethod
    def view(row):
        return EventSourceView(**(row.adapter or {}), id=row.id, revision=row.revision, name=row.name,
            origin=urlsplit(row.url).hostname or '', enabled=row.enabled, reviewed=len(row.reviewed_ids),
            last_attempt=row.last_attempt, last_success=row.last_success, last_result=row.last_result)

    def list(self):
        return [self.view(row) for row in self.repo.all()]

    def preview(self, request):
        row = self.repo.get(request.source_id) if request.source_id else None
        if request.source_id and not row:
            raise LookupError('Schedule source not found')
        url = row.url if row else request.url
        adapter = row.adapter if row else {'format': request.format, 'timezone': request.timezone}
        prior = (row.id, row.revision, row.source_identity) if row else None
        self.db.rollback()  # Do not hold a DB transaction during upstream I/O.
        data = asyncio.run(fetch_schedule(url, adapter=adapter))
        identity = data.observations[0].source_id
        row = self.repo.by_identity(identity)
        if prior and (not row or (row.id, row.revision, identity) != prior):
            raise ValueError('Schedule source changed; review it again')
        if row and row.url != url:
            raise ValueError('This source identity belongs to another URL; use a distinct publisher identity')
        context = dict(id=row.id if row else None, revision=row.revision if row else None,
            identity=identity, url=url, name=data.observations[0].source_name, adapter=adapter)
        result = EventService(self.db).preview(data, context=context)
        result.warnings.append('Only selected events will refresh. New events always need review; omitted events remain saved.')
        return result

    def update(self, source_id, request):
        try:
            self.repo.update(source_id, request.revision, enabled=request.enabled)
            self.db.commit()
            self.db.expire_all()
        except Exception:
            self.db.rollback()
            raise
        return self.view(self.repo.get(source_id))

    def refresh(self, source_id, *, timeout=15):
        row = self.repo.get(source_id)
        if not row or not row.enabled:
            return None
        revision, url, identity, reviewed, adapter = row.revision, row.url, row.source_identity, set(row.reviewed_ids), row.adapter
        self.db.rollback()
        moment = datetime.now(timezone.utc)
        token = None
        try:
            data = asyncio.run(fetch_schedule(url, timeout=timeout, adapter=adapter))
            if data.observations[0].source_id != identity:
                raise ValueError('Source identity changed')
            existing = {o.external_id: o.event_id for o in self.repo.observations(identity)}
            accepted = [o.model_copy(update={'event_id': existing[o.external_id]}) for o in data.observations
                        if o.external_id in reviewed and o.external_id in existing]
            result = EventRefreshResult(status='updated' if accepted else 'unchanged', updated=len(accepted),
                pending=sum(o.external_id not in reviewed for o in data.observations),
                message='Reviewed events refreshed; new events need review.' if accepted else 'No reviewed events were present. Existing events were preserved.')
            # Reserve the source revision before touching events; disabling or editing
            # the source while fetching invalidates this entire refresh transaction.
            self.repo.update(source_id, revision, last_attempt=moment, last_success=moment, last_result=result.model_dump())
            if accepted:
                service = EventService(self.db)
                preview = service.preview(EventImport(observations=accepted), background=True)
                token = preview.token
                service.apply(EventApply(token=token, selected_ids=[e.id for e in preview.events]))
            else:
                self.db.commit()
            return result
        except Exception:
            self.db.rollback()
            result = EventRefreshResult(status='error', message='Schedule refresh failed or changed during the request. Existing events were preserved.')
            try:
                self.repo.update(source_id, revision, last_attempt=moment, last_result=result.model_dump())
                self.db.commit()
            except Exception:
                self.db.rollback()  # A newer user edit owns the source state.
            return result
        finally:
            if token:
                with _LOCK:
                    _PREVIEWS.pop(token, None)

    def refresh_all(self, *, shutdown=None):
        rows = sorted(self.repo.all(), key=lambda row: (row.last_attempt or datetime.min.replace(tzinfo=timezone.utc), row.id))
        ids = [row.id for row in rows if row.enabled]
        self.db.rollback()
        deadline = time.monotonic() + REFRESH_BUDGET_SECONDS
        result = {'updated': 0, 'pending': 0, 'failures': 0, 'deferred': 0}
        for index, source_id in enumerate(ids):
            remaining = deadline - time.monotonic()
            if remaining <= 0 or (shutdown and shutdown.is_set()):
                result['deferred'] = len(ids) - index
                break
            refreshed = self.refresh(source_id, timeout=min(15, remaining))
            if refreshed:
                result['updated'] += refreshed.updated
                result['pending'] += refreshed.pending
                result['failures'] += refreshed.status == 'error'
        return result

    def retention(self):
        row = self.repo.retention()
        return EventRetention.model_validate_json(row.value) if row else EventRetention()

    def save_retention(self, request):
        try:
            self.repo.save_retention(request.model_dump_json())
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return request

    def cleanup(self, *, now=None):
        policy = self.retention()
        moment = now or datetime.now(timezone.utc)
        count = 0
        service = EventService(self.db)
        try:
            for event in service.repo.inventory():
                if event.followed:
                    continue
                data = event.correction or event.fields
                end = datetime.fromisoformat(data['ends_at'].replace('Z', '+00:00')) if data.get('ends_at') else None
                archive_due = (policy.archived_days and event.archived and event.archived_at
                    and event.archived_at < moment - timedelta(days=policy.archived_days))
                ended_due = (policy.ended_days and not event.archived and data['state'] in ('finished', 'cancelled') and end
                    and end < moment - timedelta(days=policy.ended_days))
                if archive_due or ended_due:
                    service.repo.reserve_revision(event.id, event.revision)
                    self.repo.delete_event(event.id)
                    count += 1
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return {'deleted': count, **policy.model_dump()}


    @staticmethod
    def queue_refresh():
        from app.services.task_service import task_service
        outcome = task_service.run_task_now('url_scraping')
        if outcome == 'unavailable':
            raise RuntimeError('Scheduler unavailable')
        return EventRefreshQueued(status=outcome, message=(
            'Scraping and event refresh are already running or waiting. Follow progress in Overview.'
            if outcome == 'already_running' else
            'Scraping and enabled event sources queued. Follow progress in Overview.'))
