"""Descriptor-relative DVR storage. Never trust a browser path or follow links."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import threading
from uuid import uuid4
from app.api.error_handlers import APIError
from app.config.settings import get_settings
from app.services.stream_bitrate_service import has_media_packets

_NAME = re.compile(r'^[0-9a-f]{32}\.(?:ts|mp4|json|lock)$')
_READERS: dict[str, int] = {}
_LOCK = threading.Lock()


def unavailable():
    return APIError('RECORDING_STORAGE_UNAVAILABLE', 'Recording storage is unavailable. Check the configured directory and mount.', 503)


def directory_fd(path):
    if not path or not os.path.isabs(path):
        raise unavailable()
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in Path(path).parts[1:]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except BaseException:
        os.close(fd)
        raise


class RecordingStorage:
    def __init__(self, root_id=None, *, initialize=False):
        self.fd = None
        try:
            self.fd = directory_fd(get_settings().RECORDINGS_DIR)
            flags = os.O_RDONLY | os.O_NOFOLLOW
            try:
                marker = os.open('.dvr-root', flags, dir_fd=self.fd)
            except FileNotFoundError:
                if not initialize or root_id:
                    raise
                value = uuid4().hex
                marker = os.open('.dvr-root', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
                try:
                    os.write(marker, value.encode())
                    os.fsync(marker)
                finally:
                    os.close(marker)
                marker = os.open('.dvr-root', flags, dir_fd=self.fd)
            try:
                info = os.fstat(marker)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid():
                    raise ValueError('Invalid marker')
                self.root_id = os.read(marker, 33).decode()
                if not re.fullmatch('[0-9a-f]{32}', self.root_id) or (root_id and root_id != self.root_id):
                    raise ValueError('Wrong mount')
            finally:
                os.close(marker)
        except (OSError, ValueError, UnicodeError):
            self.close()
            raise unavailable() from None

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def check_writable(self):
        name = uuid4().hex + '.json'
        try:
            fd = self.open(name, create=True)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
            self.unlink(name)
        except OSError:
            raise unavailable() from None

    def free(self):
        info = os.fstatvfs(self.fd)
        return info.f_bavail * info.f_frsize

    def admit(self, reserve, expected=0):
        if self.free() < reserve + expected:
            raise APIError('RECORDING_STORAGE_FULL', 'Not enough free recording space.', 503)

    def open(self, name, *, create=False):
        if not _NAME.fullmatch(name):
            raise unavailable()
        flags = os.O_NOFOLLOW | (os.O_RDWR | os.O_CREAT | os.O_EXCL if create else os.O_RDONLY)
        fd = os.open(name, flags, 0o600, dir_fd=self.fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid():
            os.close(fd)
            raise unavailable()
        return fd

    def unlink(self, name):
        with _LOCK:
            if _READERS.get(name):
                return False
            try:
                fd = self.open(name)
                os.close(fd)
                os.unlink(name, dir_fd=self.fd)
            except FileNotFoundError:
                pass
            return True

    def journal(self, rid, data):
        name = rid + '.json'
        if not _NAME.fullmatch(name):
            raise unavailable()
        # Only the owned coordinator writes these generated names. Atomic
        # replace publishes complete records; no input URLs or credentials.
        temporary = uuid4().hex + '.json'
        fd = self.open(temporary, create=True)
        try:
            payload = memoryview(json.dumps(data).encode())
            while payload:
                payload = payload[os.write(fd, payload):]
            os.fsync(fd)
        finally:
            os.close(fd)
        os.rename(temporary, name, src_dir_fd=self.fd, dst_dir_fd=self.fd)
        os.fsync(self.fd)

    def read_journal(self, rid):
        try:
            fd = self.open(rid + '.json')
        except FileNotFoundError:
            return None
        try:
            return json.loads(os.read(fd, 1024 * 1024))
        finally:
            os.close(fd)


@contextmanager
def reader(storage, name):
    with _LOCK:
        if sum(_READERS.values()) >= 16:
            raise APIError('RECORDING_READ_LIMIT', 'Too many recording file readers. Try again shortly.', 429)
        fd = storage.open(name)
        _READERS[name] = _READERS.get(name, 0) + 1
    try:
        yield fd
    finally:
        os.close(fd)
        with _LOCK:
            _READERS[name] -= 1
            if not _READERS[name]:
                _READERS.pop(name)


def binaries():
    configured = get_settings().FFMPEG_BINARY_PATH
    ffmpeg = configured or shutil.which('ffmpeg')
    ffprobe = str(Path(ffmpeg).with_name('ffprobe')) if ffmpeg else None
    return (ffmpeg, ffprobe) if ffmpeg and ffprobe and os.access(ffmpeg, os.X_OK) and os.access(ffprobe, os.X_OK) else (None, None)


def inspect_media(fd):
    """Bounded byte sample only: no file/URL interpretation in ffprobe."""
    _, probe = binaries()
    if not probe:
        return None
    sample = os.pread(fd, 2 * 1024**2, 0)
    if not sample:
        return None
    try:
        result = subprocess.run([probe, '-v', 'error', '-protocol_whitelist', 'pipe',
            '-format_whitelist', 'mpegts,mov', '-i', 'pipe:0', '-show_entries',
            'stream=index,codec_name,codec_type:packet=stream_index,size,pts_time:format=duration',
            '-of', 'json'], input=sample, capture_output=True, timeout=10)
        data = json.loads(result.stdout)
        if not has_media_packets(data):
            return None
        timestamps = [float(p['pts_time']) for p in data.get('packets', []) if 'pts_time' in p]
        if len(timestamps) < 2 or max(timestamps) <= min(timestamps):
            return None
        return {'codecs': [s['codec_name'] for s in data['streams'] if s.get('codec_name')],
                'duration': max(timestamps) - min(timestamps)}
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        return None


_CAPABILITIES = {}

def media_capabilities():
    """Inspect the selected binary without launching media work; cache by file identity."""
    binary, probe = binaries()
    empty = dict(stream_copy=False, mp4_remux=False, aac_conversion=False)
    if not binary or not probe:
        return empty
    try:
        info = os.stat(binary)
        key = (binary, info.st_mtime_ns, info.st_size)
        if key in _CAPABILITIES:
            return _CAPABILITIES[key]
        outputs = {}
        for option in ('muxers', 'encoders', 'protocols'):
            result = subprocess.run([binary, '-hide_banner', '-'+option], capture_output=True, text=True, timeout=3)
            if result.returncode:
                return empty
            outputs[option] = result.stdout[:262144]
        muxers = {name for line in outputs['muxers'].splitlines() if len(line.split()) >= 2 and 'E' in line.split()[0] for name in line.split()[1].split(',')}
        encoders = {line.split()[1] for line in outputs['encoders'].splitlines() if len(line.split()) >= 2}
        protocols = set(outputs['protocols'].split())
        result = dict(stream_copy='mpegts' in muxers and {'pipe','http','tcp','file','crypto'} <= protocols,
                      mp4_remux='mp4' in muxers, aac_conversion='aac' in encoders and 'mp4' in muxers)
        _CAPABILITIES.clear()
        _CAPABILITIES[key] = result
        return result
    except (OSError, subprocess.TimeoutExpired):
        return empty
