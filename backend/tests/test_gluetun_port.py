"""Forwarded ports are untrusted shared-file data, not engine commands."""
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from gluetun_port import read_port, reserved_ports


@pytest.mark.parametrize("raw, expected", [
    (b"45678\n", 45678), (b" 1024 ", 1024), (b"65535", 65535),
    (b"0", None), (b"1023", None), (b"65536", None), (b"", None),
    (b"45678,45679", None), (b"45678\n45679", None), (b"+45678", None),
    (b"$(touch /tmp/no)", None), (b"40000;exit", None), (b"9" * 100, None),
    (b"\xff", None), (b"8622", None),
])
def test_port_validation(tmp_path, raw, expected):
    file = tmp_path / "port"
    file.write_bytes(raw)
    assert read_port(str(file), {8622}) == expected


def test_missing_symlink_directory_and_fifo_do_not_block(tmp_path):
    missing = tmp_path / "missing"
    assert read_port(str(missing), set()) is None
    assert read_port(str(tmp_path), set()) is None
    target = tmp_path / "target"
    target.write_text("45678")
    link = tmp_path / "link"
    link.symlink_to(target)
    assert read_port(str(link), set()) is None
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    assert read_port(str(fifo), set()) is None


def test_reserved_ports_follow_runtime_overrides(monkeypatch):
    monkeypatch.setenv("FLASK_PORT", "45678")
    monkeypatch.setenv("ACESTREAM_HTTP_PORT", "45679")
    assert {45678, 45679, 8622, 6880, 62063} <= reserved_ports()


def test_supervisor_rotates_port_without_overriding_stop(tmp_path):
    root = Path(__file__).resolve().parents[2]
    source = (root / "entrypoint.sh").read_text()
    # Execute the real supervisor with an inert foreground engine. No network,
    # Docker, cache cleanup or installed engine is required for lifecycle checks.
    functions = source[source.index("normalize_bool() {"):source.index("# Supervise an auxiliary service:")]
    state = tmp_path / "run"
    state.mkdir()
    launch_file = tmp_path / "launches"
    port_file = tmp_path / "port"
    port_file.write_text("45678")
    engine = tmp_path / "engine.py"
    engine.write_text("import os, time\nwith open(os.environ['LAUNCH_FILE'], 'a') as f:\n f.write(os.environ.get('ACESTREAM_FORWARDED_PORT', 'default') + '\\n')\ntime.sleep(120)\n")
    # A sibling helper is discovered in exactly the same way as in the image.
    (tmp_path / "gluetun_port.py").write_text((root / "backend/gluetun_port.py").read_text())
    script = tmp_path / "supervisor.sh"
    script.write_text('set -euo pipefail\ncapture_output() { :; }\n' + functions + '\nsupervise_engine "$TEST_ENGINE_COMMAND"\n')
    env = {**os.environ, "SUPERVISOR_RUN_DIR": str(state), "CAPTURE_SCRIPT": str(tmp_path / "capture_logs.py"),
           "CAPTURE_PYTHON": sys.executable, "ACESTREAM_GLUETUN_PORT_FILE": str(port_file),
           "LAUNCH_FILE": str(launch_file), "TEST_ENGINE_COMMAND": f'exec "{sys.executable}" "{engine}"'}
    log = tmp_path / "log"

    def wait_for(predicate):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.1)
        pytest.fail(log.read_text())

    def launches():
        return launch_file.read_text().splitlines() if launch_file.exists() else []

    def request(action):
        request_file = state / "request"
        request_file.write_text(action)
        request_file.replace(state / "acestream.command")

    with log.open("w") as output:
        proc = subprocess.Popen(["bash", str(script)], env=env, stdout=output, stderr=output)
        try:
            wait_for(lambda: "45678" in launches())
            count = len(launches())
            port_file.write_text("0")
            wait_for(lambda: "unavailable" in log.read_text())
            assert len(launches()) == count
            request("stop")
            wait_for(lambda: (state / "acestream.stopped").exists() and not (state / "acestream.pid").exists())
            port_file.write_text("45679")
            wait_for(lambda: "changed to 45679" in log.read_text())
            assert len(launches()) == count
            request("start")
            wait_for(lambda: launches()[-1] == "45679")
            assert len(launches()) == count + 1
            # No restart for an unchanged port, then rotate during active use.
            port_file.write_text("45680")
            wait_for(lambda: launches()[-1] == "45680")
            assert len(launches()) == count + 2
        finally:
            proc.terminate()
            proc.wait(timeout=10)
    assert not (state / "acestream.pid").exists()


def test_packaged_launcher_passes_port_and_foreground_flags(tmp_path):
    root = Path(__file__).resolve().parents[2]
    recorder = tmp_path / "engine"
    recorder.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    recorder.chmod(0o755)
    launcher = tmp_path / "launcher"
    launcher.write_text((root / "docker/scripts/start-playback-engine").read_text().replace('/opt/acestream/start-engine', str(recorder)))
    result = subprocess.run(['bash', str(launcher), '--bind-all'], env={**os.environ, 'ACESTREAM_FORWARDED_PORT': '45678', 'ACESTREAM_HTTP_PORT': '6878'}, text=True, capture_output=True, check=True)
    args = result.stdout.splitlines()
    assert args[args.index('--port') + 1] == '45678'
    assert args[args.index('--http-port') + 1] == '6878'
    assert args[args.index('--live-mem-cache-size') + 1] == '67108864'
    assert args.count('--port') == 1
    assert '--client-console' in args and '--bind-all' in args
    assert '--daemon' not in args
    normal_env = {**os.environ, 'ACESTREAM_FORWARDED_PORT': ''}
    result = subprocess.run(['bash', str(launcher)], env=normal_env, text=True, capture_output=True, check=True)
    assert '--port' not in result.stdout.splitlines()


def test_changelog_tracks_selected_release():
    root = Path(__file__).resolve().parents[2]
    import re
    notes = (root / 'frontend/src/data/changelog.ts').read_text()
    versions = re.findall(r'"version": "(v\d+\.\d+\.\d+)"', notes)
    assert versions[0] == (root / 'version.txt').read_text().strip()
    assert len(versions) == len(set(versions))


@pytest.mark.parametrize('enabled, command, message', [
    ('false', 'exec /opt/acestream/start-playback-engine', 'requires the bundled playback engine'),
    ('true', 'exec custom-engine --port 12345', 'requires the packaged playback command'),
])
def test_sync_rejects_unsupported_engine_configuration(tmp_path, enabled, command, message):
    root = Path(__file__).resolve().parents[2]
    env = {**os.environ, 'LOG_DIR': str(tmp_path / 'logs'), 'LOGROTATE_DIR': str(tmp_path / 'rotation'),
           'SUPERVISOR_RUN_DIR': str(tmp_path / 'run'), 'ENABLE_WARP': 'false',
           'ENABLE_ACESTREAM_ENGINE': enabled, 'IMAGE_HAS_ACESTREAM': enabled,
           'ENABLE_ACEXY': 'false', 'ENABLE_IPFS': 'false', 'ENABLE_ZERONET': 'false',
           'ACESTREAM_GLUETUN_PORT_FILE': str(tmp_path / 'port'), 'ACESTREAM_START_COMMAND': command}
    result = subprocess.run(['bash', str(root / 'entrypoint.sh'), 'true'], env=env, text=True, capture_output=True, timeout=15)
    assert result.returncode != 0
    assert message in result.stdout + result.stderr
