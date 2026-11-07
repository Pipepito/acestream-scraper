"""Concurrent Overview requests share a bounded, DB-independent storage scan."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from datetime import datetime, timezone
import subprocess
from threading import Event, Lock
import time
from unittest.mock import Mock

import pytest

from app.schemas.storage import StorageReport
from app.services import storage_service as service


@pytest.fixture(autouse=True)
def isolated_storage_cache(monkeypatch):
    monkeypatch.setattr(service, '_CACHE', None)
    monkeypatch.setattr(service, '_CACHE_UNTIL', 0.0)
    monkeypatch.setattr(service, '_LOCK', Lock())


@pytest.mark.parametrize('worker_timeout', [False, True])
def test_concurrent_cold_requests_share_one_scan(client, monkeypatch, worker_timeout):
    started, release = Event(), Event()
    report = StorageReport(checked_at=datetime.now(timezone.utc), directories=[], mount_detection='available')

    def scan(*args, **kwargs):
        assert kwargs['timeout'] == 8
        started.set()
        assert release.wait(5), 'test did not release the scan worker'
        if worker_timeout:
            raise subprocess.TimeoutExpired(args[0], 8)
        return Mock(returncode=0, stdout=report.model_dump_json())

    run = Mock(side_effect=scan)
    monkeypatch.setattr(service.subprocess, 'run', run)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(client.get, '/api/v1/system/storage')
        assert started.wait(5)
        second = pool.submit(client.get, '/api/v1/system/storage')
        try:
            # A second cold request waits for the result instead of returning
            # the transient 503 seen when Overview is opened twice quickly.
            with pytest.raises(FutureTimeout):
                second.result(timeout=0.1)
        finally:
            release.set()
        responses = [first.result(timeout=5), second.result(timeout=5)]
    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    run.assert_called_once()
    if worker_timeout:
        assert responses[0].json()['mount_detection'] == 'unavailable'
        assert responses[0].json()['directories'] == []
        assert 'could not finish' in responses[0].json()['message']


def test_stale_cached_report_remains_immediate_during_refresh(monkeypatch):
    report = StorageReport(checked_at=datetime.now(timezone.utc), directories=[], mount_detection='available')
    monkeypatch.setattr(service, '_CACHE', report)
    run = Mock()
    monkeypatch.setattr(service.subprocess, 'run', run)
    with service._LOCK:
        result = service.storage_report()
    assert result.checked_at == report.checked_at
    assert 'previous scan' in result.message
    run.assert_not_called()


def test_cold_wait_is_bounded_if_scan_owner_is_stuck(client, monkeypatch):
    monkeypatch.setattr(service, 'COLD_SCAN_WAIT_SECONDS', 0.02, raising=False)
    run = Mock()
    monkeypatch.setattr(service.subprocess, 'run', run)
    started = time.monotonic()
    with service._LOCK:
        response = client.get('/api/v1/system/storage')
    assert time.monotonic() - started < 2
    assert response.status_code == 503
    assert response.headers['retry-after'] == '2'
    run.assert_not_called()
