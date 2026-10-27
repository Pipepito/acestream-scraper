"""Configuration-only saves and bounded additive execution for catalogue searches."""
import hashlib
import json
import time
import unicodedata
from sqlalchemy.exc import IntegrityError
from app.api.error_handlers import APIError
from app.config.database import SessionLocal
from app.models.models import SavedSearch, _utcnow
from app.repositories.saved_search_repository import SavedSearchRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.config_service import ConfigService
from app.services.import_exclusion_service import ImportExclusionService
from app.services.search_catalogue_client import SearchCatalogueClient, CatalogueReadError
from app.services.search_import_service import resolve_candidates, apply_candidates
from app.services import search_preview_store
from app.schemas.saved_searches import SavedSearchView, SavedSearchList, SavedSearchResult, SavedSearchPreview


def fingerprint(query, category):
    values = [' '.join(unicodedata.normalize('NFKC', v).split()) for v in (query, category)]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()


def check(row, revision=None, *, automatic=False):
    if row is None:
        raise APIError('SAVED_SEARCH_NOT_FOUND', 'Saved search no longer exists.', 404)
    if (revision is not None and row.revision != revision) or (automatic and not row.refresh_enabled):
        raise APIError('SAVED_SEARCH_CHANGED', 'Saved search changed. Reload before running.', 409)
    return row


class SavedSearchService:
    def __init__(self, db):
        self.db = db
        self.repo = SavedSearchRepository(db)

    def get(self, sid):
        return SavedSearchView.model_validate(check(self.repo.get(sid)))

    def list(self, offset=0, limit=50):
        query = self.repo.list()
        return SavedSearchList(items=[SavedSearchView.model_validate(r) for r in query.offset(offset).limit(limit)], total=query.count())

    def save(self, data, sid=None):
        try:
            self.repo.claim()
            row = check(self.repo.get(sid), data.expected_revision) if sid is not None else None
            if row is None:
                if self.repo.list().count() >= 100:
                    raise APIError('SEARCH_LIMIT_REACHED', 'At most 100 saved searches are supported.', 409)
                row = SavedSearch(revision=0)
                self.db.add(row)
            changed_identity = row.revision > 0 and (row.query != data.query or row.category != data.category)
            row.name, row.query, row.category = data.name, data.query, data.category
            row.fingerprint = fingerprint(data.query, data.category)
            row.refresh_enabled = False if changed_identity else data.refresh_enabled
            row.revision += 1
            row.updated_at = _utcnow()
            self.db.commit()
            return SavedSearchView.model_validate(row)
        except IntegrityError:
            self.db.rollback()
            existing = self.repo.find_fingerprint(fingerprint(data.query, data.category))
            raise APIError('SAVED_SEARCH_DUPLICATE', 'This query and category are already saved.', 409,
                           {'saved_search_id': existing}) from None
        except Exception:
            self.db.rollback()
            raise

    def delete(self, sid, revision):
        try:
            self.repo.claim()
            self.repo.delete(check(self.repo.get(sid), revision))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def preview(self, request):
        if request.saved_search_id:
            definition = SavedSearchView.model_validate(check(self.repo.get(request.saved_search_id), request.expected_revision))
            revision = definition.revision
        else:
            definition, revision = request.definition, 0
        policy = ImportExclusionService(self.db).snapshot()
        url = ConfigService(SettingsRepository(self.db)).get_ace_engine_url()
        self.db.rollback()
        start = _utcnow()
        began = time.monotonic()
        candidates, counts = fetch(definition, policy, url)
        current = ImportExclusionService(self.db).snapshot()
        if current.revision != policy.revision:
            raise APIError('IMPORT_POLICY_CHANGED', 'Import exclusions changed. Preview again.', 409)
        if request.saved_search_id:
            check(self.repo.get(request.saved_search_id), revision)
        admission = apply_candidates(self.db, candidates, current, dry_run=True)
        result = summarize(admission, candidates, counts, revision, start, began)
        token = search_preview_store.remember(dict(saved_search_id=request.saved_search_id,
            definition_revision=revision, policy_revision=policy.revision,
            candidates=candidates, counts=counts))
        return SavedSearchPreview(preview_token=token, result=result)

    def run(self, sid, request, task_service):
        definition = self.get(sid)
        check(self.repo.get(sid), request.expected_revision)
        preview = search_preview_store.recall(request.preview_token) if request.preview_token else None
        if preview:
            if preview['saved_search_id'] != sid or preview['definition_revision'] != request.expected_revision:
                raise APIError('SAVED_SEARCH_CHANGED', 'Preview belongs to a different search revision.', 409)
            if preview['policy_revision'] != ImportExclusionService(self.db).snapshot().revision:
                raise APIError('IMPORT_POLICY_CHANGED', 'Import exclusions changed. Preview again.', 409)
        self.db.rollback()
        target = dict(definition=definition.model_dump(mode='json'), automatic=False, preview=preview)
        task_service.submit_maintenance_target(f'saved_search:{sid}', target,
            prepare=prepare_target, execute=execute_target, finish=finish_target)
        self.db.expire_all()
        return self.get(sid)


