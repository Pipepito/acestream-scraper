"""Behaviour of the five channel import paths, pinned before they share a pipeline.

Lists (snapshot), W3U catalogues, Telegram messages and saved searches
(insert-only) and manual Add each decide what to insert, update, retain and
prune. These tests record those decisions as they are, so that moving the
paths onto one import pipeline cannot change any result. Synthetic data only.
"""
import json
from datetime import datetime, timezone

import pytest

from app.schemas.import_exclusions import ExclusionInput
from app.services.import_exclusion_service import ImportExclusionService, PolicySnapshot

A, B, C, D, E = ('a' * 40, 'b' * 40, 'c' * 40, 'd' * 40, 'e' * 40)
LIST_URL = 'https://lists.example.invalid/channels.m3u'
OLD = datetime(2020, 1, 1, tzinfo=timezone.utc)


def _channel(db, cid, name, **fields):
    from app.models.models import AcestreamChannel
    row = AcestreamChannel(id=cid, name=name, last_seen=OLD, **fields)
    db.add(row)
    return row


def _exclude(db, kind, value):
    return ImportExclusionService(db).save(ExclusionInput(kind=kind, value=value)).rule


def _as_utc(value):
    return value if value is None or value.tzinfo else value.replace(tzinfo=timezone.utc)


# Lists: snapshot mode ---------------------------------------------------------

def test_list_snapshot_upserts_inserts_retains_and_prunes(db_session):
    from app.models.models import AcestreamChannel, SavedSearch, SavedSearchChannel
    from app.services.scraper_service import _apply_scrape
    alias = LIST_URL + '?alias'
    _channel(db_session, A, 'Old name', source_url=alias, group='Old group', logo='https://example.invalid/old.png',
             tvg_id='old.id', tvg_name='Old', is_active=False, is_online=True,
             stream_url='https://media.example.invalid/a.m3u8', stream_headers={'Referer': 'https://example.invalid/'})
    _channel(db_session, B, 'Absent', source_url=LIST_URL)
    _channel(db_session, C, 'Other list', source_url='https://other.example.invalid/list.m3u')
    search = SavedSearch(name='Search', query='q', category='all', fingerprint='f' * 64)
    db_session.add(search)
    db_session.flush()
    db_session.add(SavedSearchChannel(saved_search_id=search.id, channel_id=B))
    db_session.commit()

    channels, excluded = _apply_scrape(db_session.get_bind(), [
        (A, 'New name', {'group_title': 'News', 'tvg_logo': 'https://example.invalid/a.png', 'tvg_id': 'a.id', 'tvg_name': 'A'}),
        (D, 'Added', {'group': 'Fallback group', 'logo': 'https://example.invalid/d.png',
                      'stream_url': 'https://media.example.invalid/d.m3u8', 'stream_headers': {'User-Agent': 'Example'}}),
    ], alias, LIST_URL, False, 'OK')
    db_session.expire_all()

    assert excluded == 0
    assert [c.channel_id for c in channels] == [A, D]
    assert channels[0].metadata == {'group': 'News', 'logo': 'https://example.invalid/a.png', 'tvg_id': 'a.id',
                                    'tvg_name': 'A', 'source_url': LIST_URL, 'tv_channel_id': None}
    updated = db_session.get(AcestreamChannel, A)
    assert (updated.name, updated.group, updated.logo, updated.tvg_id, updated.tvg_name, updated.source_url) == (
        'New name', 'News', 'https://example.invalid/a.png', 'a.id', 'A', LIST_URL)
    # The list never decides visibility, and its unknown signal leaves a probe result alone.
    assert (updated.is_active, updated.is_online) == (False, True)
    # A list that stops carrying a URL keeps the stored one and its headers.
    assert (updated.stream_url, updated.stream_headers) == (
        'https://media.example.invalid/a.m3u8', {'Referer': 'https://example.invalid/'})
    assert _as_utc(updated.last_seen) > OLD
    added = db_session.get(AcestreamChannel, D)
    assert (added.name, added.group, added.logo, added.source_url, added.is_active, added.is_online) == (
        'Added', 'Fallback group', 'https://example.invalid/d.png', LIST_URL, True, None)
    assert (added.stream_url, added.stream_headers) == ('https://media.example.invalid/d.m3u8', {'User-Agent': 'Example'})
    assert (added.tvg_id, added.tvg_name) == (None, None)
    # Absent from the list it came from: pruned together with its memberships.
    assert db_session.get(AcestreamChannel, B) is None
    assert db_session.query(SavedSearchChannel).count() == 0
    assert db_session.get(AcestreamChannel, C).name == 'Other list'


