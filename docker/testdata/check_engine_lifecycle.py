"""Runs inside a disposable container; never point at a serving engine."""
import json
import os
from pathlib import Path
import time
import urllib.request

RUN = Path('/run/acestream-scraper')


def ready(port):
    try:
        url = f'http://127.0.0.1:{port}/webui/api/service?method=get_version'
        with urllib.request.urlopen(url, timeout=2) as response:
            return json.load(response)['result']['version']
    except Exception:
        return None


def pid(name):
    try:
        return int((RUN / f'{name}.pid').read_text().strip())
    except FileNotFoundError:
        return None


def wait_for(predicate, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(1)
    raise AssertionError('Timed out waiting for engine lifecycle transition')


def main():
    wait_for(lambda: ready(6878) and ready(6880), 75)
    playback = pid('acestream')
    checker = pid('acestream-check')
    assert playback and checker and playback != checker
    print('Both engines ready:', ready(6878), ready(6880), flush=True)
    for directory in ('/var/lib/acestream-check', '/var/lib/acestream-check/cache'):
        assert Path(directory).is_dir()
    # Android's application identity must also belong to its dedicated home.
    identity = Path('/var/lib/acestream-check/.device_id')
    primary_identity = Path('/var/lib/acestream/.device_id')
    if identity.is_file() and primary_identity.is_file():
        assert identity.read_text() != primary_identity.read_text()

    os.kill(checker, 9)

    def recovered():
        assert ready(6878), 'Checker crash affected playback engine API'
        assert pid('acestream') == playback, 'Playback engine restarted'
        return pid('acestream-check') not in (None, checker) and ready(6880)

    wait_for(recovered, 40)
    print('Checker crash recovered without restarting playback', flush=True)
    request = RUN / 'request.tmp'
    request.write_text('stop')
    request.replace(RUN / 'acestream-check.command')
    wait_for(lambda: pid('acestream-check') is None, 15)
    assert ready(6878) and pid('acestream') == playback
    assert (RUN / 'acestream-check.stopped').is_file()
    print('Checker Stop leaves playback running', flush=True)


if __name__ == '__main__':
    main()
