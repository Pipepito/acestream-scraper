"""Recovery must preserve source files and fail closed before installation."""
import json
import sqlite3
import threading
import time

import pytest
from fastapi.testclient import TestClient

import main
from app.repositories import startup_recovery as recovery
from app.services.startup_service import startup_service


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    from app.config import settings as config
    from app.config.database import reset_engine
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "current.db"}')
    monkeypatch.setenv('LEGACY_DATABASE_URL', f'sqlite:///{tmp_path / "legacy.db"}')
    config.get_settings.cache_clear()
    monkeypatch.setattr(config, 'settings', config.get_settings())
    reset_engine()
    startup_service.reset()
    yield tmp_path
    reset_engine()
    config.get_settings.cache_clear()
    startup_service.reset()


def seed(path):
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE settings (id INTEGER PRIMARY KEY, key TEXT, value TEXT)')
        conn.executemany('INSERT INTO settings VALUES (?, ?, ?)', [(1, 'one', 'secret-value'), (2, 'one', 'duplicate'), (3, 'two', 'kept')])


def test_salvage_preserves_readable_rows_and_reports_skips(isolated):
    path = isolated / 'current.db'
    seed(path)
    original = path.read_bytes()
    events = []
    recovery.recover_database('salvage', lambda message, *args: events.append(message))
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT key, value FROM settings ORDER BY id').fetchall() == [('one', 'secret-value'), ('two', 'kept')]
        assert conn.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert conn.execute('SELECT version_num FROM alembic_version').fetchone()
    backup = next((isolated / 'backups').glob('recovery-*'))
    assert (backup / 'current' / path.name).read_bytes() == original
    assert any('settings: 2 rows; 1 skipped' in event for event in events)
    assert 'secret-value' not in '\n'.join(events)
    assert recovery.legacy_disabled()


def test_fresh_can_preserve_and_replace_an_unreadable_database(isolated):
    path = isolated / 'current.db'
    path.write_bytes(b'broken database')
    (isolated / 'legacy.db').write_bytes(b'original legacy')
    (isolated / 'legacy.db.migration.json').write_text('{"epg_programs": {"status": "running"}}')
    recovery.recover_database('fresh', lambda *args: None)
    backup = next((isolated / 'backups').glob('recovery-*'))
    assert (backup / 'current' / 'current.db').read_bytes() == b'broken database'
    assert (backup / 'legacy' / 'legacy.db').read_bytes() == b'original legacy'
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM settings').fetchone() == (0,)
    assert recovery.legacy_disabled()


@pytest.mark.parametrize('failure', ['backup', 'schema', 'install'])
def test_recovery_failure_never_discards_original(isolated, monkeypatch, failure):
    path = isolated / 'current.db'
    seed(path)
    original = path.read_bytes()
    def fail(*args, **kwargs):
        raise OSError('forced failure')
    if failure == 'backup':
        monkeypatch.setattr(recovery.shutil, 'copyfile', fail)
    elif failure == 'schema':
        monkeypatch.setattr(recovery.command, 'upgrade', fail)
    else:
        replace = recovery.os.replace
        def install(source, target):
            if str(source).endswith('rebuilt.db'):
                fail()
            return replace(source, target)
        monkeypatch.setattr(recovery.os, 'replace', install)
    with pytest.raises(OSError):
        recovery.recover_database('fresh', lambda *args: None)
    assert path.read_bytes() == original
    if failure == 'install':
        with pytest.raises(RuntimeError, match='interrupted'):
            recovery.legacy_disabled()
    else:
        assert not recovery.recovery_marker().exists()


def test_wal_rows_are_in_the_backup_and_salvaged(isolated):
    path = isolated / 'current.db'
    conn = sqlite3.connect(path)
    try:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA wal_autocheckpoint=0')
        conn.execute('CREATE TABLE settings (id INTEGER PRIMARY KEY, key TEXT, value TEXT)')
        conn.execute("INSERT INTO settings VALUES (1, 'wal', 'preserved')")
        conn.commit()
        recovery.recover_database('salvage', lambda *args: None)
        with sqlite3.connect(path) as rebuilt:
            assert rebuilt.execute('SELECT value FROM settings').fetchone() == ('preserved',)
        backup = next((isolated / 'backups').glob('recovery-*'))
        with sqlite3.connect(backup / 'current' / 'current.db') as saved:
            assert saved.execute('SELECT value FROM settings').fetchone() == ('preserved',)
    finally:
        conn.close()


def wait_finished():
    deadline = time.monotonic() + 5
    while startup_service.status == 'starting':
        assert time.monotonic() < deadline
        time.sleep(0.01)


