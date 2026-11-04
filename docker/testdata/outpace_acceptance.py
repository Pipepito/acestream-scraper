"""Exercise Outpace's real HTTP adapter with owned media inside a disposable image."""
import asyncio
from contextlib import contextmanager
import json
import os
import subprocess
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import time
import urllib.error
import urllib.request

from app.models.models import AcestreamChannel
from app.config.database import SessionLocal
from app.services.channel_status_service import ChannelStatusService
from app.services.engine_client import EngineClient

RUN = Path('/run/acestream-scraper')


@contextmanager
def broadcast(port):
    """Feed the repository's two-second A/V sample to this daemon's own broadcast."""
    class Feed(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            # Remux the sample continuously so timestamps and TS packet counters advance.
            args = ['/opt/ffmpeg/bin/ffmpeg', '-v', 'error', '-re', '-stream_loop', '-1',
                    '-i', '/app/tests/docker/fixtures/sample-h264-ac3.m2ts',
                    '-c', 'copy', '-muxrate', '1M', '-f', 'mpegts', 'pipe:1']
            with subprocess.Popen(args, stdout=subprocess.PIPE) as encoder:
                try:
                    while chunk := encoder.stdout.read(188 * 64):
                        self.wfile.write(chunk)
                except OSError:
                    pass
                finally:
                    encoder.kill()

    url = f'http://127.0.0.1:{port}/broadcast/smoke/source'
    with ThreadingHTTPServer(('127.0.0.1', 0), Feed) as feed:
        worker = Thread(target=feed.serve_forever)
        worker.start()
        try:
            request = urllib.request.Request(url, method='PUT', headers={'Content-Type': 'application/json'},
                data=json.dumps({'url': f'http://127.0.0.1:{feed.server_port}/media'}).encode())
            with urllib.request.urlopen(request, timeout=5) as r:
                content_id = json.load(r)['content_id']
            yield content_id
        finally:
            feed.shutdown()
            worker.join()
            with urllib.request.urlopen(urllib.request.Request(url, method='DELETE'), timeout=10):
                pass


def main():
    base = 'http://127.0.0.1:6878'
    for port in (6878, 6880):
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/webui/api/service?method=get_version', timeout=5) as r:
            assert json.load(r)['result']['version'] == '0.9.0'
    try:
        urllib.request.urlopen(base + '/search?query=smoke', timeout=5)
    except urllib.error.HTTPError as error:
        assert error.code == 404
    else:
        raise AssertionError('Review search support for this version')

    try:
        urllib.request.urlopen('http://127.0.0.1:8000/api/v1/search?query=smoke', timeout=5)
    except urllib.error.HTTPError as error:
        assert error.code == 501 and json.load(error)['error']['code'] == 'SEARCH_CATALOGUE_UNSUPPORTED'
    else:
        raise AssertionError('The app must identify the missing catalogue')

    with broadcast(6878) as content_id, EngineClient(base) as engine:
        a, b = engine.start(content_id), engine.start(content_id)
        assert a.command_url != b.command_url
        with urllib.request.urlopen(a.playback_url, timeout=60) as first, urllib.request.urlopen(b.playback_url, timeout=60) as second:
            assert first.read(188)[0] == second.read(188)[0] == 0x47
            first.close()
            engine.stop(a)
            assert second.read(188)[0] == 0x47
        engine.stop(b)
        for session in (a, b):
            with urllib.request.urlopen(session.stat_url, timeout=5) as r:
                assert json.load(r)['error']
    with broadcast(6880) as content_id, SessionLocal() as db:
        service = ChannelStatusService(db)
        assert service._get_engine_url() == 'http://127.0.0.1:6880'
        result = asyncio.run(service.check_channel_status(AcestreamChannel(id=content_id, name='Smoke'), persist=False))
        assert result['is_online'], result
    assert Path('/var/lib/outpace/identity.seed').read_bytes() != Path('/var/lib/outpace-check/identity.seed').read_bytes()
    playback_pid = (RUN / 'acestream.pid').read_text()
    old_checker = (RUN / 'acestream-check.pid').read_text()
    os.kill(int(old_checker), 9)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        checker = RUN / 'acestream-check.pid'
        if checker.exists() and checker.read_text() != old_checker:
            try:
                with urllib.request.urlopen('http://127.0.0.1:6880/healthz', timeout=2) as r:
                    assert r.status == 200
                break
            except OSError:
                pass
        time.sleep(1)
    else:
        raise AssertionError('Checker failed to recover')
    assert (RUN / 'acestream.pid').read_text() == playback_pid
    print('Verified two playback readers, isolated media check, checker restart and catalogue limitation.')


if __name__ == '__main__':
    main()
