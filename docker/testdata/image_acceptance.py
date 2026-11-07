"""Acceptance probes for an already-built production image; standard library only.

The private CI driver starts the image with its real entrypoint and injects this
file through stdin. No application source or replacement packages are mounted.
Never run the lifecycle probe against a serving installation.
"""
import argparse
import http.cookiejar
import json
import os
import re
from pathlib import Path
import subprocess
import struct
import threading
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def fetch(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.read()


def first_run_accounts():
    """Exercise the wizard's explicit opt-out on a disposable fresh container."""
    base = 'http://127.0.0.1:8000'
    browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    try:
        with browser.open(base + '/api/v1/auth/status', timeout=5) as response:
            status = json.load(response)
    except urllib.error.HTTPError as error:
        # The same pinned probe also validates protected branches predating
        # accounts. Only an absent endpoint is compatible; auth/server errors
        # must fail. The caller still verifies the legacy public OpenAPI route.
        if error.code == 404:
            return
        raise
    assert status['mode'] == 'pending', 'Fresh images must offer account setup'
    for path in ('/api/v1/config', '/openapi.json'):
        try:
            fetch(base + path)
        except urllib.error.HTTPError as error:
            assert error.code == 401, (path, error.code)
        else:
            raise AssertionError(f'Pending setup exposed {path}')
    request = urllib.request.Request(base + '/api/v1/auth/bootstrap',
        data=json.dumps({'enabled': False, 'username': 'unused', 'password': 'unused',
                         'password_confirmation': 'unused'}).encode(),
        headers={'Content-Type': 'application/json', 'X-CSRF-Token': status['csrf']})
    with browser.open(request, timeout=5) as response:
        assert response.status == 200


def wait_for(check, seconds=120):
    deadline = time.monotonic() + seconds
    last = None
    while time.monotonic() < deadline:
        try:
            return check()
        except (OSError, ValueError, AssertionError) as error:
            last = error
            time.sleep(2)
    raise AssertionError(f"Image probe did not become ready: {last}")


def engine_version(host, expected):
    payload = json.loads(fetch(f'http://{host}:6878/webui/api/service?method=get_version'))
    assert payload.get('error') is None, payload
    actual = str(payload['result']['version'])
    assert actual and expected.startswith(actual), (actual, expected)


def needed_libraries(blob):
    """Read DT_NEEDED from ELF32/64 without adding binutils to the image."""
    assert blob[:4] == b'\x7fELF' and blob[5] == 1, 'Expected little-endian ELF'
    wide = blob[4] == 2
    assert blob[4] in (1, 2)
    phoff = struct.unpack_from('<Q' if wide else '<I', blob, 32 if wide else 28)[0]
    size, count = struct.unpack_from('<HH', blob, 54 if wide else 42)
    segments = []
    dynamic = None
    for index in range(count):
        offset = phoff + index * size
        if wide:
            kind, _, fileoff, vaddr, _, filesz, _, _ = struct.unpack_from('<IIQQQQQQ', blob, offset)
        else:
            kind, fileoff, vaddr, _, filesz, _, _, _ = struct.unpack_from('<IIIIIIII', blob, offset)
        if kind == 1:
            segments.append((vaddr, fileoff, filesz))
        elif kind == 2:
            dynamic = (fileoff, filesz)
    assert dynamic is not None, 'Missing ELF dynamic segment'
    names, strings = [], None
    for offset in range(dynamic[0], sum(dynamic), 16 if wide else 8):
        tag, value = struct.unpack_from('<QQ' if wide else '<II', blob, offset)
        if tag == 0:
            break
        if tag == 1:
            names.append(value)
        if tag == 5:
            strings = value
    assert strings is not None, 'Missing ELF string table'
    base = next(fileoff + strings - vaddr for vaddr, fileoff, filesz in segments
                if vaddr <= strings < vaddr + filesz)
    return {blob[base + name:blob.index(b'\0', base + name)].decode('ascii') for name in names}


def layout(platform, expected):
    root = Path('/opt/acestream')
    metadata = (root / 'install-metadata.txt').read_text()
    for value in (f'platform={platform}', 'kind=oci-image', f'engine_version={expected}',
                  'distribution=jopsis/acestream v3.2.17-fix',
                  'engine_source=oci:jopsis/acestream:v3.2.17-fix@sha256:'):
        assert value in metadata, value
    required = {'main.py.oci-orig', 'main_linux.py', 'bionic_dns.py', 'bionic_dns_proxy.py',
                'app_bridge.py', 'app_bridge.py.oci-orig', 'engine_version.json',
                'modules.zip', 'python', 'lib', 'start-engine'}
    assert required <= {p.name for p in root.iterdir()}
    assert not (root / 'install_id').exists()
    assert not (root / 'engine_runtime.json').exists()
    linker, libdir = ('linker64', 'lib64') if platform == 'linux/arm64' else ('linker', 'lib')
    for path in (root / 'start-engine', root / 'python/bin/python', Path('/system/bin') / linker):
        assert os.access(path, os.X_OK), path
    library = (Path('/system') / libdir / 'libnetd_client.so').read_bytes()
    needed = needed_libraries(library)
    assert 'libc.so' in needed and 'libc.so.6' not in needed, needed


class ExternalEngineFixture(BaseHTTPRequestHandler):
    """Loopback-only upstream for the engine-free Acexy flavor, never real media."""
    def do_GET(self):
        body = json.dumps({'result': {'version': '3.2.11', 'status': 'idle'}}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def runtime(flavor, expected):
    server = None
    if flavor == 'scraper-acexy':
        server = ThreadingHTTPServer(('127.0.0.2', 6878), ExternalEngineFixture)
        threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        wait_for(lambda: json.loads(fetch('http://127.0.0.1:8000/api/v1/health')))
        # Probe the shipped SPA and schema through the running application.
        html = fetch('http://127.0.0.1:8000/').decode()
        assert '<html' in html.lower()
        assets = re.findall(r'(?:src|href)=[\"\'](/assets/[^\"\']+)[\"\']', html)
        assert assets, 'SPA has no built assets'
        for asset in assets:
            assert fetch('http://127.0.0.1:8000' + asset), asset
        first_run_accounts()
        schema = json.loads(fetch('http://127.0.0.1:8000/openapi.json'))
        assert '/api/v1/health' in schema['paths']
        assert Path('/usr/local/bin/engine_cache_cleanup.py').is_file()
        subprocess.run(['/opt/ffmpeg/bin/ffmpeg', '-version'], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['/opt/ffmpeg/bin/ffprobe', '-version'], check=True, stdout=subprocess.DEVNULL)
        if 'acestream' in flavor:
            assert os.access('/opt/acestream/bin/acestreamengine', os.X_OK)
            wait_for(lambda: engine_version('127.0.0.1', expected), seconds=240)
            json.loads(fetch('http://127.0.0.1:6878/server/api?api_version=3&method=get_status'))
        if 'acexy' in flavor:
            usage = subprocess.run(['/opt/acexy/bin/acexy', '--help'], capture_output=True, text=True)
            assert (usage.stdout + usage.stderr).strip()
            assert 'fixture acexy' not in usage.stdout + usage.stderr
            wait_for(lambda: fetch('http://127.0.0.1:8080/ace/status'))
        subprocess.run(['/usr/local/bin/healthcheck.sh'], check=True, timeout=30)
    finally:
        if server:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--flavor', required=True)
    parser.add_argument('--platform', required=True)
    parser.add_argument('--engine-version', default='')
    parser.add_argument('--layout', action='store_true')
    parser.add_argument('--remote-engine')
    args = parser.parse_args()
    if args.remote_engine:
        engine_version(args.remote_engine, args.engine_version)
    elif args.layout:
        layout(args.platform, args.engine_version)
    else:
        runtime(args.flavor, args.engine_version)
    print('Production image acceptance passed', flush=True)
