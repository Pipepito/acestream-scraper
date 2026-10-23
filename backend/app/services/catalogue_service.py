"""Reviewed W3U import and non-destructive source-scoped refresh."""
import asyncio
import copy
import json
import secrets
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone

from app.repositories.catalogue_repository import CatalogueRepository
from app.repositories.channel_repository import ChannelRepository
from app.schemas.catalogue import CatalogueEntry, CatalogueView, CatalogueSummary
from app.services.w3u_parser import W3UTraversal, COMPATIBLE, http_url, origin, safe_text

_PREVIEWS = OrderedDict()
_PREVIEW_LOCK = threading.Lock()
_SAVE_LOCK = threading.Lock()
_ADMISSION = threading.BoundedSemaphore(2)
PREVIEW_TTL = 15 * 60


def public_view(snapshot, *, row=None, token=None, source_url=None):
    return CatalogueView(
        id=row.id if row else None, revision=row.revision if row else 0,
        name=row.name if row else snapshot['entries'][0]['name'],
        origin=origin(row.source_url if row else source_url),
        entries=[CatalogueEntry.model_validate(entry) for entry in snapshot['entries']],
        counts=snapshot['counts'], partial=snapshot['partial'], warnings=snapshot['warnings'],
        selected_branches=row.selected_branches if row else ['root'],
        mode=row.mode if row else 'compatible', refresh_enabled=row.refresh_enabled if row else False,
        can_refresh=bool(row.source_url if row else source_url),
        updated_at=row.updated_at if row else None, preview_token=token)


def remember(value):
    # Cap serialized preview size as well as count and TTL. Private content is
    # process-local, never a browser-supplied import payload or log message.
    if len(json.dumps(value).encode()) > 32 * 1024 * 1024:
        raise ValueError('Catalogue preview exceeds its storage budget; use a smaller branch URL')
    token = secrets.token_urlsafe(32)
    with _PREVIEW_LOCK:
        now = time.monotonic()
        for key, (expires, _) in list(_PREVIEWS.items()):
            if expires < now:
                del _PREVIEWS[key]
        while len(_PREVIEWS) >= 4:
            _PREVIEWS.popitem(last=False)
        _PREVIEWS[token] = (now + PREVIEW_TTL, value)
    return token


def recalled(token):
    with _PREVIEW_LOCK:
        cached = _PREVIEWS.get(token)
        if not cached or cached[0] < time.monotonic():
            raise ValueError('Preview expired. Preview the catalogue again before saving.')
        return copy.deepcopy(cached[1])