def test_status_available_during_work_and_failure_with_auth_and_recovery_guards(isolated, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    def slow_failure():
        entered.set()
        assert release.wait(5)
        raise PermissionError('secret/path?token=never-expose')
    monkeypatch.setattr(main, 'initialize_database', slow_failure)
    monkeypatch.setenv('API_TOKEN', 'test-token')
    headers = {'X-Api-Token': 'test-token'}
    with TestClient(main.app) as client:
        try:
            assert entered.wait(5)
            assert client.get('/api/v1/startup').status_code == 401
            assert client.get('/api/v1/startup', headers=headers).json()['status'] == 'starting'
            assert client.get('/api/v1/health').status_code == 503
            assert client.get('/api/v1/settings', headers=headers).status_code == 503
        finally:
            release.set()
        wait_finished()
        status = client.get('/api/v1/startup', headers=headers).json()
        assert status['status'] == 'failed'
        report = client.get('/api/v1/startup/diagnostics', headers=headers)
        assert 'never-expose' not in report.text
        assert 'recovery_token' not in report.text
        assert report.headers['cache-control'] == 'no-store'
        payload = {'action': 'fresh', 'recovery_token': status['recovery_token'], 'confirm': False}
        assert client.post('/api/v1/startup/recover', json=payload, headers=headers).status_code == 409
        payload.update(confirm=True, recovery_token='stale')
        assert client.post('/api/v1/startup/recover', json=payload, headers=headers).status_code == 409
        payload.update(action='retry', recovery_token=status['recovery_token'])
        assert client.post('/api/v1/startup/recover', json=payload).status_code == 401
        assert client.post('/api/v1/startup/recover', json=payload, headers=headers).status_code == 202
        assert client.post('/api/v1/startup/recover', json=payload, headers=headers).status_code == 409


def test_diagnostics_are_bounded():
    for i in range(400):
        startup_service.record(f'Event {i}')
    assert len(startup_service.snapshot().events) == 300
    assert startup_service.snapshot().events[0].message == 'Event 100'


def test_empty_salvage_does_not_install_an_empty_database(isolated):
    path = isolated / 'current.db'
    path.write_bytes(b'no readable tables')
    with pytest.raises(RuntimeError, match='No readable data'):
        recovery.recover_database('salvage', lambda *args: None)
    assert path.read_bytes() == b'no readable tables'
    assert not recovery.recovery_marker().exists()


def test_interrupted_install_salvages_the_preserved_backup(isolated, monkeypatch):
    path = isolated / 'current.db'
    seed(path)
    replace = recovery.os.replace
    def interrupt(source, target):
        if str(source).endswith('rebuilt.db'):
            raise OSError('interrupted')
        return replace(source, target)
    monkeypatch.setattr(recovery.os, 'replace', interrupt)
    with pytest.raises(OSError):
        recovery.recover_database('fresh', lambda *args: None)
    # Simulate loss of the old main/WAL pair during an interrupted cutover.
    path.write_bytes(b'partial replacement')
    monkeypatch.setattr(recovery.os, 'replace', replace)
    recovery.recover_database('salvage', lambda *args: None)
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM settings').fetchone() == (2,)


def test_confirmed_fresh_recovery_restarts_the_real_database_boot(isolated, monkeypatch):
    (isolated / 'current.db').write_bytes(b'corrupt')
    async def noop():
        pass
    monkeypatch.setattr(main.player_service, 'start', noop)
    monkeypatch.setattr(main.player_service, 'stop', noop)
    monkeypatch.setattr(main.task_service, 'start', lambda: None)
    monkeypatch.setattr(main.task_service, 'shutdown', lambda: None)
    monkeypatch.setattr(main.task_service, 'add_interval_task', lambda *a, **k: None)
    with TestClient(main.app) as client:
        wait_finished()
        assert startup_service.status == 'failed'
        status = client.get('/api/v1/startup').json()
        response = client.post('/api/v1/startup/recover', json={
            'action': 'fresh', 'confirm': True, 'recovery_token': status['recovery_token'],
        })
        assert response.status_code == 202
        wait_finished()
        assert startup_service.status == 'ready', startup_service.diagnostics()
        assert client.get('/api/v1/startup').json()['status'] == 'ready'
        assert recovery.legacy_disabled()


def test_sources_are_recovered_first_despite_missing_metadata(isolated):
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from app.models.models import ScrapedURL, EPGSource
    from app.schemas.scraper import URLResponse
    from app.schemas.epg import EPGSourceResponse

    path = isolated / 'current.db'
    with sqlite3.connect(path) as conn:
        conn.executescript('''
            CREATE TABLE scraped_urls (id INTEGER, url TEXT, enabled INTEGER,
                url_type TEXT, scrape_bare_ids INTEGER, last_processed TEXT, error_count TEXT);
            INSERT INTO scraped_urls VALUES (12, 'https://example.com/list', 0, 'ipfs', 1, 'broken date', 'bad counter');
            INSERT INTO scraped_urls VALUES (13, 'https://example.com/other', NULL, NULL, NULL, NULL, NULL);
            CREATE TABLE epg_sources (id INTEGER, url TEXT, name TEXT, enabled INTEGER, last_updated TEXT);
            INSERT INTO epg_sources VALUES (42, 'https://example.com/guide.xml', NULL, 1, 'broken date');
            INSERT INTO epg_sources VALUES (43, NULL, 'Missing URL', 1, NULL);
            CREATE TABLE settings (id INTEGER, key TEXT, value TEXT);
            INSERT INTO settings VALUES (1, 'example', 'retained');
        ''')
    events = []
    recovery.recover_database('salvage', lambda message, *args: events.append(message))
    recovered = [event for event in events if event.startswith('Recovered ')]
    assert recovered[:2] == ['Recovered scraped_urls: 2 rows; 0 skipped.', 'Recovered epg_sources: 1 rows; 1 skipped.']
    engine = create_engine(f'sqlite:///{path}')
    try:
        with Session(engine) as session:
            urls = session.scalars(select(ScrapedURL).order_by(ScrapedURL.id)).all()
            assert [URLResponse.model_validate(row).id for row in urls] == [12, 13]
            assert urls[0].enabled is False
            assert urls[0].scrape_bare_ids is True
            assert urls[0].url_type == 'ipfs'
            assert urls[0].status == 'pending'
            assert urls[0].last_processed is None
            assert urls[0].error_count == 0
            source = session.get(EPGSource, 42)
            assert EPGSourceResponse.model_validate(source).url == 'https://example.com/guide.xml'
            assert source.name == 'Recovered EPG source'
            assert source.last_updated is None
    finally:
        engine.dispose()
