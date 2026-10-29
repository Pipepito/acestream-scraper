"""DVR admission/security contracts; no live streams or real FFmpeg needed."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import os
import pytest
from app.models.models import TVChannel, EPGSource, EPGChannel, EPGProgram
from app.models.recordings import Recording, RecordingArtifact
from app.services.recording_storage import RecordingStorage


@pytest.fixture
def dvr(client, db_session, monkeypatch, tmp_path):
    from app.config.settings import get_settings
    from app.services import recording_service
    monkeypatch.setattr(get_settings(), 'RECORDINGS_DIR', str(tmp_path))
    monkeypatch.setattr(recording_service, 'binaries', lambda: ('fake', 'fake'))
    monkeypatch.setattr(recording_service, 'media_capabilities', lambda: dict(stream_copy=True, mp4_remux=True, aac_conversion=True))
    monkeypatch.setattr(recording_service.RecordingService, 'notify', lambda *_: None)
    source = EPGSource(name='Guide', url='https://example.com/guide.xml')
    db_session.add(source)
    db_session.flush()
    guide = EPGChannel(epg_source_id=source.id, channel_xml_id='one', name='One')
    tv = TVChannel(name='One', epg_source_id=source.id, epg_id='one')
    db_session.add_all([guide, tv])
    db_session.flush()
    now = datetime.now(timezone.utc)
    programme = EPGProgram(epg_channel_id=guide.id, title='Programme', start_time=now+timedelta(hours=1), end_time=now+timedelta(hours=2))
    db_session.add(programme)
    db_session.commit()
    response = client.put('/api/v1/config/recordings', json={'enabled': True, 'min_free_bytes': 67108864})
    assert response.status_code == 200, response.text
    return client, db_session, tv, programme


def request(tv, programme, **kw):
    data = dict(tv_channel_id=tv.id, mode='schedule', start_time=programme.start_time.isoformat(), end_time=programme.end_time.isoformat(),
                timezone='Europe/Madrid', idempotency_key=uuid4().hex,
                programme={k: getattr(programme, k).isoformat() if k in ('start_time','end_time') else getattr(programme,k)
                           for k in ('id','epg_channel_id','start_time','end_time','title','subtitle','description','category')})
    return data | kw


def test_save_replay_conflict_and_snapshot_survive_guide_replacement(dvr):
    client, db, tv, programme = dvr
    payload = request(tv, programme)
    response = client.post('/api/v1/recordings', json=payload)
    assert response.status_code == 201, response.text
    row = response.json()
    assert client.post('/api/v1/recordings', json=payload).json()['id'] == row['id']
    assert client.post('/api/v1/recordings', json=payload | {'timezone':'UTC'}).status_code == 409
    assert client.post('/api/v1/recordings', json=request(tv, programme)).status_code == 409
    db.delete(programme)
    db.commit()
    detail = client.get('/api/v1/recordings/'+row['id']).json()
    assert detail['snapshot']['title'] == 'Programme'
    assert detail['state'] == 'scheduled'
    assert 'filename' not in str(detail)


def test_stale_programme_and_edit_cancel(dvr):
    client, db, tv, programme = dvr
    payload = request(tv, programme)
    assert client.post('/api/v1/recordings', json=payload | {'programme': payload['programme'] | {'title':'Changed'}}).status_code == 409
    row = client.post('/api/v1/recordings', json=payload).json()
    url = '/api/v1/recordings/'+row['id']
    assert client.patch(url, json={'expected_revision': 9, 'protected': True}).status_code == 409
    assert client.patch(url, json={'expected_revision': 1, 'protected': True}).json()['protected']
    assert client.post(url+'/cancel').json()['state'] == 'cancelled'
    assert client.post(url+'/cancel').json()['state'] == 'cancelled'
    assert client.delete(url).status_code == 409


def test_capacity_across_channels_and_disable(dvr):
    client, db, tv, programme = dvr
    assert client.post('/api/v1/recordings', json=request(tv, programme)).status_code == 201
    other = TVChannel(name='Two', epg_source_id=tv.epg_source_id, epg_id=tv.epg_id)
    db.add(other)
    db.commit()
    assert client.post('/api/v1/recordings', json=request(other, programme)).status_code == 409
    assert client.put('/api/v1/config/recordings', json={'enabled':False}).status_code == 200
    assert client.get('/api/v1/recordings').json()['items'][0]['state'] == 'cancelled'


def test_missing_mount_never_reinitialized(dvr, monkeypatch, tmp_path):
    client, _, _, _ = dvr
    from app.config.settings import get_settings
    other = tmp_path/'empty'
    other.mkdir()
    monkeypatch.setattr(get_settings(), 'RECORDINGS_DIR', str(other))
    assert client.put('/api/v1/config/recordings', json={'enabled':True}).status_code == 503
    assert not (other/'.dvr-root').exists()


def test_files_ranges_head_auth_and_symlink(dvr, monkeypatch, tmp_path):
    client, db, tv, programme = dvr
    row = client.post('/api/v1/recordings', json=request(tv, programme)).json()
    recording = db.get(Recording, row['id'])
    recording.state = 'completed'
    with RecordingStorage() as storage:
        fid = uuid4().hex
        fd = storage.open(fid+'.ts', create=True)
        os.write(fd, b'0123456789')
        os.close(fd)
        db.add(RecordingArtifact(id=fid, recording_id=row['id'], root_id=storage.root_id, filename=fid+'.ts', state='ready'))
    db.commit()
    url = f"/api/v1/recordings/{row['id']}/files/{fid}"
    response = client.get(url, headers={'Range':'bytes=2-5'})
    assert response.status_code == 206 and response.content == b'2345'
    assert response.headers['content-range'] == 'bytes 2-5/10'
    assert client.head(url).content == b''
    assert client.get(url, headers={'Range':'bytes=99-'}).status_code == 416
    monkeypatch.setenv('API_TOKEN', 'private')
    assert client.get(url).status_code == 401
    assert client.head(url).status_code == 401
    assert client.get(url+'?token=private').content == b'0123456789'
    (tmp_path/(fid+'.ts')).unlink()
    (tmp_path/(fid+'.ts')).symlink_to('/etc/passwd')
    assert client.get(url+'?token=private').status_code == 404


@pytest.mark.parametrize('start,end', [('2026-03-29T02:30:00+01:00','2026-03-29T04:00:00+02:00'), ('2026-10-28T10:00:00','2026-10-28T11:00:00')])
def test_invalid_timezone_intervals(dvr, start, end):
    client, _, tv, programme = dvr
    assert client.post('/api/v1/recordings', json=request(tv, programme, start_time=start, end_time=end)).status_code == 422


def test_upgrade_from_prior_head_preserves_guides(tmp_path):
    import sqlite3
    from alembic.config import Config
    from alembic import command
    path = tmp_path/'migration.db'
    config = Config('backend/migrations/alembic.ini')
    config.set_main_option('script_location', 'backend/migrations')
    config.attributes['database_url'] = 'sqlite:///'+str(path)
    config.attributes['configure_logger'] = False
    command.upgrade(config, '20261027_1300')
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO epg_sources (id,name,url) VALUES (1,'Guide','https://example.com')")
        db.execute("INSERT INTO epg_channels (id,epg_source_id,channel_xml_id,name) VALUES (1,1,'one','One')")
    command.upgrade(config, 'head')
    with sqlite3.connect(path) as db:
        first = db.execute('SELECT recording_uuid FROM epg_sources').fetchone()[0]
        assert len(first) == 32
        assert db.execute('SELECT name FROM epg_channels').fetchone() == ('One',)
        assert db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recordings'").fetchone()
    command.upgrade(config, 'head')
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT recording_uuid FROM epg_sources').fetchone()[0] == first


def test_stop_and_disable_preserve_intent_when_journal_write_is_pending(dvr, monkeypatch):
    client, db, tv, programme = dvr
    from app.services.recording_coordinator import recording_coordinator
    from app.schemas.recordings import RecordingView
    row = client.post('/api/v1/recordings', json=request(tv, programme)).json()
    live = RecordingView.model_validate(row).model_copy(update={'state':'recording'})
    monkeypatch.setattr(recording_coordinator, 'current', lambda rid: live if rid == row['id'] else None)
    url = '/api/v1/recordings/'+row['id']
    assert client.post(url+'/cancel').status_code == 409
    assert client.patch(url, json={'expected_revision':1, 'start_time':programme.start_time.isoformat()}).status_code == 409
    assert client.put('/api/v1/config/recordings', json={'enabled':False}).status_code == 200
    db.expire_all()
    stored = db.get(Recording, row['id'])
    assert stored.state == 'recording' and stored.stop_requested and stored.reason == 'disabled'


def test_deletion_waits_for_readers_and_keeps_history(dvr, monkeypatch):
    client, db, tv, programme = dvr
    from app.services import recording_coordinator as module
    from app.services.recording_storage import reader
    from app.schemas.recordings import RecordingSettings
    from contextlib import contextmanager
    row = client.post('/api/v1/recordings', json=request(tv, programme)).json()
    saved = db.get(Recording, row['id'])
    saved.state = 'completed'
    with RecordingStorage() as root:
        fid = uuid4().hex
        fd = root.open(fid+'.ts', create=True)
        os.write(fd, b'media')
        os.close(fd)
        db.add(RecordingArtifact(id=fid, recording_id=row['id'], root_id=root.root_id, filename=fid+'.ts', state='ready'))
        db.commit()
        @contextmanager
        def session():
            yield db
        monkeypatch.setattr(module, 'SessionLocal', session)
        with reader(root, fid+'.ts'):
            assert client.delete('/api/v1/recordings/'+row['id']).status_code == 202
            db.expire_all()
            module.cleanup(root.root_id, RecordingSettings())
            assert db.get(Recording, row['id']).state == 'deleting'
        module.cleanup(root.root_id, RecordingSettings())
        assert db.get(Recording, row['id']).state == 'deleted'
        assert client.get('/api/v1/recordings/'+row['id']).json()['snapshot']['title'] == 'Programme'


def test_playback_subscriptions_are_independent(dvr):
    client, db, tv, programme = dvr
    row = client.post('/api/v1/recordings', json=request(tv, programme)).json()
    db.get(Recording, row['id']).state = 'completed'
    with RecordingStorage() as root:
        fid = uuid4().hex
        db.add(RecordingArtifact(id=fid, recording_id=row['id'], root_id=root.root_id, filename=fid+'.ts', state='ready'))
    db.commit()
    url = '/api/v1/recordings/'+row['id']+'/playback-sessions'
    first = client.post(url, json={'file_id':fid}).json()
    second = client.post(url, json={'file_id':fid}).json()
    assert first['state'] == second['state'] == 'preparing'
    assert first['file_id'] == second['file_id']
    assert client.delete(url+'/'+first['id']).status_code == 204
    assert client.get(url+'/'+first['id']).status_code == 404
    assert client.get(url+'/'+second['id']).json()['state'] == 'preparing'
    client.delete(url+'/'+second['id'])
