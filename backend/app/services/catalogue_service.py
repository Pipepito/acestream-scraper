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
from app.schemas.catalogue import CatalogueEntry, CatalogueView, CatalogueSummary
from app.services.w3u_parser import W3UTraversal, COMPATIBLE, http_url, origin, safe_text
from app.utils.stream_kind import stream_kind

_PREVIEWS = OrderedDict()
_PREVIEW_LOCK = threading.Lock()
_SAVE_LOCK = threading.Lock()
_ADMISSION = threading.BoundedSemaphore(2)


class ConflictError(Exception):
    """A folder or TV channel in a match-apply request no longer exists; nothing was written."""


def folder_path(by_id, folder):
    parts = [folder['name']]
    parent, guard = folder.get('parent_id'), 0
    while parent and parent != 'root' and parent in by_id and guard < 50:
        parts.append(by_id[parent]['name'])
        parent = by_id[parent].get('parent_id')
        guard += 1
    return ' / '.join(reversed(parts))


def folder_streams(snapshot, folder_id):
    """Unique channel ids of the imported, compatible, live streams under a folder, plus how many
    compatible entries were skipped because they were never imported. Descendants count."""
    entries = snapshot.get('entries', [])
    by_id = {e['id']: e for e in entries}
    folder = by_id.get(folder_id)
    if folder is None or folder.get('kind') != 'folder':
        raise LookupError('Folder not found in this catalogue')
    children = {}
    for e in entries:
        children.setdefault(e.get('parent_id'), []).append(e)
    ids, seen, skipped = [], set(), 0
    stack, visited = [folder_id], set()
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        for e in children.get(current, []):
            if e.get('kind') == 'folder':
                stack.append(e['id'])
                continue
            if e.get('kind') not in COMPATIBLE or not e.get('channel_id'):
                continue
            if not e.get('imported'):
                skipped += 1
                continue
            if e.get('content_type') in ('event', 'vod') or e['channel_id'] in seen:
                continue
            seen.add(e['channel_id'])
            ids.append(e['channel_id'])
    return ids, skipped
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
        updated_at=row.updated_at if row else None, preview_token=token,
        policy_revision=snapshot.get("_policy_revision", 0))


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
            from app.services.import_exclusion_service import ImportExclusionService
            policy = ImportExclusionService(self.db).snapshot()
            snapshot['_policy_revision'] = policy.revision
            snapshot['counts']['excluded'] = 0
            for entry in snapshot['entries']:
                entry['excluded_rule_ids'] = (policy.matches(entry['channel_id'], entry['name'])
                    if entry.get('channel_id') and entry.get('content_type') not in ('event', 'vod') else [])
                snapshot['counts']['excluded'] += bool(entry['excluded_rule_ids'])
            token = remember(dict(snapshot=snapshot, source_url=source_url,
                                  catalogue_id=catalogue_id, revision=revision))
            row = self.repository.get(catalogue_id) if catalogue_id else None
            if catalogue_id and (row is None or row.revision != revision):
                raise ValueError('Catalogue changed during preview. Preview it again.')
            return public_view(snapshot, row=row, token=token, source_url=source_url)
        finally:
            _ADMISSION.release()

    def save(self, request, *, reviewed=True):
        with _SAVE_LOCK:
            result = self._save(request, reviewed=reviewed)
            with _PREVIEW_LOCK:
                _PREVIEWS.pop(request.preview_token, None)
            return result

    def _save(self, request, *, reviewed=True):
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
            from app.services.import_exclusion_service import ImportExclusionService
            from app.api.error_handlers import APIError
            from app.services.import_pipeline import ImportEntry, ImportPipeline, ImportReference
            policy = ImportExclusionService(self.db).snapshot(claim=True)
            if reviewed and policy.revision != snapshot.get('_policy_revision', 0):
                raise APIError('IMPORT_POLICY_CHANGED', 'Import exclusions changed. Preview again.', 409)
            snapshot['_policy_revision'] = policy.revision
            snapshot['counts']['excluded'] = sum(bool(policy.matches(e.get('channel_id') or '', e['name'])) for e in entries if e.get('channel_id') and e.get('content_type') not in ('event', 'vod'))
            row = self.repository.save(preview['catalogue_id'], preview['revision'], dict(
                name=safe_text(request.name) or 'W3U catalogue', source_url=preview['source_url'],
                snapshot=copy.deepcopy(snapshot), selected_branches=list(dict.fromkeys(request.selected_branches)),
                mode=request.mode, refresh_enabled=request.refresh_enabled and bool(preview['source_url']),
                updated_at=datetime.now(timezone.utc)))
            reviewed = set(snapshot.get('_reviewed_live_ids', []))
            eligible = []
            for entry in entries:
                channel_id = entry.get('channel_id')
                entry['imported'] = False
                if (not channel_id or entry['kind'] not in COMPATIBLE or not included(entry)
                        or entry.get('content_type') in ('event', 'vod')
                        or (not request.confirm_live and entry['id'] not in reviewed)
                        or (request.mode == 'acestream' and entry['kind'] != 'acestream')):
                    continue
                reviewed.add(entry['id'])
                eligible.append(entry)

            def import_entry(entry: dict) -> ImportEntry:
                path = []
                parent = entry['parent_id']
                while parent and parent != 'root':
                    ancestor = by_id.get(parent)
                    if ancestor is None:
                        break
                    path.append(ancestor['name'])
                    parent = ancestor['parent_id']
                return ImportEntry(entry['channel_id'], entry['name'], group=' / '.join(reversed(path))[:255],
                                   logo=entry['image'], tvg_id=entry['guide_id'],
                                   stream_url=entry.get('_stream_url'), stream_headers=entry.get('_headers'))
            # Existing rows retain operator names, assignments, activity,
            # headers and other-source ownership. Refresh never deletes.
            result = ImportPipeline.apply(self.db, ImportReference(f'catalogue:{row.id}'),
                                          [import_entry(entry) for entry in eligible], 'insert_only', policy=policy)
            for entry, item in zip(eligible, result.items):
                entry['excluded_rule_ids'] = item.rule_ids
                entry['imported'] = item.outcome != 'excluded'
            snapshot['_reviewed_live_ids'] = sorted(reviewed)
            # SQLAlchemy JSON mutations must be assigned as a fresh value.
            row.snapshot = copy.deepcopy(snapshot)
            self.db.commit()
            self.db.refresh(row)
            return public_view(row.snapshot, row=row)
        except Exception:
            self.db.rollback()
            raise

    def assign_folder(self, catalogue_id, entry_id, request, *, commit=True, ids=None):
        """Assign a folder's imported streams to one TV channel. ``ids`` narrows the folder's streams
        (the match-apply pass uses it so a parent never re-handles a child's streams)."""
        from app.models.models import AcestreamChannel, TVChannel
        from app.repositories.channel_repository import ChannelRepository
        from app.schemas.catalogue import FolderAssignResult, TVChannelRef
        row = self.repository.get(catalogue_id)
        if row is None:
            raise LookupError('Catalogue not found')
        stream_ids, skipped_not_imported = folder_streams(row.snapshot, entry_id)
        if ids is not None:
            stream_ids = [cid for cid in stream_ids if cid in ids]
        if not stream_ids:
            raise ValueError('This folder has no imported streams to assign')
        try:
            if request.create_name:
                name = request.create_name.strip()
                if self.db.query(TVChannel.id).filter(TVChannel.name == name).first():
                    raise ValueError(f'A TV channel named "{name}" already exists; choose it instead')
                # Created directly: the TV channel service's name-based auto-association
                # must not pull unrelated streams into a folder assignment.
                tv = TVChannel(name=name, is_active=True)
                self.db.add(tv)
                self.db.flush()
            else:
                tv = self.db.get(TVChannel, request.tv_channel_id)
                if tv is None or not tv.is_active:
                    raise LookupError('TV channel not found')
            owners = {cid: owner for cid, owner in self.db.query(AcestreamChannel.id, AcestreamChannel.tv_channel_id)
                      .filter(AcestreamChannel.id.in_(stream_ids)).all()}
            unassigned = [cid for cid, owner in owners.items() if owner is None]
            already = [cid for cid, owner in owners.items() if owner == tv.id]
            elsewhere = [cid for cid, owner in owners.items() if owner not in (None, tv.id)]
            channels = ChannelRepository(self.db)
            assigned = channels.assign_acestreams_to_tv_channel(unassigned, tv.id, commit=False) if unassigned else 0
            moved = channels.move_acestreams_to_tv_channel(elsewhere, tv.id) if request.reassign and elsewhere else 0
            if commit:
                self.db.commit()
            return FolderAssignResult(tv_channel=TVChannelRef(id=tv.id, name=tv.name), assigned=assigned, already=len(already),
                                      moved=moved, skipped_other_channel=0 if request.reassign else len(elsewhere),
                                      skipped_not_imported=skipped_not_imported)
        except Exception:
            if commit:
                self.db.rollback()
            raise

    def folder_matches(self, catalogue_id):
        """Folders worth assigning: those holding imported streams themselves, plus parents whose
        name matches a TV channel. Streams always mean descendants, like assign_folder."""
        from app.models.models import AcestreamChannel, TVChannel
        from app.schemas.catalogue import FolderMatchPreview, FolderMatchRow, TVChannelRef
        from app.services.tv_matching_service import normalize_name, name_score
        row = self.repository.get(catalogue_id)
        if row is None:
            raise LookupError('Catalogue not found')
        entries = row.snapshot.get('entries', [])
        by_id = {e['id']: e for e in entries}
        index = {}
        for tv in self.db.query(TVChannel.id, TVChannel.name, TVChannel.country).filter(TVChannel.is_active.is_(True)).all():
            candidate = normalize_name(tv.name, tv.country)
            index.setdefault(candidate.text, []).append((candidate, tv))
        direct = {e.get('parent_id') for e in entries if e.get('kind') in COMPATIBLE and e.get('imported')
                  and e.get('channel_id') and e.get('content_type') not in ('event', 'vod')}
        folders = [e for e in entries if e.get('kind') == 'folder' and e['id'] != 'root']
        per_folder = {folder['id']: folder_streams(row.snapshot, folder['id'])[0] for folder in folders}
        all_ids = sorted({cid for ids in per_folder.values() for cid in ids})
        owners = {}
        for offset in range(0, len(all_ids), 500):
            owners.update(self.db.query(AcestreamChannel.id, AcestreamChannel.tv_channel_id)
                          .filter(AcestreamChannel.id.in_(all_ids[offset:offset + 500])).all())
        rows = []
        for folder in folders:
            ids = per_folder[folder['id']]
            if not ids:
                continue
            name = normalize_name(folder['name'])
            matches = [tv for candidate, tv in index.get(name.text, []) if name_score(name, candidate, allow_unknown_country=True)]
            if folder['id'] not in direct and not matches:
                continue
            owner_ids = {owners.get(cid) for cid in ids}
            current, status = None, 'none'
            if len(owner_ids) == 1 and None not in owner_ids:
                owner = self.db.get(TVChannel, next(iter(owner_ids)))
                status, current = 'assigned', TVChannelRef(id=owner.id, name=owner.name) if owner else None
            elif len(matches) == 1:
                status = 'match'
            elif len(matches) > 1:
                status = 'ambiguous'
            candidate = TVChannelRef(id=matches[0].id, name=matches[0].name) if len(matches) == 1 else None
            rows.append(FolderMatchRow(folder_id=folder['id'], name=folder['name'], path=folder_path(by_id, folder),
                                       stream_count=len(ids), candidate=candidate, current=current, status=status))
        return FolderMatchPreview(rows=rows)

    def apply_folder_matches(self, catalogue_id, request):
        """Apply several folder assignments in one transaction, deepest folders first so a
        parent never re-handles streams a subfolder already took."""
        from app.models.models import TVChannel
        from app.schemas.catalogue import FolderAssignRequest, FolderApplyRow, FolderMatchApplyResult
        row = self.repository.get(catalogue_id)
        if row is None:
            raise LookupError('Catalogue not found')
        by_id = {e['id']: e for e in row.snapshot.get('entries', [])}
        for item in request.assignments:
            folder = by_id.get(item.folder_id)
            if folder is None or folder.get('kind') != 'folder':
                raise ConflictError('A folder is no longer in this catalogue; preview the matches again')
            if item.tv_channel_id is not None:
                tv = self.db.get(TVChannel, item.tv_channel_id)
                if tv is None or not tv.is_active:
                    raise ConflictError('A chosen TV channel no longer exists; preview the matches again')

        def depth(folder_id):
            level, parent, guard = 0, by_id[folder_id].get('parent_id'), 0
            while parent and parent in by_id and guard < 100:
                level, parent, guard = level + 1, by_id[parent].get('parent_id'), guard + 1
            return level

        handled, results = set(), {}
        try:
            for item in sorted(request.assignments, key=lambda entry: -depth(entry.folder_id)):
                remaining = [cid for cid in folder_streams(row.snapshot, item.folder_id)[0] if cid not in handled]
                if not remaining:
                    results[item.folder_id] = FolderApplyRow(folder_id=item.folder_id, note='Covered by a subfolder in this pass')
                    continue
                folder_request = FolderAssignRequest(tv_channel_id=item.tv_channel_id,
                    create_name=by_id[item.folder_id]['name'] if item.create else None, reassign=request.reassign)
                result = self.assign_folder(catalogue_id, item.folder_id, folder_request, commit=False, ids=set(remaining))
                handled |= set(remaining)
                results[item.folder_id] = FolderApplyRow(folder_id=item.folder_id, tv_channel=result.tv_channel, assigned=result.assigned,
                    already=result.already, moved=result.moved, skipped_other_channel=result.skipped_other_channel,
                    skipped_not_imported=result.skipped_not_imported)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return FolderMatchApplyResult(results=[results[item.folder_id] for item in request.assignments])

    def refresh(self, catalogue_id):
        from app.schemas.catalogue import CataloguePreviewRequest, CatalogueSaveRequest
        preview = self.preview(CataloguePreviewRequest(catalogue_id=catalogue_id))
        return self.save(CatalogueSaveRequest(preview_token=preview.preview_token, name=preview.name,
            selected_branches=preview.selected_branches, mode=preview.mode, refresh_enabled=preview.refresh_enabled), reviewed=False)

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
            url = entry.get('_stream_url') or ('acestream://' + cid if cid and stream_kind(cid) != 'http' else None)
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