def test_list_snapshot_clears_guide_fields_the_list_stops_publishing(db_session):
    from app.models.models import AcestreamChannel
    from app.services.scraper_service import _apply_scrape
    _channel(db_session, A, 'Name', source_url=LIST_URL, group='Group', logo='https://example.invalid/a.png',
             tvg_id='a.id', tvg_name='A')
    db_session.commit()
    _apply_scrape(db_session.get_bind(), [(A, 'Name', {})], LIST_URL, LIST_URL, False, 'OK')
    db_session.expire_all()
    row = db_session.get(AcestreamChannel, A)
    assert (row.group, row.logo, row.tvg_id, row.tvg_name) == (None, None, None, None)


@pytest.mark.parametrize('incoming,status,recipe', [
    ([], 'OK', False),                                    # empty snapshot
    ([(B, 'Present', {})], 'OK', True),                   # custom recipe
    ([(B, 'Present', {})], 'Partial', False),             # any status other than exactly 'OK'
    ([(B, 'Present', {})], 'ok', False),
    ([(B, 'Present', {})], 'OK ', False),
    ([(B, 'Present', {})], 'Extracted 1 channels from direct M3U file', False),
    ([(B, 'Present', {})], 'Error: upstream', False),
])
def test_list_snapshot_prunes_only_complete_automatic_ok_snapshots(db_session, incoming, status, recipe):
    from app.models.models import AcestreamChannel
    from app.services.scraper_service import _apply_scrape
    _channel(db_session, A, 'Absent', source_url=LIST_URL)
    db_session.commit()
    _apply_scrape(db_session.get_bind(), incoming, LIST_URL, LIST_URL, recipe, status)
    db_session.expire_all()
    assert db_session.get(AcestreamChannel, A) is not None


def test_list_snapshot_left_empty_by_exclusions_never_prunes(db_session):
    from app.models.models import AcestreamChannel
    from app.services.scraper_service import _apply_scrape
    _channel(db_session, A, 'Absent', source_url=LIST_URL)
    db_session.commit()
    _exclude(db_session, 'name_contains', 'blocked')
    channels, excluded = _apply_scrape(db_session.get_bind(), [(B, 'Blocked', {})], LIST_URL, LIST_URL, False, 'OK')
    db_session.expire_all()
    assert (channels, excluded) == ([], 1)
    assert db_session.get(AcestreamChannel, A) is not None
    assert db_session.get(AcestreamChannel, B) is None


def test_list_snapshot_with_ok_status_does_prune(db_session):
    """Control for the test above: the same data with 'OK' and no recipe prunes."""
    from app.models.models import AcestreamChannel
    from app.services.scraper_service import _apply_scrape
    _channel(db_session, A, 'Absent', source_url=LIST_URL)
    db_session.commit()
    _apply_scrape(db_session.get_bind(), [(B, 'Present', {})], LIST_URL, LIST_URL, False, 'OK')
    db_session.expire_all()
    assert db_session.get(AcestreamChannel, A) is None


