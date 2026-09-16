import os
import time
from unittest.mock import Mock
from app.services.storage_service import directory_size, inspect_storage, mount_directories


def test_mount_parsing_and_shared_filesystem_space(tmp_path):
    root = tmp_path / 'mapped space'
    root.mkdir()
    (root / 'data').write_bytes(b'x' * 8192)
    sub = root / 'config'
    sub.mkdir()
    escaped = str(root).replace(' ', r'\040')
    mounts = f'1 0 0:1 / / rw - overlay overlay rw\n2 1 0:2 / {escaped} ro - ext4 /dev/test ro'
    assert mount_directories(mounts)[str(root)] is True
    report = inspect_storage([str(root), str(sub)], mounts)
    by_path = {row.path: row for row in report.directories}
    assert by_path[str(root)].mounted is True
    assert by_path[str(sub)].mount_point == str(root)
    assert by_path[str(sub)].read_only is True
    assert by_path[str(root)].directory_bytes >= 8192
    assert by_path[str(root)].filesystem_total_bytes == by_path[str(sub)].filesystem_total_bytes
    assert by_path[str(sub)].filesystem_free_bytes > 0


def test_directory_size_skips_links_nested_mounts_and_duplicate_hardlinks(tmp_path):
    (tmp_path / 'file').write_bytes(b'x' * 8192)
    os.link(tmp_path / 'file', tmp_path / 'hardlink')
    (tmp_path / 'symlink').symlink_to(tmp_path, target_is_directory=True)
    mounted = tmp_path / 'child'
    mounted.mkdir()
    (mounted / 'file').write_bytes(b'x' * 8192)
    size, complete = directory_size(str(tmp_path), {str(mounted)}, time.monotonic() + 2)
    assert size == (tmp_path / 'file').stat().st_blocks * 512
    assert complete
    _, complete = directory_size(str(tmp_path), set(), time.monotonic() - 1)
    assert not complete


def test_missing_and_nonlinux_mounts_are_unknown(tmp_path):
    report = inspect_storage([str(tmp_path / 'missing')], '')
    row = report.directories[0]
    assert row.mounted is None and row.directory_bytes is None
    assert row.filesystem_free_bytes is None
    assert report.mount_detection == 'unavailable'


def test_storage_api_auth_and_cache(client, monkeypatch):
    from app.services import storage_service as service
    from app.schemas.storage import StorageReport
    from datetime import datetime, timezone
    report = StorageReport(checked_at=datetime.now(timezone.utc), directories=[], mount_detection='available')
    monkeypatch.setattr(service, '_CACHE', None)
    run = Mock(return_value=Mock(returncode=0, stdout=report.model_dump_json()))
    monkeypatch.setattr(service.subprocess, 'run', run)
    monkeypatch.setenv('API_TOKEN', 'secret')
    assert client.get('/api/v1/system/storage').status_code == 401
    run.assert_not_called()
    for _ in range(2):
        assert client.get('/api/v1/system/storage', headers={'X-Api-Token': 'secret'}).status_code == 200
    run.assert_called_once()
