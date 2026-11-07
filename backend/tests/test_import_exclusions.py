"""Admission preserves existing inventory and operator choices across imports."""
import pytest
from app.schemas.import_exclusions import ExclusionInput, normalized_rule
from app.services.import_exclusion_service import ImportExclusionService, PolicySnapshot


def test_literal_unicode_matching():
    p = PolicySnapshot(1, ((1, 'name_contains', 'é %_[]'), (2, 'name_equals', '123')))
    assert p.matches('', '  É   %_[]  HD') == [1]
    assert p.matches('', '123') == [2]
    assert not p.matches('', 'e %_[]')
    assert normalized_rule('stream_id_equals', 'A' * 40) == 'a' * 40
    with pytest.raises(ValueError):
        normalized_rule('name_contains', '\x00')


def test_rule_crud_revision_preview(client, db_session):
    from app.models.models import AcestreamChannel
    db_session.add(AcestreamChannel(id='a' * 40, name='É Sport', is_active=False))
    db_session.commit()
    payload = dict(kind='name_contains', value='é  sport')
    created = client.post('/api/v1/import-exclusions', json=payload)
    assert created.status_code == 201, created.text
    data = created.json()
    assert data['policy_revision'] == 1
    assert client.post('/api/v1/import-exclusions', json=payload).status_code == 409
    preview = client.post('/api/v1/import-exclusions/preview', json=payload).json()
    assert preview['matched'] == 1 and preview['complete']
    assert db_session.get(AcestreamChannel, 'a' * 40).is_active is False
    rid = data['rule']['id']
    assert client.get(f'/api/v1/import-exclusions?rule_id={rid}').json()['items'][0]['id'] == rid
    assert client.get('/api/v1/import-exclusions?rule_id=9999').json()['total'] == 0
    assert client.patch(f'/api/v1/import-exclusions/{rid}', json={**payload, 'expected_revision': 4}).status_code == 409
    assert client.delete(f'/api/v1/import-exclusions/{rid}?expected_revision=1').status_code == 204


def test_manual_override_is_explicit(client):
    client.post('/api/v1/import-exclusions', json=dict(kind='name_equals', value='Blocked'))
    payload = dict(id='b' * 40, name='Blocked')
    blocked = client.post('/api/v1/channels/', json=payload)
    assert blocked.status_code == 409
    assert blocked.json()['error']['code'] == 'IMPORT_EXCLUDED'
    assert client.post('/api/v1/channels/', json={**payload, 'allow_excluded': True}).status_code == 201


def test_additive_ingestion_does_not_touch_excluded_existing(db_session):
    from app.models.models import AcestreamChannel
    from app.schemas.extraction import ExtractedChannel
    from app.services.incremental_ingestion_service import ingest_records
    cid = 'a' * 40
    row = AcestreamChannel(id=cid, name='Operator', is_active=False, is_online=True, group='Mine')
    db_session.add(row)
    db_session.commit()
    before = row.last_seen
    ImportExclusionService(db_session).save(ExclusionInput(kind='stream_id_equals', value=cid))
    assert ingest_records(db_session, [ExtractedChannel(channel_id=cid, name='Publisher')], 'new') == 0
    db_session.commit()
    db_session.refresh(row)
    assert (row.name, row.group, row.is_active, row.is_online, row.last_seen) == ('Operator', 'Mine', False, True, before)