def test_list_snapshot_excludes_by_identity_across_duplicate_entries(db_session):
    """One excluded spelling of an ID drops every entry with that ID."""
    from app.models.models import AcestreamChannel
    from app.services.scraper_service import _apply_scrape
    _exclude(db_session, 'name_contains', 'blocked')
    channels, excluded = _apply_scrape(db_session.get_bind(), [
        (A, 'Blocked', {}), (A, 'Allowed spelling', {}), (B, 'Allowed', {}), (B, 'Allowed twice', {}),
    ], LIST_URL, LIST_URL, False, 'OK')
    db_session.expire_all()
    assert excluded == 1
    assert [c.channel_id for c in channels] == [B, B]
    assert db_session.get(AcestreamChannel, A) is None
    assert db_session.get(AcestreamChannel, B).name == 'Allowed twice'


ZERO_SITE = '1ExampleZeroNetSiteAddressXXXXXXX'


@pytest.mark.asyncio
@pytest.mark.parametrize('path,content', [
    ('channels.m3u', f'#EXTM3U\n#EXTINF:-1,Present\nacestream://{B}\n'),
    ('channels.m3u8', f'#EXTM3U\n#EXTINF:-1,Present\nacestream://{B}\n'),
    ('links.json', json.dumps({'links': [{'name': 'Present', 'url': f'acestream://{B}'}]})),
])
async def test_zeronet_file_shortcuts_never_prune(db_session, monkeypatch, path, content):
    """ZeroNet's direct M3U/JSON shortcuts report 'Extracted N channels…', not 'OK'."""
    from app.models.models import AcestreamChannel
    from app.scrapers.zeronet import ZeronetScraper
    from app.services.scraper_service import ScraperService

    async def fetch(self, url):
        return content

    async def record(self, url, status, error=None):
        return None
    monkeypatch.setattr(ZeronetScraper, 'fetch_content', fetch)
    monkeypatch.setattr(ZeronetScraper, 'update_url_status', record)
    url = f'zero://{ZERO_SITE}/{path}'
    _channel(db_session, A, 'Absent', source_url=url)
    db_session.commit()
    channels, status = await ScraperService(db_session).scrape_url(url, 'zeronet')
    assert status.startswith('Extracted 1 channels')
    assert [c.channel_id for c in channels] == [B]
    db_session.expire_all()
    assert db_session.get(AcestreamChannel, A) is not None
    assert db_session.get(AcestreamChannel, B).source_url == url


# W3U catalogues: insert-only ---------------------------------------------------

