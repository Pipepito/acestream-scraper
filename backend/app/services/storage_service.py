"""Bounded, cached storage inventory without Docker socket access or user paths."""
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from app.schemas.storage import ConfigurationWarning, StorageDirectory, StorageReport

_CACHE = None
_CACHE_UNTIL = 0.0
_LOCK = threading.Lock()
MAX_ENTRIES = 100_000
MAX_MOUNTS = 64


def mount_directories(text):
    mounts = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 7 or '-' not in fields:
            continue
        path = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), fields[4])
        mounts[path] = 'ro' in fields[5].split(',')
    return mounts


def directory_size(path, excluded, deadline):
    """Allocated bytes, excluding symlinks, nested mounts and duplicate hard links."""
    seen = set()
    total = entries = 0
    complete = True
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    root = os.open(path, flags)
    root_device = os.fstat(root).st_dev

    def visit(fd, relative, depth):
        nonlocal total, entries, complete
        if depth > 64:
            complete = False
            return
        with os.scandir(fd) as children:
            for child in children:
                if entries >= MAX_ENTRIES or time.monotonic() >= deadline:
                    complete = False
                    return
                entries += 1
                child_path = relative + '/' + child.name
                if child_path in excluded:
                    continue
                try:
                    info = child.stat(follow_symlinks=False)
                    key = (info.st_dev, info.st_ino)
                    if info.st_dev != root_device or stat.S_ISLNK(info.st_mode) or key in seen:
                        continue
                    seen.add(key)
                    if stat.S_ISREG(info.st_mode):
                        total += getattr(info, 'st_blocks', 0) * 512
                    elif stat.S_ISDIR(info.st_mode):
                        nested = os.open(child.name, flags, dir_fd=fd)
                        try:
                            visit(nested, child_path, depth + 1)
                        finally:
                            os.close(nested)
                except OSError:
                    complete = False
    try:
        visit(root, path.rstrip('/'), 0)
    finally:
        os.close(root)
    return total, complete


def inspect_storage(configured, mount_text=None):
    if mount_text is None:
        try:
            mount_text = Path('/proc/self/mountinfo').read_text()
        except OSError:
            mount_text = ''
    mounts = mount_directories(mount_text)
    candidates = set(configured)
    for path in mounts:
        if path != '/' and not any(path == prefix or path.startswith(prefix + '/') for prefix in ('/proc', '/sys', '/dev')):
            try:
                if stat.S_ISDIR(os.lstat(path).st_mode):
                    candidates.add(path)
            except OSError:
                pass
    directories = []
    deadline = time.monotonic() + 4
    for path in sorted(candidates)[:MAX_MOUNTS]:
        ancestor = next((m for m in sorted(mounts, key=len, reverse=True) if path == m or path.startswith(m.rstrip('/') + '/')), None)
        row = StorageDirectory(path=path, mounted=(ancestor != '/' if ancestor else None), mount_point=ancestor,
                               read_only=mounts.get(ancestor))
        try:
            info = os.lstat(path)
            if not stat.S_ISDIR(info.st_mode):
                row.message = 'Not a directory; symbolic links are not scanned.'
            else:
                usage = os.statvfs(path)
                row.filesystem_total_bytes = usage.f_blocks * usage.f_frsize
                row.filesystem_free_bytes = usage.f_bavail * usage.f_frsize
                row.directory_bytes, row.size_complete = directory_size(path, set(mounts) - {path}, min(deadline, time.monotonic() + 1))
                if not row.size_complete:
                    row.message = 'Partial size: scan limit or unreadable entries.'
        except OSError:
            row.message = 'Directory missing or unavailable.'
        directories.append(row)
    return StorageReport(checked_at=datetime.now(timezone.utc), directories=directories,
                         mount_detection='available' if mounts else 'unavailable',
                         message='Some directories omitted: mount limit reached.' if len(candidates) > MAX_MOUNTS else '')


def configured_directories():
    from sqlalchemy.engine import make_url
    from app.config.settings import get_settings
    settings = get_settings()
    paths = {os.environ.get('IPFS_PATH', '/data/ipfs'), os.environ.get('ZERONET_DATA_DIR', '/data/zeronet'),
             '/var/lib/acestream', '/var/lib/acestream-check', '/var/lib/cloudflare-warp',
             os.environ.get('LOG_DIR', '/app/logs'), settings.PLAYER_HLS_DIR}
    for value in (settings.DATABASE_URL, settings.LEGACY_DATABASE_URL):
        url = make_url(value)
        if url.get_backend_name() == 'sqlite' and url.database and url.database != ':memory:':
            paths.add(str(Path(url.database).absolute().parent))
    return sorted({os.path.abspath(path) for path in paths if path})


def storage_report():
    from app.config.settings import get_settings
    global _CACHE, _CACHE_UNTIL
    warnings = [ConfigurationWarning(**item) for item in get_settings().configuration_warnings]
    if _CACHE is not None and time.monotonic() < _CACHE_UNTIL:
        return _CACHE.model_copy(update={'configuration_warnings': warnings})
    if not _LOCK.acquire(blocking=False):
        if _CACHE is not None:
            return _CACHE.model_copy(update={'message': 'Showing the previous scan while storage is refreshed.'})
        raise RuntimeError('Storage scan is already running')
    try:
        root = Path(__file__).resolve().parents[2]
        try:
            result = subprocess.run([sys.executable, '-m', 'app.services.storage_service'],
                                    input=json.dumps(configured_directories()), text=True, capture_output=True, timeout=8,
                                    cwd=root, env={'PATH': os.defpath, 'PYTHONPATH': str(root)})
            if result.returncode:
                raise ValueError('Storage scan failed')
            report = StorageReport.model_validate_json(result.stdout)
        except (subprocess.TimeoutExpired, ValueError):
            report = StorageReport(checked_at=datetime.now(timezone.utc), directories=[], mount_detection='unavailable',
                                   message='Storage scan could not finish. Try again later.')
        report.configuration_warnings = warnings
        _CACHE, _CACHE_UNTIL = report, time.monotonic() + 60
        return report
    finally:
        _LOCK.release()


if __name__ == '__main__':
    print(inspect_storage(json.loads(sys.stdin.read())).model_dump_json())
