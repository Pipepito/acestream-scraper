"""Actual owned fake children and coordinator lifecycle; never open live streams."""
import asyncio
from datetime import datetime, timedelta, timezone
import fcntl
import os
import sys
import threading
from uuid import uuid4
import pytest
from app.schemas.recordings import RecordingSettings, RecordingView
from app.services.recording_capture import spawn_owned
from app.services.recording_coordinator import RecordingCoordinator, execution_lock
from app.services.recording_storage import RecordingStorage


@pytest.fixture
def storage(tmp_path, monkeypatch):
    from app.config.settings import get_settings
    monkeypatch.setattr(get_settings(), 'RECORDINGS_DIR', str(tmp_path))
    with RecordingStorage(initialize=True) as root:
        yield root


@pytest.mark.asyncio
async def test_owned_child_reaped_and_lock_released(storage):
    name = uuid4().hex
    output = storage.open(name+'.ts', create=True)
    lock = execution_lock(storage, name)
    process = await spawn_owned([sys.executable, '-u', '-c',
        'import os,time; os.write(1,b"media"); os.write(2,b"out_time_us=1000000\\n"); time.sleep(60)'], output, ownership_fd=lock)
    try:
        for _ in range(100):
            if os.fstat(output).st_size:
                break
            await asyncio.sleep(.02)
        assert os.pread(output, 5, 0) == b'media'
        os.close(lock)
        lock = None
        assert execution_lock(storage, name) is None
        await process.close()
        assert process.process.returncode is not None
        again = execution_lock(storage, name)
        assert again is not None
        os.close(again)
    finally:
        await process.close()
        os.close(output)
        if lock is not None:
            os.close(lock)


def view(**kwargs):
    now = datetime.now(timezone.utc)
    return RecordingView(id=uuid4().hex, tv_channel_id=1, snapshot={'title':'Test','channel_name':'Test'},
        start_time=now-timedelta(seconds=1), end_time=now+timedelta(seconds=1), timezone='UTC', state='scheduled',
        revision=1, protected=False, actual_start=None, actual_end=None, reason=None, gaps=[], created_at=now, **kwargs)


@pytest.mark.asyncio
async def test_capture_finalizes_media_without_maintenance_queue(storage, monkeypatch):
    import app.services.recording_coordinator as module
    manager = RecordingCoordinator()
    row = view()
    manager.views[row.id] = row
    manager.root_id = storage.root_id
    manager.config = RecordingSettings(enabled=True, min_free_bytes=67108864)
    manager._prepared[row.id] = ['url:test']
    manager._writes = asyncio.Queue()
    class Input:
        def __init__(self, *_): pass
        async def open(self, *_): return 'unused'
        async def close(self): pass
    monkeypatch.setattr(module, 'CaptureInput', Input)
    monkeypatch.setattr(module, 'binaries', lambda: ('fake','fake'))
    monkeypatch.setattr(module, 'inspect_media', lambda fd: {'codecs':['h264'], 'duration':1} if os.fstat(fd).st_size else None)
    monkeypatch.setattr(module, 'capture_argv', lambda *_: [sys.executable, '-u', '-c',
        'import os,time\nfor i in range(1000):\n os.write(1,b"x"*1880); os.write(2,f"out_time_us={i*100000}\\n".encode()); time.sleep(.1)'])
    await asyncio.wait_for(manager.capture(row.id), 8)
    journal = storage.read_journal(row.id)
    assert journal['state'] == 'completed', journal
    assert journal['files'][0]['state'] == 'ready'
    assert journal['attempts'][0]['ended_at']
    assert not manager.sources
    lock = execution_lock(storage, row.id)
    assert lock is not None
    os.close(lock)


@pytest.mark.asyncio
async def test_start_expired_does_not_spawn(storage, monkeypatch):
    manager = RecordingCoordinator()
    row = view().model_copy(update={'start_time': datetime.now(timezone.utc)-timedelta(minutes=3)})
    manager.views[row.id] = row
    manager.root_id = storage.root_id
    manager._writes = asyncio.Queue()
    await manager.capture(row.id)
    assert storage.read_journal(row.id)['state'] == 'missed'


def test_storage_rejects_hard_links(storage, tmp_path):
    file = uuid4().hex+'.ts'
    fd = storage.open(file, create=True)
    os.close(fd)
    os.link(tmp_path/file, tmp_path/'other')
    from app.api.error_handlers import APIError
    with pytest.raises(APIError):
        storage.open(file)