def test_w3u_inserts_missing_only_and_never_prunes(db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.schemas.catalogue import CataloguePreviewRequest, CatalogueSaveRequest
    from app.services.catalogue_service import CatalogueService
    from app.utils.bounded_source import SourceResponse
    document = {'name': 'Catalogue', 'groups': [{'name': 'Sports', 'groups': [{'name': 'Football', 'stations': [
        {'name': 'New', 'url': f'acestream://{A}', 'image': 'https://example.invalid/a.png', 'epgId': 'a.id'},
        {'name': 'Publisher name', 'url': f'acestream://{B}'},
        {'name': 'New again', 'url': f'acestream://{A}'},
    ]}]}]}

    async def get(url, **kwargs):
        return SourceResponse(200, json.dumps(document).encode(), {})
    monkeypatch.setattr('app.services.w3u_parser.source_get', get)
    _channel(db_session, B, 'Operator name', source_url=LIST_URL, group='Mine', is_active=False, is_online=True)
    db_session.commit()
    service = CatalogueService(db_session)
    preview = service.preview(CataloguePreviewRequest(url='https://catalogue.example.invalid/root'))
    saved = service.save(CatalogueSaveRequest(confirm_live=True, preview_token=preview.preview_token, name='Mine',
                                              selected_branches=['root'], refresh_enabled=True))
    assert [e.imported for e in saved.entries if e.channel_id] == [True, True, True]
    db_session.expire_all()
    added = db_session.get(AcestreamChannel, A)
    assert (added.name, added.source_url, added.group, added.logo, added.tvg_id, added.is_online, added.is_active) == (
        'New', f'catalogue:{saved.id}', 'Sports / Football', 'https://example.invalid/a.png', 'a.id', None, True)
    kept = db_session.get(AcestreamChannel, B)
    assert (kept.name, kept.source_url, kept.group, kept.is_active, kept.is_online, _as_utc(kept.last_seen)) == (
        'Operator name', LIST_URL, 'Mine', False, True, OLD)
    # The catalogue drops A: refresh adds nothing and removes nothing.
    document['groups'][0]['groups'][0]['stations'] = [{'name': 'Publisher name', 'url': f'acestream://{B}'}]
    service.refresh(saved.id)
    db_session.expire_all()
    assert db_session.get(AcestreamChannel, A).name == 'New'
    assert db_session.get(AcestreamChannel, B).name == 'Operator name'


def test_w3u_exclusion_applies_per_entry_name(db_session):
    from app.models.models import AcestreamChannel
    from app.schemas.catalogue import CataloguePreviewRequest, CatalogueSaveRequest
    from app.services.catalogue_service import CatalogueService
    rule = _exclude(db_session, 'name_contains', 'blocked')
    service = CatalogueService(db_session)
    preview = service.preview(CataloguePreviewRequest(sample=json.dumps({'stations': [
        {'name': 'Blocked', 'url': f'acestream://{A}'},
        {'name': 'Allowed', 'url': f'acestream://{A}'},
    ]})))
    saved = service.save(CatalogueSaveRequest(confirm_live=True, preview_token=preview.preview_token, name='Mine',
                                              selected_branches=['root']))
    entries = [e for e in saved.entries if e.channel_id]
    assert [(e.imported, e.excluded_rule_ids) for e in entries] == [(False, [rule.id]), (True, [])]
    assert db_session.get(AcestreamChannel, A).name == 'Allowed'


# Telegram: insert-only, existing rows only observed ------------------------------

def test_telegram_ingestion_inserts_missing_and_only_observes_existing(db_session):
    from app.models.models import AcestreamChannel
    from app.schemas.extraction import ExtractedChannel
    from app.services.incremental_ingestion_service import ingest_records
    _channel(db_session, A, 'Operator', source_url=LIST_URL, group='Mine', is_active=False, is_online=True)
    db_session.commit()
    count = ingest_records(db_session, [
        ExtractedChannel(channel_id=A, name='Publisher', metadata={'group_title': 'Theirs'}),
        ExtractedChannel(channel_id=B, name='New', metadata={'group_title': 'Group', 'tvg_logo': 'https://example.invalid/b.png',
                                                             'tvg_id': 'b.id', 'group': 'Ignored'}),
        ExtractedChannel(channel_id=B, name='New twice'),
        ExtractedChannel(channel_id=C, name='Bare'),
    ], 'telegram-source:7')
    db_session.commit()
    db_session.expire_all()
    assert count == 2
    existing = db_session.get(AcestreamChannel, A)
    assert (existing.name, existing.group, existing.source_url, existing.is_active, existing.is_online) == (
        'Operator', 'Mine', LIST_URL, False, True)
    assert _as_utc(existing.last_seen) > OLD
    added = db_session.get(AcestreamChannel, B)
    assert (added.name, added.group, added.logo, added.tvg_id, added.source_url, added.is_online, added.is_active) == (
        'New', 'Group', 'https://example.invalid/b.png', 'b.id', 'telegram-source:7', None, True)
    assert db_session.get(AcestreamChannel, C).group is None


def test_telegram_ingestion_leaves_commit_to_the_caller(db_session):
    from app.models.models import AcestreamChannel
    from app.schemas.extraction import ExtractedChannel
    from app.services.incremental_ingestion_service import ingest_records
    assert ingest_records(db_session, [ExtractedChannel(channel_id=A, name='New')], 'telegram-source:1') == 1
    db_session.rollback()
    assert db_session.get(AcestreamChannel, A) is None


def test_telegram_failure_after_import_rolls_back_channels_and_cursor(alembic_backend_runtime, monkeypatch):
    from sqlalchemy.orm import Session
    from app.models.models import AcestreamChannel
    from app.repositories import telegram_repository as repo
    from app.schemas.extraction import ExtractedChannel, RecipePreview
    from app.schemas.telegram import TelegramSourceConfig
    from app.services.telegram.ingestion import record
    runtime = alembic_backend_runtime
    source = repo.save_source('account', TelegramSourceConfig(name='Example', chat_id='-100123'), 'Example', {}, 0)
    _, generation = repo.snapshot(source.id, 'account')
    preview = RecipePreview(channels=[ExtractedChannel(channel_id=A, name='New')], record_count=1,
                            invalid_count=0, duplicate_count=0, issues=[])
    real_commit = Session.commit

    def failing_commit(self):
        if self.query(AcestreamChannel).filter_by(id=A).count():
            raise RuntimeError('injected failure after import')
        return real_commit(self)
    with monkeypatch.context() as patch:
        patch.setattr(Session, 'commit', failing_commit)
        with pytest.raises(RuntimeError, match='after import'):
            record(source.id, 'account', generation, 5, 'revision', preview, True)
    row = repo.snapshot(source.id, 'account')[0]
    assert (row.cursor, row.imported_count) == (0, 0)
    with runtime.SessionLocal() as db:
        assert db.get(AcestreamChannel, A) is None
    assert record(source.id, 'account', generation, 5, 'revision', preview, True)
    row = repo.snapshot(source.id, 'account')[0]
    assert (row.cursor, row.imported_count) == (5, 1)


# Saved searches and catalogue search: insert-only -------------------------------

def test_search_apply_adds_missing_and_reports_without_touching_existing(db_session):
    from app.models.models import AcestreamChannel
    from app.services.search_import_service import apply_candidates
    _channel(db_session, B, 'Operator', source_url=LIST_URL, group='Mine', is_active=False, is_online=True)
    db_session.commit()
    policy = PolicySnapshot(3, ((1, 'name_contains', 'blocked'),))
    candidates = [
        dict(infohash='1' * 40, name='New', content_id=A, decision='resolved', category='sport'),
        dict(infohash='2' * 40, name='Publisher', content_id=B, decision='resolved', category='movies'),
        dict(infohash='3' * 40, name='Alias', content_id=A, decision='resolved'),
        dict(infohash='4' * 40, name='Blocked', content_id=C, decision='resolved'),
        dict(infohash='5' * 40, name='Was hidden', decision='excluded'),
        dict(infohash='6' * 40, name='Unresolved', decision='unresolved'),
        dict(infohash='7' * 40, name='Later', decision='deferred'),
    ]
    result = apply_candidates(db_session, candidates, policy, 'saved-search:9')
    assert [(i.outcome, i.content_id, i.rule_ids) for i in result.items] == [
        ('added', A, []), ('existing', B, []), ('duplicate', A, []), ('excluded', C, [1]),
        ('deferred', None, []), ('unresolved', None, []), ('deferred', None, [])]
    assert (result.added, result.existing, result.excluded, result.unresolved, result.deferred, result.policy_revision) == (
        1, 1, 1, 1, 2, 3)
    db_session.commit()
    db_session.expire_all()
    added = db_session.get(AcestreamChannel, A)
    assert (added.name, added.source_url, added.group, added.is_online, added.is_active) == (
        'New', 'saved-search:9', 'sport', None, True)
    kept = db_session.get(AcestreamChannel, B)
    assert (kept.name, kept.group, kept.source_url, kept.is_active, kept.is_online, _as_utc(kept.last_seen)) == (
        'Operator', 'Mine', LIST_URL, False, True, OLD)
    assert db_session.get(AcestreamChannel, C) is None


def test_search_apply_dry_run_writes_nothing(db_session):
    from app.models.models import AcestreamChannel
    from app.services.search_import_service import apply_candidates
    candidates = [dict(infohash='1' * 40, name='New', content_id=A, decision='resolved'),
                  dict(infohash='2' * 40, name='New', content_id=A, decision='resolved')]
    result = apply_candidates(db_session, candidates, PolicySnapshot(0, ()), dry_run=True)
    assert [i.outcome for i in result.items] == ['added', 'duplicate']
    db_session.commit()
    assert db_session.query(AcestreamChannel).count() == 0


def test_search_import_without_category_stores_no_group(db_session):
    from app.models.models import AcestreamChannel
    from app.services.search_import_service import apply_candidates
    apply_candidates(db_session, [dict(infohash='1' * 40, name='New', content_id=A, decision='resolved', category='')],
                     PolicySnapshot(0, ()))
    db_session.commit()
    row = db_session.get(AcestreamChannel, A)
    assert (row.group, row.source_url) == (None, 'Acestream Search')


# Manual Add: upsert, explicit override ------------------------------------------

def test_manual_add_creates_with_the_given_fields(client, db_session):
    from app.models.models import AcestreamChannel
    response = client.post('/api/v1/channels/', json=dict(
        id=A, name='Manual', source_url='manual', group='Group', logo='https://example.invalid/a.png',
        tvg_id='a.id', tvg_name='A', is_online=True))
    assert response.status_code == 201, response.text
    assert response.json()['id'] == A
    db_session.expire_all()
    row = db_session.get(AcestreamChannel, A)
    assert (row.name, row.source_url, row.group, row.logo, row.tvg_id, row.tvg_name, row.is_online, row.is_active) == (
        'Manual', 'manual', 'Group', 'https://example.invalid/a.png', 'a.id', 'A', True, True)


def test_manual_add_updates_only_the_fields_sent(client, db_session):
    from app.models.models import AcestreamChannel
    _channel(db_session, A, 'Before', source_url=LIST_URL, group='Mine', logo='https://example.invalid/a.png',
             is_active=False, is_online=True)
    db_session.commit()
    response = client.post('/api/v1/channels/', json=dict(id=A, name='After', group='Changed'))
    assert response.status_code == 201, response.text
    assert (response.json()['name'], response.json()['group']) == ('After', 'Changed')
    db_session.expire_all()
    row = db_session.get(AcestreamChannel, A)
    assert (row.name, row.group, row.logo, row.source_url, row.is_active, row.is_online, _as_utc(row.last_seen)) == (
        'After', 'Changed', 'https://example.invalid/a.png', LIST_URL, False, True, OLD)


def test_manual_override_is_one_request_and_never_reaches_automatic_imports(client, db_session):
    from app.models.models import AcestreamChannel
    from app.schemas.extraction import ExtractedChannel
    from app.services.incremental_ingestion_service import ingest_records
    from app.services.scraper_service import _apply_scrape
    rule = _exclude(db_session, 'name_contains', 'blocked')
    blocked = client.post('/api/v1/channels/', json=dict(id=A, name='Blocked'))
    assert blocked.status_code == 409
    assert blocked.json()['error']['code'] == 'IMPORT_EXCLUDED'
    assert db_session.get(AcestreamChannel, A) is None
    allowed = client.post('/api/v1/channels/', json=dict(id=A, name='Blocked', source_url=LIST_URL, allow_excluded=True))
    assert allowed.status_code == 201, allowed.text
    assert 'allow_excluded' not in allowed.json()
    db_session.expire_all()
    admitted_seen = db_session.get(AcestreamChannel, A).last_seen
    # The next manual request without the flag is refused again, even as an update.
    again = client.post('/api/v1/channels/', json=dict(id=A, name='Blocked again'))
    assert again.status_code == 409 and again.json()['error']['context']['rule_ids'] == [rule.id]
    # Automatic imports still exclude it and never touch the admitted row.
    _apply_scrape(db_session.get_bind(), [(A, 'Blocked by list', {}), (B, 'Other', {})], LIST_URL, LIST_URL, False, 'OK')
    assert ingest_records(db_session, [ExtractedChannel(channel_id=A, name='Blocked by message')], 'telegram-source:1') == 0
    db_session.commit()
    db_session.expire_all()
    row = db_session.get(AcestreamChannel, A)
    assert (row.name, row.source_url) == ('Blocked', LIST_URL)
    assert row.last_seen == admitted_seen
