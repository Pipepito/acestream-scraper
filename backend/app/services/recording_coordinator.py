"""Dedicated DVR event loop and durable journal reconciliation, outside maintenance FIFO."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import asyncio
import contextlib
import fcntl
import json
import logging
import os
import threading
import time
from uuid import uuid4
from app.config.database import SessionLocal
from app.models.models import _utcnow
from app.models.recordings import Recording, RecordingAttempt, RecordingArtifact
from app.repositories.recording_repository import RecordingRepository, PENDING
from app.repositories.settings_repository import SettingsRepository
from app.schemas.recordings import RecordingSettings
from app.services.engine_client import playback_client_from_settings
from app.services.recording_capture import CaptureInput, capture_argv, spawn_owned
from app.services.recording_service import RecordingService, ROOT_KEY
from app.services.recording_storage import RecordingStorage, binaries, inspect_media

log = logging.getLogger(__name__)


def load_configuration():
    with SessionLocal() as db:
        service = RecordingService(db)
        repo = service.repo
        settings, root = service.settings(), repo.setting(ROOT_KEY)
        return settings, root, [service.get(r.id) for r in repo.pending()] if settings.enabled or root else []


def candidates(cid):
    from app.services.tuner_service import TunerService
    from app.services.tuner_playback_service import prefer_recovered_sources
    with SessionLocal() as db:
        repo = RecordingRepository(db)
        channel = repo.channel(cid) if cid else None
        if not channel or not channel.is_active:
            return []
        return prefer_recovered_sources(TunerService(db).relay_stream_ids(cid))


def engine_client():
    with SessionLocal() as db:
        return playback_client_from_settings(SettingsRepository(db))


def persist(data):
    """Idempotent replay. Operator times, revisions and stop intent are never overwritten."""
    with SessionLocal() as db:
        row = db.get(Recording, data['id'])
        if row is None or row.state in ('deleted', 'deleting'):
            return
        if not row.stop_requested or data['state'] not in PENDING:
            row.state = data['state']
            row.reason = data.get('reason')
        for key in ('actual_start', 'actual_end'):
            if data.get(key):
                setattr(row, key, datetime.fromisoformat(data[key]))
        row.gaps = data.get('gaps', [])
        for item in data.get('attempts', []):
            item = dict(item)
            for key in ('started_at', 'ended_at'):
                if item.get(key):
                    item[key] = datetime.fromisoformat(item[key])
            attempt = db.get(RecordingAttempt, item['id'])
            if attempt is None:
                attempt = RecordingAttempt(recording_id=row.id)
                db.add(attempt)
            for key, value in item.items():
                setattr(attempt, key, value)
        db.flush()
        for item in data.get('files', []):
            artifact = db.get(RecordingArtifact, item['id'])
            if artifact is None:
                artifact = RecordingArtifact(recording_id=row.id)
                db.add(artifact)
            for key, value in item.items():
                setattr(artifact, key, value)
        db.commit()


class JournalQueue:
    """Coalesce checkpoints so a locked database cannot build an unbounded backlog."""
    def __init__(self):
        self.pending = {}
        self.event = asyncio.Event()
        self.closed = False

    async def put(self, data):
        if data is None:
            self.closed = True
        else:
            self.pending[data['id']] = data
        self.event.set()

    async def get(self):
        while not self.pending and not self.closed:
            self.event.clear()
            await self.event.wait()
        if self.pending:
            key = next(iter(self.pending))
            return self.pending.pop(key)
        return None


class RecordingCoordinator:
    def __init__(self):
        self._lock = threading.Lock()
        self.views = {}
        self.config = RecordingSettings()
        self.root_id = None
        self.thread = None
        self.loop = None
        self.ready = threading.Event()
        self.stopping = threading.Event()
        self.refresh = threading.Event()
        self.active = {}
        self.sources = {}
        self.reserved_bytes = {}
        self._prepared = {}
        self._prepare_tasks = {}
        self._writes = None
        self._preparation_pool = None
        self._persisted_terminal = set()

    async def start(self):
        if self.thread:
            return
        config, root, views = await asyncio.to_thread(load_configuration)
        self.config, self.root_id = config, root
        self.views = {v.id: v for v in views}
        self.ready.clear()
        self.stopping.clear()
        self.refresh.clear()
        self.thread = threading.Thread(target=self._thread, name='recording-coordinator', daemon=True)
        self.thread.start()

    def _thread(self):
        try:
            asyncio.run(self.run())
        except Exception:
            log.exception('Recording coordinator stopped unexpectedly')

    async def stop(self):
        self.stopping.set()
        if self.thread:
            await asyncio.to_thread(self.thread.join)
        self.thread = None
        self.loop = None
        self.views.clear()
        self.sources.clear()

    def update(self, view):
        with self._lock:
            old = self.views.get(view.id)
            if old is None or view.revision >= old.revision:
                self.views[view.id] = view
        self.refresh.set()

    def request_refresh(self):
        self.refresh.set()

    def activity(self):
        now = _utcnow()
        with self._lock:
            return [v.model_copy(deep=True) for v in self.views.values()
                    if v.state in PENDING and v.start_time <= now + timedelta(seconds=60) and v.end_time > now]

    def source_active(self, cid):
        with self._lock:
            return cid.lower() in self.sources.values()

    def current(self, rid):
        with self._lock:
            return self.views.get(rid)

    def transition(self, rid, state, **values):
        with self._lock:
            view = self.views.get(rid)
            if view:
                self.views[rid] = view.model_copy(update=dict(state=state, **values))

    async def run(self):
        self.loop = asyncio.get_running_loop()
        self.loop.set_default_executor(ThreadPoolExecutor(max_workers=8, thread_name_prefix='dvr'))
        self._writes = JournalQueue()
        self._preparation_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='dvr-prepare')
        writer = asyncio.create_task(self.write_loop())
        refresh_task = None
        upkeep = None
        try:
            await self.recover()
            self.ready.set()
            last_refresh = last_upkeep = time.monotonic()
            while not self.stopping.is_set():
                if (self.refresh.is_set() or time.monotonic()-last_refresh > 30) and (refresh_task is None or refresh_task.done()):
                    self.refresh.clear()
                    last_refresh = time.monotonic()
                    refresh_task = asyncio.create_task(self.reload())
                if time.monotonic()-last_upkeep > 10 and (upkeep is None or upkeep.done()):
                    last_upkeep = time.monotonic()
                    upkeep = asyncio.create_task(self.upkeep())
                with self._lock:
                    views = list(self.views.values())
                for view in views:
                    if view.id in self.active or view.state not in PENDING:
                        continue
                    now = _utcnow()
                    if not self.config.enabled:
                        continue
                    if view.start_time <= now + timedelta(seconds=60) and view.id not in self._prepare_tasks:
                        self._prepare_tasks[view.id] = asyncio.create_task(self.prepare(view))
                    if view.start_time <= now:
                        self.active[view.id] = asyncio.create_task(self.capture(view.id))
                for rid, task in list(self.active.items()):
                    if task.done():
                        try:
                            task.result()
                        except Exception:
                            log.exception('Recording task failed recording_id=%s', rid)
                            self.transition(rid, 'failed', reason='internal_error')
                        self.active.pop(rid)
                        self._prepared.pop(rid, None)
                        self._prepare_tasks.pop(rid, None)
                with self._lock:
                    for rid in list(self._persisted_terminal):
                        view = self.views.get(rid)
                        if rid not in self.active and (view is None or view.state not in PENDING):
                            self.views.pop(rid, None)
                            self._persisted_terminal.discard(rid)
                await asyncio.sleep(.2)
        finally:
            for task in (refresh_task, upkeep, *self._prepare_tasks.values()):
                if task:
                    with contextlib.suppress(Exception):
                        await task
            await asyncio.gather(*self.active.values(), return_exceptions=True)
            self.active.clear()
            await self._writes.put(None)
            await writer
            self._preparation_pool.shutdown(wait=True)

    async def reload(self):
        try:
            config, root, views = await asyncio.to_thread(load_configuration)
            self.config, self.root_id = config, root
            with self._lock:
                durable_pending = {view.id for view in views}
                for rid, cached in list(self.views.items()):
                    if rid not in durable_pending and rid not in self.active and cached.state not in PENDING:
                        self.views.pop(rid, None)
                        self._prepared.pop(rid, None)
                        task = self._prepare_tasks.pop(rid, None)
                        if task and not task.done():
                            task.cancel()
                for view in views:
                    old = self.views.get(view.id)
                    if old is None or view.revision > old.revision:
                        self.views[view.id] = view
                if not config.enabled:
                    for rid, view in self.views.items():
                        if view.state in PENDING:
                            self.views[rid] = view.model_copy(update={'state': 'cancelled', 'reason': 'disabled'})
        except Exception:
            log.warning('Could not refresh recording configuration')

    async def prepare(self, view):
        try:
            ids = await asyncio.get_running_loop().run_in_executor(self._preparation_pool, candidates, view.tv_channel_id)
            self._prepared[view.id] = ids
        except Exception:
            self._prepared[view.id] = []

    async def write_loop(self):
        while (data := await self._writes.get()) is not None:
            try:
                await asyncio.to_thread(persist, data)
                if data['state'] not in PENDING:
                    self._persisted_terminal.add(data['id'])
            except Exception:
                # The durable journal is replayed on next startup, never claim
                # this persistence failure means no media was captured.
                log.warning('Recording state pending journal recovery recording_id=%s', data['id'])
                if not self.stopping.is_set():
                    # Never replace a newer checkpoint already waiting.
                    self._writes.pending.setdefault(data['id'], data)
                    self._writes.event.set()
                    await asyncio.sleep(5)

    async def checkpoint(self, storage, data):
        await asyncio.to_thread(storage.journal, data['id'], data)
        await self._writes.put(json.loads(json.dumps(data)))

    async def recover(self):
        if not self.root_id:
            return
        try:
            with RecordingStorage(self.root_id) as storage:
                for view in list(self.views.values()):
                    journal = await asyncio.to_thread(storage.read_journal, view.id)
                    if not journal:
                        continue
                    # An inherited execution lock proves a surviving wrapper
                    # owns this recording. Do not start a second writer or kill
                    # a PID inferred from stale metadata.
                    lock = await asyncio.to_thread(execution_lock, storage, view.id)
                    if lock is None:
                        self.transition(view.id, 'failed', reason='process_ownership_unavailable')
                        continue
                    os.close(lock)
                    if journal['state'] in PENDING:
                        for attempt in journal.get('attempts', []):
                            if not attempt.get('ended_at'):
                                attempt.update(ended_at=_utcnow().isoformat(), reason='interrupted')
                        for file in journal.get('files', []):
                            if file['state'] != 'writing':
                                continue
                            try:
                                fd = storage.open(file['filename'])
                                try:
                                    info = await asyncio.to_thread(inspect_media, fd)
                                    file.update(bytes=os.fstat(fd).st_size, state='ready' if info else 'invalid',
                                                codecs=info['codecs'] if info else [])
                                finally:
                                    os.close(fd)
                            except OSError:
                                file['state'] = 'missing'
                        journal['gaps'].append({'start': journal.get('checkpoint_at', view.start_time.isoformat()),
                                               'end': _utcnow().isoformat(), 'reason': 'restart'})
                        if view.reason in ('user_stop', 'disabled') or view.end_time <= _utcnow() or not self.config.enabled:
                            journal['state'] = 'partial' if any(f['state']=='ready' for f in journal['files']) else 'failed'
                            journal['reason'] = 'interrupted'
                        else:
                            journal['state'] = 'scheduled'
                    await asyncio.to_thread(storage.journal, view.id, journal)
                    await asyncio.to_thread(persist, journal)
                    self.transition(view.id, journal['state'], reason=journal.get('reason'))
        except Exception:
            log.warning('Recording recovery unavailable; capture remains guarded by storage validation')

    async def capture(self, rid):
        view = self.current(rid)
        data = {'id': rid, 'state': 'starting', 'attempts': [], 'files': [], 'gaps': [], 'reason': None}
        storage = None
        lock = None
        last_media = None
        interrupted = False
        try:
            storage = await asyncio.to_thread(RecordingStorage, self.root_id)
            lock = await asyncio.to_thread(execution_lock, storage, rid)
            if lock is None:
                data.update(state='failed', reason='process_ownership_unavailable')
                return
            old = await asyncio.to_thread(storage.read_journal, rid)
            if old:
                data.update(attempts=old.get('attempts', []), files=old.get('files', []), gaps=old.get('gaps', []),
                            actual_start=old.get('actual_start'))
            if not data.get('actual_start') and (_utcnow()-view.start_time).total_seconds() > 120:
                data.update(state='missed', reason='start_window_expired')
                return
            if len(self.active) > self.config.max_concurrent:
                data.update(state='missed', reason='capacity_unavailable')
                return
            if view.tv_channel_id is None:
                data.update(state='failed', reason='channel_deleted')
                return
            expected = int(max(0, (view.end_time-_utcnow()).total_seconds())*3_000_000)
            self.reserved_bytes[rid] = expected
            await asyncio.to_thread(storage.admit, self.config.min_free_bytes, sum(self.reserved_bytes.values()))
            ids = self._prepared.get(rid)
            if ids is None:
                ids = await asyncio.to_thread(candidates, view.tv_channel_id)
            if not ids:
                data.update(state='failed', reason='no_eligible_source')
                return
            recover_seconds = 0.0
            failures = 0
            episode = time.monotonic()
            index = 0
            while True:
                view = self.current(rid)
                if self.stopping.is_set():
                    interrupted = True
                    data['reason'] = 'interrupted'
                    break
                if view.state not in PENDING or view.reason in ('user_stop', 'disabled') or not self.config.enabled:
                    data['reason'] = view.reason or 'user_stop'
                    break
                if _utcnow() >= view.end_time:
                    data['reason'] = 'end_time'
                    break
                if failures >= 3 or time.monotonic()-episode > 45 or recover_seconds >= 300 or len(data['attempts']) >= 64:
                    data['reason'] = 'recovery_exhausted'
                    break
                cid = ids[index % len(ids)]
                index += 1
                source = process = None
                fd = None
                began = time.monotonic()
                aid, fid = uuid4().hex, uuid4().hex
                attempt = dict(id=aid, ordinal=len(data['attempts'])+1, source_id=cid,
                    route='http' if cid.startswith('url:') else 'direct', started_at=_utcnow().isoformat(),
                    ended_at=None, exit_code=None, reason=None, process_identity=None)
                file = dict(id=fid, attempt_id=aid, root_id=storage.root_id, filename=fid+'.ts', kind='original',
                            state='writing', bytes=0, duration=None, codecs=[], reason=None)
                data['attempts'].append(attempt)
                data['files'].append(file)
                try:
                    with self._lock:
                        self.sources[rid] = cid.lower()
                    data['state'] = 'starting' if not data.get('actual_start') else 'recovering'
                    self.transition(rid, data['state'])
                    await self.checkpoint(storage, data)
                    client = None if cid.startswith('url:') else await asyncio.to_thread(engine_client)
                    source = CaptureInput(client)
                    if client and client.use_acexy:
                        attempt['route'] = 'acexy'
                    deadline = time.monotonic()+min(15, max(0, (view.end_time-_utcnow()).total_seconds()), max(0, 45-(time.monotonic()-episode)))
                    url = await source.open(cid, deadline)
                    fd = await asyncio.to_thread(storage.open, file['filename'], create=True)
                    process = await spawn_owned(capture_argv(binaries()[0], url), fd, ownership_fd=lock)
                    attempt['process_identity'] = {'pid': process.process.pid, 'execution_id': aid}
                    verified = False
                    last_check = time.monotonic()
                    while True:
                        view = self.current(rid)
                        if self.stopping.is_set() or view.state not in PENDING or view.reason in ('user_stop', 'disabled') or not self.config.enabled or _utcnow() >= view.end_time:
                            break
                        if process.process.returncode is not None:
                            raise RuntimeError('source_ended')
                        now = time.monotonic()
                        if not verified and now > deadline:
                            raise RuntimeError('startup_timeout')
                        if now-process.progress['changed'] > 25:
                            raise RuntimeError('media_stalled')
                        if not verified and os.fstat(fd).st_size >= 188*10:
                            info = await asyncio.to_thread(inspect_media, fd)
                            if info:
                                verified = True
                                actual = _utcnow()
                                if data.get('actual_start') is None:
                                    data['actual_start'] = actual.isoformat()
                                gap_start = last_media or view.start_time
                                if (actual-gap_start).total_seconds() > 5:
                                    data['gaps'].append(dict(start=gap_start.isoformat(), end=actual.isoformat(), reason='source_start'))
                                file.update(codecs=info['codecs'])
                                data['state'] = 'recording'
                                self.transition(rid, 'recording', actual_start=datetime.fromisoformat(data['actual_start']))
                                failures = 0
                                await self.checkpoint(storage, data)
                        if now-last_check >= 5:
                            await asyncio.to_thread(storage.admit, self.config.min_free_bytes)
                            used = sum(f['bytes'] for f in data['files'] if f is not file)+os.fstat(fd).st_size
                            self.reserved_bytes[rid] = max(0, expected-used)
                            if used >= self.config.max_recording_bytes:
                                raise RuntimeError('recording_quota')
                            data['checkpoint_at'] = _utcnow().isoformat()
                            await self.checkpoint(storage, data)
                            last_check = now
                        await asyncio.sleep(.2)
                    if verified:
                        last_media = _utcnow()
                except Exception as exc:
                    from app.api.error_handlers import APIError
                    code = exc.code.lower() if isinstance(exc, APIError) else str(exc) if isinstance(exc, RuntimeError) else 'source_unavailable'
                    attempt['reason'] = code if code in {'source_ended','startup_timeout','media_stalled','recording_quota','recording_storage_full'} else 'source_unavailable'
                    if attempt['reason'] in ('recording_quota', 'recording_storage_full'):
                        data['reason'] = attempt['reason']
                        break
                    failures += 1
                finally:
                    if process:
                        await process.close()
                        attempt['exit_code'] = process.process.returncode
                    if source:
                        await source.close()
                    attempt['ended_at'] = _utcnow().isoformat()
                    if fd is not None:
                        try:
                            file['bytes'] = os.fstat(fd).st_size
                            info = await asyncio.to_thread(inspect_media, fd)
                            file.update(state='ready' if info else 'invalid', codecs=info['codecs'] if info else [])
                            if process and process.progress['media_us'] > 0:
                                file['duration'] = process.progress['media_us']/1_000_000
                            await asyncio.to_thread(os.fsync, fd)
                        finally:
                            os.close(fd)
                    else:
                        file['state'] = 'missing'
                    with self._lock:
                        self.sources.pop(rid, None)
                    await self.checkpoint(storage, data)
                if file['state'] == 'ready':
                    last_media = _utcnow()-timedelta(seconds=max(0, time.monotonic()-process.progress['changed'])) if process else datetime.fromisoformat(attempt['ended_at'])
                    episode = time.monotonic()
                recover_seconds += max(0, (time.monotonic()-began) - (file.get('duration') or 0))
            good = any(f['state'] == 'ready' for f in data['files'])
            complete = good and data['reason']=='end_time' and not data['gaps'] and not any(a['reason'] for a in data['attempts'])
            data['state'] = 'completed' if complete else 'partial' if good else 'failed'
            data['actual_end'] = _utcnow().isoformat()
            if interrupted:
                # Resume only captures interrupted by application shutdown.
                data['state'] = 'recovering'
        except Exception:
            data.update(state='partial' if any(f['state']=='ready' for f in data['files']) else 'failed', reason='storage_or_runtime_unavailable')
        finally:
            if storage and lock is not None:
                try:
                    await self.checkpoint(storage, data)
                except Exception:
                    log.warning('Recording journal could not be saved recording_id=%s', rid)
                    await self._writes.put(data)
            else:
                await self._writes.put(data)
            if storage:
                storage.close()
            self.reserved_bytes.pop(rid, None)
            if lock is not None:
                os.close(lock)
            self.transition(rid, data['state'], reason=data.get('reason'))

    async def upkeep(self):
        try:
            await asyncio.to_thread(cleanup, self.root_id, self.config)
            if not self.activity() and not self.stopping.is_set():
                from app.services.recording_conversion import convert_next
                await convert_next(self)
        except Exception:
            log.warning('Recording maintenance deferred')


def execution_lock(storage, rid):
    try:
        fd = storage.open(rid+'.lock', create=True)
    except FileExistsError:
        fd = storage.open(rid+'.lock')
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return None
    return fd


def cleanup(root_id, config):
    if not root_id:
        return
    with SessionLocal() as db, RecordingStorage(root_id) as storage:
        repo = RecordingRepository(db)
        if config.retention_days:
            cutoff = _utcnow()-timedelta(days=config.retention_days)
            for row in db.query(Recording).filter(Recording.state.in_(['completed','partial','failed','missed','cancelled']),
                                                  Recording.protected.is_(False), Recording.end_time < cutoff).limit(100):
                if any(f.state == 'converting' for f in repo.files(row.id)):
                    continue
                row.state = 'deleting'
            db.commit()
        for row in db.query(Recording).filter_by(state='deleting').limit(100):
            done = True
            for file in repo.files(row.id):
                if file.root_id != storage.root_id or not storage.unlink(file.filename):
                    done = False
                else:
                    file.state = 'deleted'
            if done:
                storage.unlink(row.id+'.json')
                row.state = 'deleted'
            db.commit()


recording_coordinator = RecordingCoordinator()
