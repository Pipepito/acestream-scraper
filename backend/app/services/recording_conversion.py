"""One low-priority derivative at a time; originals are never replaced."""
import asyncio
import os
from app.config.database import SessionLocal
from app.models.recordings import Recording, RecordingArtifact
from app.services.recording_capture import spawn_owned
from app.services.recording_storage import RecordingStorage, binaries, inspect_media, reader


def claim_next():
    with SessionLocal() as db:
        row = db.query(RecordingArtifact).join(Recording, Recording.id == RecordingArtifact.recording_id).filter(
            RecordingArtifact.state.in_(['queued', 'converting']), Recording.state.in_(['completed','partial'])).order_by(RecordingArtifact.id).first()
        if row is None:
            return None
        source = db.get(RecordingArtifact, row.source_artifact_id)
        if source is None or source.state != 'ready':
            row.state, row.reason = 'failed', 'original_unavailable'
            db.commit()
            return None
        row.state = 'converting'
        db.commit()
        return {k: getattr(row, k) for k in ('id','root_id','filename','profile','recording_id')} | {'source': source.filename}


def finish(fid, **values):
    with SessionLocal() as db:
        row = db.get(RecordingArtifact, fid)
        if row and row.state != 'deleted':
            for key, value in values.items():
                setattr(row, key, value)
            db.commit()


def conversion_argv(binary, source_fd, output_fd, profile):
    return [binary, '-y', '-nostdin', '-hide_banner', '-loglevel', 'error', '-nostats',
        '-progress', 'pipe:2', '-protocol_whitelist', 'file', '-format_whitelist', 'mpegts',
        '-i', f'/dev/fd/{source_fd}', '-map', '0:v:0?', '-map', '0:a:0?', '-c', 'copy',
        *(['-c:a', 'aac', '-b:a', '160k'] if profile == 'aac' else []),
        '-movflags', '+frag_keyframe+empty_moov+default_base_moof', '-f', 'mp4', 'pipe:1']


async def convert_next(coordinator):
    work = await asyncio.to_thread(claim_next)
    if not work:
        return
    output = process = None
    state, reason, metadata = 'failed', 'conversion_failed', {}
    try:
        with RecordingStorage(work['root_id']) as storage, reader(storage, work['source']) as source:
            expected = os.fstat(source).st_size * 2
            await asyncio.to_thread(storage.admit, coordinator.config.min_free_bytes, expected)
            # An unfinished derivative is disposable, unlike an original.
            if not storage.unlink(work['filename']):
                raise RuntimeError('Derivative is being read')
            output = storage.open(work['filename'], create=True)
            try:
                process = await spawn_owned(conversion_argv(binaries()[0], source, output, work['profile']), output, source)
                while process.process.returncode is None:
                    if coordinator.activity() or coordinator.stopping.is_set():
                        state, reason = 'queued', None
                        break
                    await asyncio.to_thread(storage.admit, coordinator.config.min_free_bytes)
                    if os.fstat(output).st_size > coordinator.config.max_recording_bytes:
                        raise RuntimeError('Derivative too large')
                    await asyncio.sleep(.5)
                await process.close()
                if state != 'queued' and process.process.returncode == 0:
                    info = await asyncio.to_thread(inspect_media, output)
                    if info:
                        state, reason = 'ready', None
                        metadata = dict(bytes=os.fstat(output).st_size, codecs=info['codecs'],
                                        duration=max(0, process.progress['media_us'])/1_000_000)
                        await asyncio.to_thread(os.fsync, output)
            finally:
                if process:
                    await process.close()
                os.close(output)
                output = None
            if state != 'ready':
                storage.unlink(work['filename'])
    except Exception:
        state, reason = 'failed', 'conversion_failed'
    finally:
        await asyncio.to_thread(finish, work['id'], state=state, reason=reason, **metadata)
