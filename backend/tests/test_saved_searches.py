"""Authoritative, additive saved-search lifecycle and bounded upstream handling."""
import threading
import httpx
import pytest
from app.models.models import AcestreamChannel, SavedSearchChannel
from app.repositories.settings_repository import SettingsRepository
from app.schemas.saved_searches import SavedSearchInput, SavedSearchUpdate, SavedSearchPreviewRequest
from app.schemas.import_exclusions import ExclusionInput
from app.services.saved_search_service import SavedSearchService, prepare_target, execute_target
from app.services.import_exclusion_service import ImportExclusionService
from app.services.search_catalogue_client import SearchCatalogueClient, CatalogueReadError, flatten_results
from app.services.search_preview_store import recall

A, B, C = 'a' * 40, 'b' * 40, 'c' * 40


def definition(**kw):
    return SavedSearchInput(**dict(name='Sports', query='Sports [ES]', **kw))


def test_save_is_configuration_only_and_duplicates_conflict(client, db_session, monkeypatch):
    monkeypatch.setattr(SearchCatalogueClient, 'get', lambda *args: pytest.fail('Save must not fetch'))
    response = client.post('/api/v1/saved-searches', json=definition().model_dump())
    assert response.status_code == 201, response.text
    row = response.json()
    assert not row['refresh_enabled'] and row['last_outcome'] is None
    assert db_session.query(AcestreamChannel).count() == 0
    duplicate = client.post('/api/v1/saved-searches', json={**definition().model_dump(), 'name': 'Other'})
    assert duplicate.status_code == 409
    assert duplicate.json()['error']['context']['saved_search_id'] == row['id']
    changed = client.patch(f"/api/v1/saved-searches/{row['id']}", json={**definition().model_dump(), 'query': 'News', 'refresh_enabled': True, 'expected_revision': 1})
    assert changed.status_code == 200 and not changed.json()['refresh_enabled']
    assert client.delete(f"/api/v1/saved-searches/{row['id']}?expected_revision=1").status_code == 409


def test_flatten_numeric_names_and_invalid_entries():
    candidates, total, invalid, capped = flatten_results({'result': {'total': 2, 'results': [
        {'name': 123, 'items': [{'infohash': A}, {'infohash': 'bad'}]}, {'name': 'Other', 'infohash': B}]}})
    assert candidates[0]['name'] == '123'
    assert len(candidates) == 2 and invalid == 1 and not capped


@pytest.mark.parametrize('payload', [None, [], {}, {'result': {'total': 1, 'results': None}}, {'result': {'total': '1', 'results': []}}])
def test_malformed_payload_is_not_empty_success(payload):
    with pytest.raises(CatalogueReadError):
        flatten_results(payload)


def test_client_repeated_pages_and_authoritative_resolution():
    paths = []
    def handler(request):
        paths.append(request.url.path)
        if request.url.path == '/search':
            return httpx.Response(200, json={'result': {'total': 500, 'results': [{'name': 'Sport', 'infohash': A}]}})
        assert request.url.params['method'] == 'get_content_id'
        return httpx.Response(200, json={'result': {'content_id': B.upper()}})
    with SearchCatalogueClient('http://engine:6878', transport=httpx.MockTransport(handler)) as client:
        candidates, counts = client.collect('Sport', '')
        assert len(candidates) == 1 and counts['stop_reason'] == 'repeated_page'
        assert client.resolve(A) == B
    assert paths == ['/search', '/search', '/server/api']


@pytest.mark.parametrize('kind', ['redirect', 'oversized', 'json', 'timeout'])
def test_client_failure_is_safe_and_bounded(kind, monkeypatch):
    monkeypatch.setattr('app.services.search_catalogue_client.MAX_RESPONSE_BYTES', 100)
    def handler(request):
        if kind == 'redirect':
            return httpx.Response(302, headers={'Location': 'http://private/secret'})
        if kind == 'oversized':
            return httpx.Response(200, content=b'x' * 101)
        if kind == 'timeout':
            raise httpx.ReadTimeout('private details')
        return httpx.Response(200, content=b'private invalid json')
    with SearchCatalogueClient('http://engine', transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CatalogueReadError) as error:
            client.get('/search', {})
        assert 'private' not in str(error.value)


