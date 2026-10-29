"""DVR admission, immutable guide snapshots and operator mutations."""
from datetime import timedelta, timezone
import hashlib
import json
from uuid import uuid4
from zoneinfo import ZoneInfo
from app.api.error_handlers import APIError
from app.models.models import _utcnow
from app.models.recordings import Recording, RecordingArtifact
from app.repositories.recording_repository import RecordingRepository, PENDING
from app.schemas.recordings import (RecordingSettings, RecordingSnapshot, RecordingView, RecordingFile,
    RecordingAttemptView, RecordingList, RecordingCapabilities)
from app.services.recording_storage import RecordingStorage, binaries, media_capabilities

CONFIG_KEY = 'recordings'
ROOT_KEY = 'recordings_root_id'


def check(row):
    if row is None:
        raise APIError('RECORDING_NOT_FOUND', 'Recording not found.', 404)
    return row


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def capacity(rows, maximum):
    events = []
    for row in rows:
        events.extend([(row.start_time, 1), (row.end_time + timedelta(seconds=2), -1)])
    active = 0
    for _, change in sorted(events):
        active += change
        if active > maximum:
            raise APIError('RECORDING_CONFLICT', 'Recording capacity is already reserved during these times.', 409)


class RecordingService:
    def __init__(self, db):
        self.db = db
        self.repo = RecordingRepository(db)

    def settings(self):
        return RecordingSettings.model_validate_json(self.repo.setting(CONFIG_KEY, '{}'))

    def capabilities(self):
        config = self.settings()
        ready = False
        try:
            with RecordingStorage(self.repo.setting(ROOT_KEY)):
                ready = True
        except (APIError, OSError):
            pass
        features = media_capabilities()
        ffmpeg = features["stream_copy"]
        return RecordingCapabilities(enabled=config.enabled, available=bool(config.enabled and ready and ffmpeg),
            storage_ready=ready, message='Ready' if ready and ffmpeg else 'Configure a recording directory and FFmpeg/ffprobe.',
            **features, settings=config)

    def configure(self, payload):
        self.repo.claim()
        changed = []
        try:
            if payload.enabled:
                capacity(self.repo.pending(), payload.max_concurrent)
                if not media_capabilities()["stream_copy"]:
                    raise APIError('RECORDING_UNAVAILABLE', 'FFmpeg and ffprobe are required.', 503)
                with RecordingStorage(self.repo.setting(ROOT_KEY), initialize=True) as storage:
                    storage.check_writable()
                    storage.admit(payload.min_free_bytes)
                    self.repo.set_setting(ROOT_KEY, storage.root_id)
            else:
                for pending in self.repo.pending():
                    row = self.operator_row(pending.id)
                    row.reason = 'disabled'
                    changed.append(row)
                    row.stop_requested = True
                    row.revision += 1
                    if row.state == 'scheduled':
                        row.state, row.reason = 'cancelled', 'disabled'
            self.repo.set_setting(CONFIG_KEY, payload.model_dump_json())
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        for row in changed:
            self.notify(row)
        self.notify()
        return payload

    def notify(self, row=None):
        from app.services.recording_coordinator import recording_coordinator
        if row:
            recording_coordinator.update(self.get(row.id))
        else:
            recording_coordinator.request_refresh()

    def operator_row(self, rid):
        row = check(self.repo.get(rid))
        from app.services.recording_coordinator import recording_coordinator
        live = recording_coordinator.current(rid)
        if live and live.revision == row.revision and row.state in PENDING:
            row.state, row.reason = live.state, live.reason
        return row

    def get(self, rid):
        row = check(self.repo.get(rid))
        result = RecordingView.model_validate(row)
        result.files = [RecordingFile.model_validate(f) for f in self.repo.files(rid)]
        result.attempts = [RecordingAttemptView.model_validate(a) for a in self.repo.attempts(rid)]
        return result

    def list(self, offset=0, limit=50, **filters):
        query = self.repo.list(**filters)
        return RecordingList(total=query.count(), items=[self.get(row.id) for row in query.offset(offset).limit(limit)])

    def create(self, data):
        now = _utcnow()
        identity = fingerprint(data.model_dump(mode='json'))
        self.repo.claim()
        try:
            old = self.repo.by_key(data.idempotency_key)
            if old:
                if old.request_hash != identity:
                    raise APIError('RECORDING_IDEMPOTENCY_CONFLICT', 'This request key belongs to another recording request.', 409)
                self.db.rollback()
                return self.get(old.id)
            config = self.settings()
            from app.services.recording_coordinator import recording_coordinator
            if recording_coordinator.thread and not recording_coordinator.ready.is_set():
                raise APIError('RECORDING_RECOVERING', 'Recording recovery is still running. Try again shortly.', 503)
            if not config.enabled:
                raise APIError('RECORDING_DISABLED', 'Enable recordings in Settings first.', 503)
            start = now if data.mode == 'now' else data.start_time.astimezone(timezone.utc)
            end = data.end_time.astimezone(timezone.utc)
            if end <= now or end <= start or start < now - timedelta(seconds=120) or start > now + timedelta(days=90) or end - start > timedelta(hours=12):
                raise APIError('RECORDING_INTERVAL_INVALID', 'Choose a future end, a start within 90 days and a duration of at most 12 hours.', 422)
            channel = self.repo.channel(data.tv_channel_id)
            if channel is None or not channel.is_active:
                raise APIError('RECORDING_CHANNEL_UNAVAILABLE', 'Choose an active TV Channel.', 409)
            snapshot = RecordingSnapshot(title=channel.name, channel_name=channel.name)
            occurrence = None
            if data.programme:
                found = self.repo.programme(data.programme.id)
                if not found:
                    raise APIError('PROGRAMME_CHANGED', 'Programme changed. Refresh the guide.', 409)
                program, guide, source = found
                expected = data.programme.model_dump()
                if any(getattr(program, key) != value for key, value in expected.items()) or channel.epg_source_id != source.id or channel.epg_id != guide.channel_xml_id:
                    raise APIError('PROGRAMME_CHANGED', 'Programme or channel mapping changed. Refresh the guide.', 409)
                occurrence = fingerprint([source.recording_uuid, guide.channel_xml_id, program.start_time.isoformat()])
                snapshot = RecordingSnapshot(title=program.title, channel_name=channel.name,
                    subtitle=program.subtitle, description=program.description, category=program.category,
                    guide_source_uuid=source.recording_uuid, guide_channel_id=guide.channel_xml_id,
                    original_start=program.start_time, original_end=program.end_time, provider_programme_id=program.program_xml_id)
            pending = self.repo.pending()
            if len(pending) >= 1000:
                raise APIError('RECORDING_LIMIT', 'At most 1,000 pending recordings are supported.', 409)
            if any(r.tv_channel_id == channel.id and ((occurrence and r.occurrence_key == occurrence) or
                   (r.start_time < end and r.end_time > start)) for r in pending):
                raise APIError('RECORDING_DUPLICATE', 'This channel already has a recording during these times.', 409)
            row = Recording(id=uuid4().hex, tv_channel_id=channel.id, occurrence_key=occurrence,
                snapshot=snapshot.model_dump(mode='json'), start_time=start, end_time=end, timezone=data.timezone,
                idempotency_key=data.idempotency_key, request_hash=identity)
            capacity([*pending, row], config.max_concurrent)
            with RecordingStorage(self.repo.setting(ROOT_KEY)) as storage:
                storage.admit(config.min_free_bytes, int((end-start).total_seconds() * 3_000_000) if data.mode == 'now' else 0)
            self.db.add(row)
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.notify(row)
        return self.get(row.id)

    def edit(self, rid, data):
        self.repo.claim()
        try:
            row = self.operator_row(rid)
            if row.revision != data.expected_revision:
                raise APIError('RECORDING_CHANGED', 'Recording changed. Refresh before editing.', 409)
            if data.start_time is not None and row.state != 'scheduled':
                raise APIError('RECORDING_STARTED', 'Start time can only change before recording starts.', 409)
            if (data.start_time or data.end_time) and row.state not in PENDING:
                raise APIError('RECORDING_FINISHED', 'This recording has finished.', 409)
            for value in (data.start_time, data.end_time):
                if value and value.utcoffset().total_seconds() and value.astimezone(ZoneInfo(row.timezone)).utcoffset() != value.utcoffset():
                    raise APIError('RECORDING_INTERVAL_INVALID', 'Time offset does not match the recording timezone.', 422)
            row.start_time = data.start_time or row.start_time
            row.end_time = data.end_time or row.end_time
            now = _utcnow()
            if (data.start_time or data.end_time) and (row.end_time <= row.start_time or row.end_time <= now or row.end_time-row.start_time > timedelta(hours=12)):
                raise APIError('RECORDING_INTERVAL_INVALID', 'End must be in the future and within 12 hours of start.', 422)
            if (data.start_time or data.end_time) and row.state == 'scheduled' and (row.start_time < now or row.start_time > now + timedelta(days=90)):
                raise APIError('RECORDING_INTERVAL_INVALID', 'Choose a future start within 90 days.', 422)
            if data.protected is not None:
                row.protected = data.protected
            pending = self.repo.pending()
            if (data.start_time or data.end_time) and any(other.id != row.id and other.tv_channel_id == row.tv_channel_id and other.start_time < row.end_time and other.end_time > row.start_time for other in pending):
                raise APIError('RECORDING_DUPLICATE', 'This channel already has a recording during these times.', 409)
            row.revision += 1
            capacity(pending, self.settings().max_concurrent)
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.notify(row)
        return self.get(rid)

    def stop(self, rid, *, cancel=False):
        self.repo.claim()
        try:
            row = self.operator_row(rid)
            if cancel and row.state not in ('scheduled', 'cancelled'):
                raise APIError('RECORDING_STARTED', 'Use Stop for a recording that has started.', 409)
            if row.state in PENDING:
                row.stop_requested = True
                row.revision += 1
                row.reason = 'user_stop'
                if row.state == 'scheduled':
                    row.state = 'cancelled'
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.notify(row)
        return self.get(rid)

    def delete(self, rid):
        self.repo.claim()
        try:
            row = self.operator_row(rid)
            if row.state in PENDING or row.protected or any(f.state == 'converting' for f in self.repo.files(rid)):
                raise APIError('RECORDING_DELETE_CONFLICT', 'Stop recording, wait for conversion and remove protection before deleting.', 409)
            if row.state != 'deleted':
                row.state = 'deleting'
                row.revision += 1
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.notify()
        return self.get(rid)

    def convert(self, rid, data):
        self.repo.claim()
        try:
            row = check(self.repo.get(rid))
            source = check(self.repo.file(rid, data.file_id))
            features = media_capabilities()
            if not features['mp4_remux'] or (data.profile == 'aac' and not features['aac_conversion']):
                raise APIError('RECORDING_CONVERSION_UNAVAILABLE', 'This FFmpeg build cannot prepare the requested format.', 503)
            if row.state in (*PENDING, 'deleting', 'deleted') or source.state != 'ready' or source.kind != 'original':
                raise APIError('RECORDING_FILE_NOT_READY', 'Choose a closed original recording part.', 409)
            existing = next((f for f in self.repo.files(rid) if f.source_artifact_id == source.id and f.profile == data.profile and f.state != 'failed'), None)
            if existing is None:
                fid = uuid4().hex
                existing = RecordingArtifact(id=fid, recording_id=rid, root_id=source.root_id, filename=fid+'.mp4',
                    kind='derivative', state='queued', profile=data.profile, source_artifact_id=source.id)
                self.db.add(existing)
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        self.notify()
        return RecordingFile.model_validate(existing)