@pytest.mark.asyncio
async def test_scraper_raw_observations_protect_excluded_rows(db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.services.scraper_service import ScraperService
    from unittest.mock import AsyncMock, MagicMock
    url = 'https://example.org/list'
    for letter, name in [('a', 'Allowed'), ('b', 'Blocked'), ('c', 'Absent'), ('d', 'Blocked absent')]:
        db_session.add(AcestreamChannel(id=letter * 40, name=name, source_url=url, is_active=False))
    db_session.commit()
    ImportExclusionService(db_session).save(ExclusionInput(kind='name_contains', value='blocked'))
    scraper = MagicMock()
    scraper.url_obj.get_normalized_url.return_value = url
    scraper.scrape = AsyncMock(return_value=([('a' * 40, 'Updated', {}), ('b' * 40, 'Blocked incoming', {})], 'OK'))
    monkeypatch.setattr('app.services.scraper_service.create_scraper_for_url', lambda *args: scraper)
    result, status = await ScraperService(db_session).scrape_url(url)
    assert status == 'OK'
    assert [r.channel_id for r in result] == ['a' * 40]
    assert db_session.get(AcestreamChannel, 'b' * 40).name == 'Blocked'
    assert db_session.get(AcestreamChannel, 'd' * 40).name == 'Blocked absent'
    assert db_session.get(AcestreamChannel, 'c' * 40) is None


def test_w3u_review_survives_exclusion_but_never_marks_skipped_imported(db_session):
    import json
    from app.services.catalogue_service import CatalogueService
    from app.schemas.catalogue import CataloguePreviewRequest, CatalogueSaveRequest
    from app.models.models import AcestreamChannel
    policy = ImportExclusionService(db_session)
    rule = policy.save(ExclusionInput(kind='name_contains', value='blocked')).rule
    service = CatalogueService(db_session)
    preview = service.preview(CataloguePreviewRequest(sample=json.dumps({'name': 'Catalogue', 'stations': [
        {'name': 'Blocked', 'url': 'acestream://' + 'b' * 40}]})))
    entry = next(e for e in preview.entries if e.channel_id)
    assert entry.excluded_rule_ids == [rule.id]
    saved = service.save(CatalogueSaveRequest(preview_token=preview.preview_token, name='Catalogue', selected_branches=['root'], confirm_live=True))
    assert not next(e for e in saved.entries if e.channel_id).imported
    assert db_session.query(AcestreamChannel).count() == 0
    policy.delete(rule.id, rule.revision)
    refreshed = service.refresh(saved.id)
    assert next(e for e in refreshed.entries if e.channel_id).imported
    assert db_session.get(AcestreamChannel, 'b' * 40) is not None


def test_policy_changed_after_w3u_preview_rejects_save(db_session):
    import json
    from app.api.error_handlers import APIError
    from app.services.catalogue_service import CatalogueService
    from app.schemas.catalogue import CataloguePreviewRequest, CatalogueSaveRequest
    service = CatalogueService(db_session)
    preview = service.preview(CataloguePreviewRequest(sample=json.dumps({'name': 'Test', 'stations': [{'name': 'Sports', 'url': 'acestream://' + 'a' * 40}]})))
    ImportExclusionService(db_session).save(ExclusionInput(kind='name_contains', value='sport'))
    with pytest.raises(APIError) as error:
        service.save(CatalogueSaveRequest(preview_token=preview.preview_token, name='Test', selected_branches=['root'], confirm_live=True))
    assert error.value.code == 'IMPORT_POLICY_CHANGED'


def test_telegram_all_excluded_advances_cursor_without_replaying_on_rule_removal(alembic_backend_runtime):
    from app.repositories import telegram_repository as repo
    from app.services.telegram.ingestion import record
    from app.schemas.telegram import TelegramSourceConfig
    from app.schemas.extraction import RecipePreview, ExtractedChannel
    from app.models.models import AcestreamChannel
    runtime = alembic_backend_runtime
    source = repo.save_source('account', TelegramSourceConfig(name='Test', chat_id='-100123'), 'Test', {}, 0)
    _, generation = repo.snapshot(source.id, 'account')
    with runtime.SessionLocal() as db:
        rule = ImportExclusionService(db).save(ExclusionInput(kind='name_contains', value='blocked')).rule
    preview = RecipePreview(channels=[ExtractedChannel(channel_id='a' * 40, name='Blocked')], record_count=1, invalid_count=0, duplicate_count=0, issues=[])
    assert record(source.id, 'account', generation, 1, 'revision', preview, True)
    updated = repo.snapshot(source.id, 'account')[0]
    assert (updated.cursor, updated.imported_count, updated.excluded_count) == (1, 0, 1)
    with runtime.SessionLocal() as db:
        ImportExclusionService(db).delete(rule.id, rule.revision)
    assert record(source.id, 'account', generation, 1, 'revision', preview, True)
    with runtime.SessionLocal() as db:
        assert db.query(AcestreamChannel).count() == 0


def test_policy_write_claim_serializes_rule_mutation(alembic_backend_runtime):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from app.models.models import AcestreamChannel
    runtime = alembic_backend_runtime
    entered = threading.Event()
    def edit():
        entered.set()
        with runtime.SessionLocal() as other:
            return ImportExclusionService(other).save(ExclusionInput(kind='name_equals', value='Sports'))
    with runtime.SessionLocal() as db, ThreadPoolExecutor(1) as pool:
        policy = ImportExclusionService(db).snapshot(claim=True)
        future = pool.submit(edit)
        assert entered.wait(2)
        assert not policy.matches('a' * 40, 'Sports')
        db.add(AcestreamChannel(id='a' * 40, name='Sports'))
        db.commit()
        assert future.result(5).policy_revision == 1
        assert ImportExclusionService(db).snapshot().matches('a' * 40, 'Sports')
        assert db.get(AcestreamChannel, 'a' * 40).name == 'Sports'


def test_failed_scrape_rolls_back_pruning_and_new_tv_assignment(db_session, monkeypatch):
    from app.models.models import AcestreamChannel, TVChannel, EPGSource, EPGChannel
    from app.repositories.channel_repository import ChannelRepository
    from app.services.scraper_service import _apply_scrape
    url = 'https://example.org/list'
    guide = EPGSource(name='Guide', url='https://example.org/guide.xml')
    db_session.add(guide)
    db_session.flush()
    db_session.add(EPGChannel(epg_source_id=guide.id, channel_xml_id='sport', name='Sport'))
    db_session.add(AcestreamChannel(id='a' * 40, name='Retain on failure', source_url=url))
    db_session.commit()
    def fail(self, **kwargs):
        # The TV row was flushed inside the same ingestion transaction.
        assert self.db.query(TVChannel).filter_by(epg_id='sport').count() == 1
        raise RuntimeError('injected channel write failure')
    monkeypatch.setattr(ChannelRepository, 'create_or_update_channel', fail)
    with pytest.raises(RuntimeError, match='injected'):
        _apply_scrape(db_session.get_bind(), [('b' * 40, 'Sport', {'tvg_id': 'sport'})], url, url, False, 'OK')
    db_session.expire_all()
    assert db_session.get(AcestreamChannel, 'a' * 40) is not None
    assert db_session.get(AcestreamChannel, 'b' * 40) is None
    assert db_session.query(TVChannel).count() == 0


@pytest.mark.parametrize('status,recipe', [('Partial', False), ('Error: upstream', False), ('OK', True)])
def test_non_authoritative_scrape_keeps_absent_inventory(db_session, status, recipe):
    from app.models.models import AcestreamChannel
    from app.services.scraper_service import _apply_scrape
    url = 'https://example.org/list'
    db_session.add(AcestreamChannel(id='a' * 40, name='Absent', source_url=url))
    db_session.commit()
    _apply_scrape(db_session.get_bind(), [('b' * 40, 'Present', {})], url, url, recipe, status)
    assert db_session.get(AcestreamChannel, 'a' * 40) is not None


def test_all_excluded_scrape_preserves_metadata_and_protects_followup_matching(db_session, monkeypatch):
    from app.models.models import AcestreamChannel, TVChannel
    from app.services.scraper_service import _apply_scrape
    from app.services.epg_matching_automation import EPGMatchingAutomation
    url = 'https://example.org/list'
    row = AcestreamChannel(id='a' * 40, name='Operator name', source_url=url, is_active=False, is_online=True)
    db_session.add(row)
    db_session.commit()
    before = row.last_seen
    ImportExclusionService(db_session).save(ExclusionInput(kind='name_contains', value='publisher'))
    protected = []
    monkeypatch.setattr(EPGMatchingAutomation, 'run', lambda self, **kw: protected.extend(kw['import_excluded_ids']))
    channels, excluded = _apply_scrape(db_session.get_bind(), [('a' * 40, 'Publisher name', {'tvg_id': 'guide'})], url, url, False, 'OK')
    db_session.refresh(row)
    assert channels == [] and excluded == 1 and protected == ['a' * 40]
    assert (row.name, row.is_active, row.is_online, row.last_seen, row.tv_channel_id) == ('Operator name', False, True, before, None)
    assert db_session.query(TVChannel).count() == 0