def test_canonical_import_mixed_outcomes_and_preserves_existing(client, db_session, monkeypatch):
    SettingsRepository(db_session).set_setting('ace_engine_url', 'http://engine')
    row = AcestreamChannel(id=B, name='Operator', is_active=False, is_online=True, source_url='mine')
    db_session.add(row)
    db_session.commit()
    ImportExclusionService(db_session).save(ExclusionInput(kind='name_contains', value='blocked'))
    def resolve(self, ih):
        if ih == C:
            raise CatalogueReadError('unresolved')
        return B
    monkeypatch.setattr(SearchCatalogueClient, 'resolve', resolve)
    response = client.post('/api/v1/search/import', json={'items': [
        {'infohash': A, 'name': 'Publisher'}, {'infohash': B, 'name': 'Blocked'}, {'infohash': C, 'name': 'Unresolved'}]})
    assert response.status_code == 200, response.text
    assert [r['outcome'] for r in response.json()['items']] == ['existing', 'excluded', 'unresolved']
    db_session.refresh(row)
    assert (row.name, row.is_active, row.is_online, row.source_url) == ('Operator', False, True, 'mine')
    assert db_session.get(AcestreamChannel, A) is None
    assert db_session.get(AcestreamChannel, C) is None


def seed(runtime):
    with runtime.SessionLocal() as db:
        SettingsRepository(db).set_setting('ace_engine_url', 'http://engine')
        return SavedSearchService(db).save(definition())


def fake_engine(monkeypatch):
    monkeypatch.setattr(SearchCatalogueClient, 'collect', lambda *args: ([{'infohash': A, 'name': 'Sports', 'category': ''}], dict(pages_fetched=1, candidates_seen=1, unique_infohashes=1)))
    monkeypatch.setattr(SearchCatalogueClient, 'resolve', lambda *args: B)


def test_execution_memberships_delete_preserves_inventory(alembic_backend_runtime, monkeypatch):
    runtime = alembic_backend_runtime
    fake_engine(monkeypatch)
    row = seed(runtime)
    target = prepare_target('run1', dict(definition=row.model_dump(mode='json'), automatic=False, preview=None))
    result = execute_target(target, threading.Event())
    assert result.outcome == 'complete' and result.added == 1
    with runtime.SessionLocal() as db:
        assert db.get(AcestreamChannel, A) is None
        channel = db.get(AcestreamChannel, B)
        assert channel.is_online is None
        channel.name, channel.is_active, channel.is_online = 'Mine', False, True
        db.commit()
    target = prepare_target('run2', dict(definition=row.model_dump(mode='json'), automatic=False, preview=None))
    assert execute_target(target, threading.Event()).existing == 1
    with runtime.SessionLocal() as db:
        channel = db.get(AcestreamChannel, B)
        assert (channel.name, channel.is_active, channel.is_online) == ('Mine', False, True)
        assert db.query(SavedSearchChannel).count() == 1
        SavedSearchService(db).delete(row.id, row.revision)
        assert db.query(SavedSearchChannel).count() == 0
        assert db.get(AcestreamChannel, B) is not None


def test_preview_is_private_read_only_and_revision_bound(alembic_backend_runtime, monkeypatch):
    runtime = alembic_backend_runtime
    fake_engine(monkeypatch)
    row = seed(runtime)
    with runtime.SessionLocal() as db:
        service = SavedSearchService(db)
        preview = service.preview(SavedSearchPreviewRequest(saved_search_id=row.id, expected_revision=row.revision))
        assert preview.result.added == 1 and db.query(AcestreamChannel).count() == 0
        private = recall(preview.preview_token)
        ImportExclusionService(db).save(ExclusionInput(kind='name_contains', value='sports'))
    target = prepare_target('run', dict(definition=row.model_dump(mode='json'), automatic=False, preview=private))
    result = execute_target(target, threading.Event())
    assert result.stop_reason == 'IMPORT_POLICY_CHANGED'
    with runtime.SessionLocal() as db:
        assert db.query(AcestreamChannel).count() == 0