def fetch(definition, policy, url, shutdown=None, deadline=None):
    try:
        with SearchCatalogueClient(url, shutdown=shutdown, deadline=deadline) as client:
            candidates, counts = client.collect(definition.query, definition.category)
            candidates = resolve_candidates(client, candidates, policy)
            if not counts.get('stop_reason'):
                counts['stop_reason'] = next((c['resolution_stop_reason'] for c in candidates
                    if c.get('resolution_stop_reason') in ('deadline', 'shutdown')), None)
        return candidates, counts
    except CatalogueReadError as exc:
        return [], dict(stop_reason=exc.code, pages_fetched=0)


def summarize(admission, candidates, counts, revision, start, began):
    counts = dict(counts)
    reason = counts.pop('stop_reason', None)
    invalid = counts.pop('unresolved_candidates', 0)
    duplicates = counts.pop('duplicates', 0) + sum(i.outcome == 'duplicate' for i in admission.items)
    unresolved = admission.unresolved + invalid
    outcome = 'complete'
    if reason or unresolved or admission.deferred:
        outcome = 'partial' if candidates else 'failed'
    if reason == 'SEARCH_ENGINE_UNCONFIGURED':
        outcome = 'skipped'
    if reason == 'shutdown':
        outcome = 'interrupted'
    return SavedSearchResult(outcome=outcome, stop_reason=reason, **counts,
        resolved_content_ids=len({c['content_id'] for c in candidates if c.get('content_id')}),
        added=admission.added, existing=admission.existing, excluded_candidates=admission.excluded,
        unresolved_candidates=unresolved, duplicates=duplicates, deferred_candidates=admission.deferred,
        policy_revision=admission.policy_revision, definition_revision=revision,
        started_at=start, finished_at=_utcnow(), duration_seconds=round(time.monotonic() - began, 3),
        samples=admission.items[:100], samples_truncated=len(admission.items) > 100)


def scheduled_targets():
    with SessionLocal() as db:
        rows = SavedSearchRepository(db).scheduled()
        return [(f'saved_search:{r.id}', dict(definition=SavedSearchView.model_validate(r).model_dump(mode='json'),
                                            automatic=True, preview=None)) for r in rows]


def prepare_target(run_id, target):
    definition = target['definition']
    with SessionLocal() as db:
        repo = SavedSearchRepository(db)
        repo.claim()
        row = check(repo.get(definition['id']), definition['revision'], automatic=target['automatic'])
        row.run_id, row.run_state = run_id, 'waiting'
        row.error_code = row.error_message = None
        db.commit()
    return dict(target, run_id=run_id)


def finish_target(target):
    """Release unfinished persisted state after queue shutdown/failure/budget."""
    with SessionLocal() as db:
        repo = SavedSearchRepository(db)
        repo.claim()
        row = repo.get(target['definition']['id'])
        if row and row.run_id == target['run_id'] and row.run_state:
            row.run_state = None
            row.last_result = None
            row.last_outcome = 'interrupted'
            row.last_finished_at = _utcnow()
            row.error_code = 'interrupted'
            row.error_message = 'Run did not complete. Run again when ready.'
            db.commit()


