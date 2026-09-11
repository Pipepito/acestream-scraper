"""Bounded, read-only diagnostic exports. Never traverse user-selected paths."""
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
import platform
from threading import Lock
from zipfile import ZipFile, ZIP_DEFLATED

LIMIT = 256 * 1024
SERVICES = ('acestream', 'acestream-check', 'acexy', 'ipfs', 'zeronet', 'warp', 'tor')
CAPTURE_NAMES = ('scraper', 'entrypoint', *SERVICES)
LOG_NAMES = tuple(
    f'{name}.log{suffix}'
    for name in CAPTURE_NAMES for suffix in ('', '.1', '.2')
) + ('console.log', 'console.log.1', 'console.log.2', 'warp-svc.log', 'debug.log', 'error.log')
_lock = Lock()


class DiagnosticsBusy(RuntimeError):
    pass


def redact(text: str) -> str:
    # Also mask configured secrets when a third-party logger emits an unlabelled value.
    for key, value in os.environ.items():
        if re.search(r'token|password|secret|license|api_key', key, re.I) and len(value) >= 4:
            text = text.replace(value, '[redacted]')
    text = re.sub(r'(?im)(authorization|cookie|set-cookie|x-api-token)\s*[:=].*$', r'\1: [redacted]', text)
    text = re.sub(r'''(?i)(\b(?:[\w-]{0,64}(?:token|password|secret|license|api[_-]?key)[\w-]{0,32})["']?\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;&]+)''', r'\1[redacted]', text)
    text = re.sub(r'(?i)\b(?:https?|socks5)://[^\s<>"\']+', '[redacted-url]', text)
    text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[redacted-ip]', text)
    return text


def read_tail(directory: Path, name: str, limit: int = LIMIT) -> tuple[str | None, bool]:
    """Reject symlinks/devices and bound reads even while files grow/rotate."""
    try:
        root = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root)
        finally:
            os.close(root)
        with os.fdopen(fd, 'rb') as stream:
            metadata = os.fstat(stream.fileno())
            if not stat.S_ISREG(metadata.st_mode):
                return None, False
            truncated = metadata.st_size > limit
            stream.seek(max(0, metadata.st_size - limit))
            raw = stream.read(limit)
            if truncated:
                # A partial credential/URL at the cut boundary cannot be redacted reliably.
                raw = raw.partition(b'\n')[2]
            return redact(raw.decode('utf-8', 'replace')), truncated
    except OSError:
        return None, False


def build_bundle() -> bytes:
    if not _lock.acquire(blocking=False):
        raise DiagnosticsBusy()
    try:
        logs = Path(os.environ.get('LOG_DIR', '/app/logs'))
        run = Path(os.environ.get('SUPERVISOR_RUN_DIR', '/run/acestream-scraper'))
        manifest = {'created_at': datetime.now(timezone.utc).isoformat(),
                    'format_version': 1, 'logs': {}, 'supervisor': {},
                    'architecture': platform.machine(), 'memory': {},
                    'note': 'Recent bounded log tails. Common credentials and URLs are masked; review before sharing. External service and host Docker/kernel logs are not available.'}
        output = BytesIO()
        with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
            for name in LOG_NAMES:
                content, truncated = read_tail(logs, name)
                manifest['logs'][name] = {'available': content is not None, 'truncated': truncated}
                if content is not None:
                    archive.writestr('logs/' + name, content)
            for service in SERVICES:
                state = {}
                for field in ('pid', 'started'):
                    value, _ = read_tail(run, f'{service}.{field}', 64)
                    state[field] = int(value.strip()) if value and value.strip().isdigit() else None
                stopped, _ = read_tail(run, f'{service}.stopped', 64)
                state['stopped_by_user'] = stopped is not None
                manifest['supervisor'][service] = state
            # Linux cgroup v2 can identify container OOM kills without a Docker
            # socket or privileged host/kernel access. Other platforms omit it.
            for name in ('memory.events', 'memory.current', 'memory.max'):
                value, _ = read_tail(Path('/sys/fs/cgroup'), name, 4096)
                manifest['memory'][name] = value
            archive.writestr('manifest.json', json.dumps(manifest, indent=2))
        return output.getvalue()
    finally:
        _lock.release()