def test_edited_target_during_fetch_cannot_apply(alembic_backend_runtime, monkeypatch):
    runtime = alembic_backend_runtime
    fake_engine(monkeypatch)
    row = seed(runtime)
    def resolve(*args):
        with runtime.SessionLocal() as db:
            SavedSearchService(db).save(SavedSearchUpdate(name='Changed', query='News', expected_revision=1), row.id)
        return B
    monkeypatch.setattr(SearchCatalogueClient, 'resolve', resolve)
    target = prepare_target('run', dict(definition=row.model_dump(mode='json'), automatic=False, preview=None))
    assert execute_target(target, threading.Event()).stop_reason == 'SAVED_SEARCH_CHANGED'
    with runtime.SessionLocal() as db:
        assert db.query(AcestreamChannel).count() == 0
        assert SavedSearchService(db).get(row.id).run_state is None


def test_missing_engine_skipped_and_restart_interrupts(alembic_backend_runtime):
    from app.repositories.saved_search_repository import SavedSearchRepository
    runtime = alembic_backend_runtime
    row = seed(runtime)
    with runtime.SessionLocal() as db:
        SettingsRepository(db).set_setting('ace_engine_url', '')
    target = prepare_target('run', dict(definition=row.model_dump(mode='json'), automatic=False, preview=None))
    result = execute_target(target, threading.Event())
    assert result.outcome == 'skipped' and result.stop_reason == 'SEARCH_ENGINE_UNCONFIGURED'
    prepare_target('orphan', dict(definition=row.model_dump(mode='json'), automatic=False, preview=None))
    with runtime.SessionLocal() as db:
        SavedSearchRepository(db).interrupt_orphans()
        latest = SavedSearchService(db).get(row.id)
        assert latest.run_state is None and latest.last_outcome == 'interrupted'


def test_preview_cache_eviction_and_expiry_are_explicit(monkeypatch):
    from app.services import search_preview_store as store
    from app.api.error_handlers import APIError
    with store._LOCK:
        store._CACHE.clear()
    first = store.remember({'candidates': []})
    for _ in range(8):
        store.remember({'candidates': []})
    with pytest.raises(APIError) as error:
        store.recall(first)
    assert error.value.status_code == 410
    monkeypatch.setattr(store, 'TTL', -1)
    expired = store.remember({'candidates': []})
    with pytest.raises(APIError) as error:
        store.recall(expired)
    assert error.value.code == 'SEARCH_PREVIEW_EXPIRED'


def test_whole_request_deadline_cancels_before_releasing_slot(monkeypatch):
    import asyncio
    from app.services import search_catalogue_client as module
    cleaned = threading.Event()
    async def slow(request):
        try:
            await asyncio.sleep(1)
        finally:
            cleaned.set()
        return httpx.Response(200, json={})
    monkeypatch.setattr(module, 'REQUEST_SECONDS', .02)
    with SearchCatalogueClient('http://engine', transport=httpx.MockTransport(slow)) as client:
        with pytest.raises(CatalogueReadError) as error:
            client.get('/search', {})
    assert error.value.code == 'deadline' and cleaned.is_set()
    assert module.ENGINE_SLOTS.acquire(blocking=False)
    assert module.ENGINE_SLOTS.acquire(blocking=False)
    module.ENGINE_SLOTS.release()
    module.ENGINE_SLOTS.release()


def test_duplicate_resolution_and_changed_early_policy_are_truthful(db_session):
    from app.services.search_import_service import resolve_candidates, apply_candidates
    from app.services.import_exclusion_service import PolicySnapshot
    from unittest.mock import Mock
    engine = Mock()
    engine.resolve.return_value = B
    before = PolicySnapshot(1, ((1, 'name_contains', 'blocked'),))
    candidates = resolve_candidates(engine, [dict(infohash=A, name='Blocked'), dict(infohash=B, name='Good'), dict(infohash=B, name='Good'), dict(infohash=C, name='Alias')], before)
    assert engine.resolve.call_count == 2
    result = apply_candidates(db_session, candidates, PolicySnapshot(2, ()))
    assert [i.outcome for i in result.items] == ['deferred', 'added', 'duplicate', 'duplicate']
    assert result.deferred == 1 and result.added == 1
    db_session.rollback()


def test_prepared_preview_does_not_fetch_new_discoveries(alembic_backend_runtime, monkeypatch):
    runtime = alembic_backend_runtime
    fake_engine(monkeypatch)
    row = seed(runtime)
    with runtime.SessionLocal() as db:
        preview = SavedSearchService(db).preview(SavedSearchPreviewRequest(saved_search_id=row.id, expected_revision=row.revision))
    target = prepare_target('run', dict(definition=row.model_dump(mode='json'), automatic=False, preview=recall(preview.preview_token)))
    monkeypatch.setattr(SearchCatalogueClient, 'collect', lambda *args: pytest.fail('Snapshot run must not fetch again'))
    assert execute_target(target, threading.Event()).added == 1


