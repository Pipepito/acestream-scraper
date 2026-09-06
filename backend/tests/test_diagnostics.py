from io import BytesIO
import json
import os
from zipfile import ZipFile

from app.services.diagnostics_service import build_bundle, read_tail, redact, LIMIT
from capture_logs import capture


def test_capture_rotates_and_preserves_console(tmp_path):
    console = BytesIO()
    data = b'engine started\n' * 100
    capture(BytesIO(data), console, tmp_path, max_bytes=200)
    assert console.getvalue() == data
    assert len(list(tmp_path.iterdir())) == 3
    assert all(p.stat().st_size <= 200 for p in tmp_path.iterdir())
    assert b'engine started' in (tmp_path / 'console.log').read_bytes()


def test_capture_disk_failure_keeps_draining(tmp_path):
    console = BytesIO()
    capture(BytesIO(b'engine exited\n'), console, tmp_path / 'missing')
    assert console.getvalue() == b'engine exited\n'


def test_export_is_bounded_redacted_and_rejects_symlinks(tmp_path, monkeypatch):
    monkeypatch.setenv('LOG_DIR', str(tmp_path))
    monkeypatch.setenv('SUPERVISOR_RUN_DIR', str(tmp_path))
    monkeypatch.setenv('API_TOKEN', 'configured-private-token')
    (tmp_path / 'console.log').write_text('x' * LIMIT + '\nAuthorization: Bearer xyz\nhttps://u:pass@private.test/api?token=abc\nconfigured-private-token\nengine exited with status 137\n')
    secret = tmp_path / 'private.txt'
    secret.write_text('must not be exported')
    (tmp_path / 'console.log.1').symlink_to(secret)
    (tmp_path / 'acestream.pid').write_text('123')
    with ZipFile(BytesIO(build_bundle())) as archive:
        assert set(archive.namelist()) == {'manifest.json', 'logs/console.log'}
        text = archive.read('logs/console.log').decode()
        assert '137' in text
        for value in ('xyz', 'private.test', 'configured-private-token', 'must not be exported'):
            assert value not in text
        manifest = json.loads(archive.read('manifest.json'))
        assert manifest['logs']['console.log']['truncated']
        assert manifest['supervisor']['acestream']['pid'] == 123
        assert not manifest['logs']['console.log.1']['available']


def test_non_regular_files_are_not_read(tmp_path):
    os.mkfifo(tmp_path / 'console.log')
    assert read_tail(tmp_path, 'console.log') == (None, False)


def test_redact_key_value_and_json_credentials():
    result = redact('password=secret123 {"api_token": "abc123"} license: value123\nCookie: session=456\n192.168.2.10')
    for value in ('secret123', 'abc123', 'value123', '456', '192.168.2.10'):
        assert value not in result


def test_empty_flavour_bundle_and_endpoint_auth(client, monkeypatch, tmp_path):
    monkeypatch.setenv('LOG_DIR', str(tmp_path))
    monkeypatch.setenv('API_TOKEN', 'private')
    assert client.get('/api/v1/system/diagnostics').status_code == 401
    response = client.get('/api/v1/system/diagnostics', headers={'Authorization': 'Bearer private'})
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/zip'
    assert response.headers['cache-control'] == 'no-store'
    assert 'attachment' in response.headers['content-disposition']
    with ZipFile(BytesIO(response.content)) as archive:
        assert archive.namelist() == ['manifest.json']


def test_export_remains_available_during_startup_failure(client, monkeypatch, tmp_path):
    from app.services.startup_service import startup_service
    monkeypatch.setenv('LOG_DIR', str(tmp_path))
    monkeypatch.setattr(startup_service, 'active', True)
    monkeypatch.setattr(startup_service, 'status', 'failed')
    assert client.get('/api/v1/system/diagnostics').status_code == 200


def test_export_busy_returns_retryable_error(client):
    from app.services.diagnostics_service import _lock
    with _lock:
        response = client.get('/api/v1/system/diagnostics')
    assert response.status_code == 503
    assert response.headers['retry-after'] == '2'


def test_long_unbroken_log_line_is_safe_to_redact():
    assert redact('x' * LIMIT) == 'x' * LIMIT