def execute_target(target, shutdown, *, deadline=None):
    definition = SavedSearchView.model_validate(target['definition'])
    began, start = time.monotonic(), _utcnow()
    try:
        if shutdown.is_set():
            raise APIError('interrupted', 'Application is stopping.', 409)
        with SessionLocal() as db:
            repo = SavedSearchRepository(db)
            repo.claim()
            row = check(repo.get(definition.id), definition.revision, automatic=target['automatic'])
            if row.run_id != target['run_id']:
                raise APIError('SAVED_SEARCH_CHANGED', 'Run ownership changed.', 409)
            row.run_state, row.last_started_at, row.last_attempt_at = 'running', start, start
            policy = ImportExclusionService(db).snapshot()
            url = ConfigService(SettingsRepository(db)).get_ace_engine_url()
            db.commit()
        preview = target.get('preview')
        if preview:
            candidates, counts = preview['candidates'], preview['counts']
        else:
            candidates, counts = fetch(definition, policy, url, shutdown, deadline)
        with SessionLocal() as db:
            repo = SavedSearchRepository(db)
            repo.claim()
            row = check(repo.get(definition.id), definition.revision, automatic=target['automatic'])
            if row.run_id != target['run_id']:
                raise APIError('SAVED_SEARCH_CHANGED', 'Run ownership changed.', 409)
            policy = ImportExclusionService(db).snapshot()
            if preview and preview['policy_revision'] != policy.revision:
                raise APIError('IMPORT_POLICY_CHANGED', 'Import exclusions changed. Preview again.', 409)
            if shutdown.is_set():
                raise APIError('interrupted', 'Application is stopping.', 409)
            admission = apply_candidates(db, candidates, policy, f'saved-search:{definition.id}')
            for item in admission.items:
                if item.outcome in ('added', 'existing'):
                    repo.membership(definition.id, item.content_id)
            result = summarize(admission, candidates, counts, definition.revision, start, began)
            row.last_result = result.model_dump(mode='json')
            row.last_outcome, row.last_finished_at, row.run_state = result.outcome, result.finished_at, None
            if result.outcome == 'complete':
                row.last_success_at = result.finished_at
            if result.outcome in ('failed', 'skipped'):
                row.error_code = result.stop_reason
                row.error_message = 'Configure a reachable AceStream engine in Settings → Playback.'
            db.commit()
    except Exception as exc:
        code = exc.code if isinstance(exc, APIError) else 'SEARCH_IMPORT_FAILED'
        result = SavedSearchResult(outcome='interrupted' if code == 'interrupted' else 'skipped' if code in (
            'SAVED_SEARCH_CHANGED', 'SAVED_SEARCH_NOT_FOUND', 'IMPORT_POLICY_CHANGED') else 'failed',
            stop_reason=code, policy_revision=0, definition_revision=definition.revision,
            started_at=start, finished_at=_utcnow(), duration_seconds=round(time.monotonic() - began, 3))
        with SessionLocal() as db:
            repo = SavedSearchRepository(db)
            repo.claim()
            row = repo.get(definition.id)
            if row and row.run_id == target['run_id']:
                row.run_state = None
                row.last_outcome, row.last_finished_at = result.outcome, result.finished_at
                row.last_result = result.model_dump(mode='json')
                row.error_code = code
                row.error_message = 'Run could not apply. Reload the search and try again.'
                db.commit()
    if not target['automatic']:
        from app.services import notification_service
        notification_service.scraping_completed({'processed': 0, 'saved_search_id': definition.id,
            'failures': int(result.outcome == 'failed'),
            'saved_searches': aggregate([result])})
    return result


def aggregate(results):
    return dict(searches=len(results), **{name: sum(getattr(r, name) for r in results) for name in (
        'added', 'existing', 'excluded_candidates', 'unresolved_candidates', 'deferred_candidates')},
        **{name: sum(r.outcome == name for r in results) for name in ('complete', 'partial', 'failed', 'skipped', 'interrupted')})


def run_reserved_batch(targets, shutdown):
    deadline = time.monotonic() + 300
    results = []
    deferred = 0
    for target in targets:
        if shutdown.is_set() or time.monotonic() >= deadline:
            deferred += 1
            with SessionLocal() as db:
                repo = SavedSearchRepository(db)
                repo.claim()
                row = repo.get(target['definition']['id'])
                if row and row.run_id == target['run_id']:
                    row.run_state = None
                    row.last_outcome = 'skipped'
                    row.last_finished_at = _utcnow()
                    row.error_code = 'shutdown' if shutdown.is_set() else 'batch_budget'
                    row.error_message = 'Deferred until the next source refresh or Run now.'
                    row.last_result = None
                    db.commit()
            continue
        results.append(execute_target(target, shutdown, deadline=min(deadline, time.monotonic() + 120)))
    return dict(aggregate(results), deferred_searches=deferred)