@pytest.mark.asyncio
async def test_recovery_saves_reconciled_gap_before_resuming(storage, monkeypatch):
    import app.services.recording_coordinator as module
    manager = RecordingCoordinator()
    row = view().model_copy(update={'end_time': datetime.now(timezone.utc)+timedelta(minutes=5)})
    manager.views[row.id] = row
    manager.root_id = storage.root_id
    manager.config = RecordingSettings(enabled=True)
    storage.journal(row.id, {'id':row.id, 'state':'recording', 'files':[], 'attempts':[], 'gaps':[],
        'actual_start':row.start_time.isoformat(), 'checkpoint_at':row.start_time.isoformat()})
    saved = []
    monkeypatch.setattr(module, 'persist', lambda data: saved.append(data))
    await manager.recover()
    journal = storage.read_journal(row.id)
    assert journal['state'] == 'scheduled'
    assert journal['gaps'][0]['reason'] == 'restart'
    assert saved[0]['gaps'] == journal['gaps']


@pytest.mark.asyncio
async def test_stopped_recording_never_resumes_after_restart(storage, monkeypatch):
    import app.services.recording_coordinator as module
    manager = RecordingCoordinator()
    row = view().model_copy(update={'reason':'user_stop'})
    manager.views[row.id] = row
    manager.root_id = storage.root_id
    manager.config = RecordingSettings(enabled=True)
    storage.journal(row.id, {'id':row.id, 'state':'recording', 'files':[], 'attempts':[], 'gaps':[]})
    monkeypatch.setattr(module, 'persist', lambda _: None)
    await manager.recover()
    assert storage.read_journal(row.id)['state'] == 'failed'
    assert manager.current(row.id).state == 'failed'


@pytest.mark.asyncio
async def test_pinned_ffmpeg_converts_fixture_using_owned_descriptors(storage):
    from pathlib import Path
    from app.services.recording_conversion import conversion_argv
    from app.services.recording_storage import binaries, inspect_media, media_capabilities
    binary, _ = binaries()
    if not binary:
        pytest.skip('FFmpeg unavailable')
    assert media_capabilities()['aac_conversion']
    fixture = Path(__file__).parent/'docker/fixtures/sample-h264-ac3.m2ts'
    source = os.open(fixture, os.O_RDONLY)
    output = storage.open(uuid4().hex+'.mp4', create=True)
    process = None
    try:
        process = await spawn_owned(conversion_argv(binary, source, output, 'aac'), output, source)
        await asyncio.wait_for(process.process.wait(), 30)
        await process.close()
        assert process.process.returncode == 0
        info = inspect_media(output)
        assert info and 'h264' in info['codecs'] and 'aac' in info['codecs']
    finally:
        if process:
            await process.close()
        os.close(source)
        os.close(output)


@pytest.mark.asyncio
async def test_another_execution_cannot_overwrite_the_owners_journal(storage):
    manager = RecordingCoordinator()
    row = view()
    manager.views[row.id] = row
    manager.root_id = storage.root_id
    manager._writes = asyncio.Queue()
    original = {'id':row.id, 'state':'recording', 'owner':'original'}
    storage.journal(row.id, original)
    lock = execution_lock(storage, row.id)
    try:
        await manager.capture(row.id)
        assert storage.read_journal(row.id) == original
        assert manager.current(row.id).reason == 'process_ownership_unavailable'
    finally:
        os.close(lock)


@pytest.mark.asyncio
async def test_checkpoints_coalesce_while_database_writer_is_busy():
    from app.services.recording_coordinator import JournalQueue
    queue = JournalQueue()
    for i in range(100):
        await queue.put({'id':'one', 'value':i})
    await queue.put({'id':'two', 'value':0})
    await queue.put(None)
    assert await queue.get() == {'id':'one', 'value':99}
    assert await queue.get() == {'id':'two', 'value':0}
    assert await queue.get() is None


@pytest.mark.asyncio
async def test_due_dispatch_does_not_wait_for_database_writer(monkeypatch):
    import time
    import app.services.recording_coordinator as module
    manager = RecordingCoordinator()
    due = datetime.now(timezone.utc) + timedelta(seconds=.3)
    row = view().model_copy(update={'start_time':due, 'end_time':due+timedelta(minutes=5)})
    manager.views[row.id] = row
    manager.config = RecordingSettings(enabled=True)
    entered, release = threading.Event(), threading.Event()
    def persist(_):
        entered.set()
        assert release.wait(5)
    async def recovery():
        await manager._writes.put({'id':'busy', 'state':'failed'})
    async def prepare(_):
        pass
    delays = []
    async def capture(_):
        delays.append((datetime.now(timezone.utc)-due).total_seconds())
        manager.stopping.set()
        release.set()
    monkeypatch.setattr(module, 'persist', persist)
    monkeypatch.setattr(manager, 'recover', recovery)
    monkeypatch.setattr(manager, 'prepare', prepare)
    monkeypatch.setattr(manager, 'capture', capture)
    try:
        await asyncio.wait_for(manager.run(), 5)
    finally:
        release.set()
    assert entered.is_set()
    assert 0 <= delays[0] < 1