class CatalogueService:
    def __init__(self, db):
        self.db = db
        self.repository = CatalogueRepository(db)

    def get(self, catalogue_id):
        row = self.repository.get(catalogue_id)
        if row is None:
            raise LookupError('Catalogue not found')
        return public_view(row.snapshot, row=row)

    def list(self):
        return [CatalogueSummary(id=row.id, name=row.name, revision=row.revision,
            origin=origin(row.source_url), partial=bool(row.partial),
            refresh_enabled=row.refresh_enabled, updated_at=row.updated_at)
            for row in self.repository.list()]

    def preview(self, request):
        if not _ADMISSION.acquire(blocking=False):
            raise ValueError('Two catalogue previews are already running. Try again shortly.')
        try:
            row = self.repository.get(request.catalogue_id) if request.catalogue_id else None
            if request.catalogue_id and row is None:
                raise LookupError('Catalogue not found')
            try:
                source_url = row.source_url if row else http_url(request.url) if request.url else None
            except ValueError:
                raise ValueError('Enter a valid HTTP(S) URL without embedded credentials') from None
            old = copy.deepcopy(row.snapshot) if row else None
            # Release the read transaction before any upstream wait.
            revision = row.revision if row else 0
            catalogue_id = row.id if row else None
            self.db.rollback()
            traversal = W3UTraversal(cached=old.get('documents') if old else None)
            snapshot = (old if row and not source_url else
                        asyncio.run(traversal.run(url=source_url, sample=request.sample)))
            if old and snapshot['partial']:
                # Preserve previous entries, including folder ancestry and selections.
                new_ids = {entry['id'] for entry in snapshot['entries']}
                retained = [dict(entry, retained=True) for entry in old['entries'] if entry['id'] not in new_ids]
                if len(snapshot['entries']) + len(retained) <= traversal.limits.records:
                    snapshot['entries'].extend(retained)
                else:
                    snapshot['entries'] = [dict(entry, retained=True) for entry in old['entries']]
                    snapshot['warnings'].append('Partial result exceeds the retained-entry budget; previous inventory preserved')
            snapshot['_event_source_id'] = old.get('_event_source_id') or secrets.token_hex(16) if old else secrets.token_hex(16)
            snapshot['_reviewed_live_ids'] = old.get('_reviewed_live_ids', [e['id'] for e in old['entries'] if e.get('imported')]) if old else []
            # Persist unique final documents only, avoiding redirect-alias amplification.
            snapshot['documents'] = {value['url']: value for value in snapshot['documents'].values()}
            token = remember(dict(snapshot=snapshot, source_url=source_url,
                                  catalogue_id=catalogue_id, revision=revision))
            row = self.repository.get(catalogue_id) if catalogue_id else None
            if catalogue_id and (row is None or row.revision != revision):
                raise ValueError('Catalogue changed during preview. Preview it again.')
            return public_view(snapshot, row=row, token=token, source_url=source_url)
        finally:
            _ADMISSION.release()

    def save(self, request):
        with _SAVE_LOCK:
            result = self._save(request)
            with _PREVIEW_LOCK:
                _PREVIEWS.pop(request.preview_token, None)
            return result

    def _save(self, request):
        preview = recalled(request.preview_token)
        snapshot = preview['snapshot']
        entries = snapshot['entries']
        folders = {entry['id'] for entry in entries if entry['kind'] == 'folder'}
        if not set(request.selected_branches) <= folders:
            raise ValueError('Selection contains an unknown folder. Preview the catalogue again.')
        selected = set(request.selected_branches)
        by_id = {entry['id']: entry for entry in entries}
        def included(entry):
            parent = entry['parent_id']
            visited = set()
            while parent is not None and parent not in visited:
                if parent in selected:
                    return True
                visited.add(parent)
                parent = by_id.get(parent, {}).get('parent_id')
            return False
        try:
            row = self.repository.save(preview['catalogue_id'], preview['revision'], dict(
                name=safe_text(request.name) or 'W3U catalogue', source_url=preview['source_url'],
                snapshot=copy.deepcopy(snapshot), selected_branches=list(dict.fromkeys(request.selected_branches)),
                mode=request.mode, refresh_enabled=request.refresh_enabled and bool(preview['source_url']),
                updated_at=datetime.now(timezone.utc)))
            reviewed = set(snapshot.get('_reviewed_live_ids', []))
            channels = ChannelRepository(self.db)
            imported = set()
            for entry in entries:
                channel_id = entry.get('channel_id')
                entry['imported'] = False
                if (not channel_id or entry['kind'] not in COMPATIBLE or not included(entry)
                        or entry.get('content_type') in ('event', 'vod')
                        or (not request.confirm_live and entry['id'] not in reviewed)
                        or (request.mode == 'acestream' and entry['kind'] != 'acestream')):
                    continue
                if channel_id not in imported:
                    # Existing rows retain operator names, assignments, activity,
                    # headers and other-source ownership. Refresh never deletes.
                    existing = channels.get_channel_by_id(channel_id)
                    if existing is None:
                        path = []
                        parent = entry['parent_id']
                        while parent and parent != 'root':
                            ancestor = by_id.get(parent)
                            if ancestor is None:
                                break
                            path.append(ancestor['name'])
                            parent = ancestor['parent_id']
                        channels.create_or_update_channel(channel_id=channel_id, name=entry['name'],
                            source_url=f'catalogue:{row.id}', group=' / '.join(reversed(path))[:255],
                            logo=entry['image'], tvg_id=entry['guide_id'],
                            stream_url=entry.get('_stream_url'), stream_headers=entry.get('_headers'),
                            is_online=None, commit=False)
                    imported.add(channel_id)
                entry['imported'] = True
                reviewed.add(entry['id'])
            snapshot['_reviewed_live_ids'] = sorted(reviewed)
            # SQLAlchemy JSON mutations must be assigned as a fresh value.
            row.snapshot = copy.deepcopy(snapshot)
            self.db.commit()
            self.db.refresh(row)
            return public_view(row.snapshot, row=row)
        except Exception:
            self.db.rollback()
            raise

    def refresh(self, catalogue_id):
        from app.schemas.catalogue import CataloguePreviewRequest, CatalogueSaveRequest
        preview = self.preview(CataloguePreviewRequest(catalogue_id=catalogue_id))
        return self.save(CatalogueSaveRequest(preview_token=preview.preview_token, name=preview.name,
            selected_branches=preview.selected_branches, mode=preview.mode, refresh_enabled=preview.refresh_enabled))

    def refresh_enabled(self):
        ids = self.repository.enabled_ids()
        self.db.rollback()
        result = {'catalogues': len(ids), 'catalogue_failures': 0, 'catalogue_partial': 0}
        for catalogue_id in ids:
            try:
                view = self.refresh(catalogue_id)
                result['catalogue_partial'] += int(view.partial)
            except Exception:
                self.db.rollback()
                result['catalogue_failures'] += 1
        return result


    def preview_event(self, catalogue_id, request):
        from app.schemas.events import EventFields, EventImport, EventObservation, EventBroadcast
        from app.services.event_service import EventService
        row = self.repository.get(catalogue_id)
        if row is None:
            raise LookupError('Catalogue not found')
        if row.revision != request.revision:
            raise ValueError('Catalogue changed; reload it before reviewing events')
        if not row.snapshot.get('_event_source_id'):
            raise ValueError('Review and save this catalogue once before adding events')
        entries = {entry['id']: entry for entry in row.snapshot['entries']}
        selected = [entries.get(key) for key in dict.fromkeys(request.entry_ids)]
        if any(not entry or entry['kind'] not in COMPATIBLE or entry.get('content_type') == 'vod' for entry in selected):
            raise ValueError('Choose compatible event broadcasts; VOD and unsupported sources cannot be imported as events')
        broadcasts = []
        publisher_ids = [e.get('_publisher_id') for e in entries.values() if e.get('_publisher_id')]
        if any(e.get('_publisher_id') and publisher_ids.count(e['_publisher_id']) != 1 for e in selected):
            raise ValueError('Publisher IDs are not unique in this catalogue; correct the source before importing events')
        for entry in selected:
            cid = entry.get('channel_id')
            url = entry.get('_stream_url') or ('acestream://' + cid if cid and not cid.startswith('url:') else None)
            # Resolver web pages are not direct event media; retain an explicit
            # unresolved broadcast for mapping, rather than bypassing the player.
            if entry['kind'] == 'resolver':
                url = None
            broadcasts.append(EventBroadcast(id=entry.get('_publisher_id', entry['id']),
                label=entry['name'][:200], url=url, headers=entry.get('_headers', {}) if url else {}))
        data = {key: getattr(request, key) for key in EventFields.model_fields}
        observation = EventObservation(**data, source_id=f"w3u:{row.snapshot['_event_source_id']}", source_name=row.name[:200],
            source_kind='w3u', external_id=selected[0].get('_publisher_id', selected[0]['id']),
            event_id=request.event_id, broadcasts=broadcasts)
        return EventService(self.db).preview(EventImport(observations=[observation]),
            context={'kind': 'catalogue', 'id': row.id, 'revision': row.revision, 'source_id': row.snapshot['_event_source_id']})