def test_channel_delete_removes_search_membership(alembic_backend_runtime, monkeypatch):
    from app.repositories.channel_repository import ChannelRepository
    runtime = alembic_backend_runtime
    fake_engine(monkeypatch)
    row = seed(runtime)
    target = prepare_target('run', dict(definition=row.model_dump(mode='json'), automatic=False, preview=None))
    execute_target(target, threading.Event())
    with runtime.SessionLocal() as db:
        ChannelRepository(db).delete_channel(B)
        assert db.query(SavedSearchChannel).count() == 0
        assert SavedSearchService(db).get(row.id).name == row.name


@pytest.mark.parametrize('mode,outcome,added', [
    ('empty', 'complete', 0), ('partial', 'partial', 1),
    ('unresolved', 'partial', 0), ('deadline', 'partial', 0),
    ('failed', 'failed', 0), ('excluded', 'complete', 0),
])
def test_execution_outcomes_do_not_infer_signal_or_remove_inventory(alembic_backend_runtime, monkeypatch, mode, outcome, added):
    runtime = alembic_backend_runtime
    row = seed(runtime)
    fake_engine(monkeypatch)
    with runtime.SessionLocal() as db:
        db.add(AcestreamChannel(id=C, name='Existing', is_online=True))
        db.commit()
        if mode == 'excluded':
            ImportExclusionService(db).save(ExclusionInput(kind='name_contains', value='sports'))
    if mode in ('empty', 'failed'):
        monkeypatch.setattr(SearchCatalogueClient, 'collect', lambda *args: ([], dict(
            pages_fetched=1 if mode == 'empty' else 0,
            stop_reason=None if mode == 'empty' else 'SEARCH_ENGINE_UNAVAILABLE')))
    elif mode == 'partial':
        monkeypatch.setattr(SearchCatalogueClient, 'collect', lambda *args: (
            [{'infohash': A, 'name': 'Sports'}], dict(pages_fetched=1, stop_reason='page_limit')))
    elif mode in ('unresolved', 'deadline'):
        def resolve(*args):
            raise CatalogueReadError(mode)
        monkeypatch.setattr(SearchCatalogueClient, 'resolve', resolve)
    target = prepare_target('run', dict(definition=row.model_dump(mode='json'), automatic=False, preview=None))
    result = execute_target(target, threading.Event())
    assert (result.outcome, result.added) == (outcome, added)
    if mode == 'deadline':
        assert result.stop_reason == 'deadline' and result.deferred_candidates == 1
    with runtime.SessionLocal() as db:
        assert db.get(AcestreamChannel, C).is_online is True
        assert db.get(AcestreamChannel, A) is None
        latest = SavedSearchService(db).get(row.id)
        assert bool(latest.last_success_at) == (outcome == 'complete')
        assert latest.run_state is None


@pytest.mark.parametrize('change', ['pause', 'delete', 'shutdown'])
def test_waiting_target_revalidates_before_any_import(alembic_backend_runtime, monkeypatch, change):
    runtime = alembic_backend_runtime
    row = seed(runtime)
    with runtime.SessionLocal() as db:
        row = SavedSearchService(db).save(SavedSearchUpdate(**definition(refresh_enabled=True).model_dump(), expected_revision=row.revision), row.id)
    target = prepare_target('waiting', dict(definition=row.model_dump(mode='json'), automatic=True, preview=None))
    shutdown = threading.Event()
    with runtime.SessionLocal() as db:
        if change == 'delete':
            SavedSearchService(db).delete(row.id, row.revision)
        elif change == 'pause':
            SavedSearchService(db).save(SavedSearchUpdate(**definition().model_dump(), expected_revision=row.revision), row.id)
        else:
            shutdown.set()
    monkeypatch.setattr(SearchCatalogueClient, 'get', lambda *args: pytest.fail('Stale or stopping target must not fetch'))
    result = execute_target(target, shutdown)
    assert result.outcome in ('skipped', 'interrupted')
    with runtime.SessionLocal() as db:
        assert db.query(AcestreamChannel).count() == 0
