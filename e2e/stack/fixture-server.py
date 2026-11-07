#!/usr/bin/env python3
"""Owned E2E upstreams: synthetic catalogue, playlist, rolling XMLTV and media.

This is a protocol fixture, not an AceStream implementation. Real engine and
sidecar behaviour is covered separately by backend/tests/docker.
"""
import argparse
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import time
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[2]
ROWS = [dict(name=f'E2E Search {n}', infohash=f'{n:040x}', categories=['Test']) for n in range(1, 4)]


def guide():
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
    programmes = []
    for hour in range(24 * 9):
        begins = start + timedelta(hours=hour)
        ends = begins + timedelta(hours=1)
        programmes.append(
            f'<programme channel="e2e-test" start="{begins:%Y%m%d%H%M%S} +0000" stop="{ends:%Y%m%d%H%M%S} +0000">'
            f'<title>E2E programme {hour}</title><desc>Locally generated test programme.</desc></programme>'
        )
    return '<?xml version="1.0"?><tv><channel id="e2e-test"><display-name>E2E Test</display-name></channel>' + ''.join(programmes) + '</tv>'


def scenario(port, target):
    local = f'http://127.0.0.1:{port}'
    app = f'http://host.docker.internal:{port}' if target == 'docker' else local
    return {
        'name': 'controlled-local-fixtures',
        'description': 'Synthetic local upstreams; real application, database and media pipeline. Does not validate real AceStream peers or sidecars.',
        'stack': {'engineUrl': local, 'acexyUrl': local},
        'scrape': {'sources': [{'id': 'controlled', 'label': 'E2E owned playlist', 'url': f'{local}/playlist.m3u', 'dockerUrl': f'{app}/playlist.m3u', 'expectMinChannels': 3}]},
        'search': {'queries': [{'query': 'E2E Search', 'expectMinResults': 3, 'addFirst': 1}]},
        'epg': {'sources': [{'name': 'E2E owned guide', 'url': f'{app}/guide.xml', 'expectMinChannels': 1}], 'targetChannel': {'xmlId': 'e2e-test', 'displayNameContains': 'E2E Test'}},
        'tv': {'channels': [{'name': 'E2E Test TV', 'category': 'Test', 'streamSearchQuery': 'E2E Search', 'epgXmlId': 'e2e-test'}]},
        'playlist': {'baseUrlName': 'E2E fixture proxy', 'baseUrlPattern': f'{local}/ace/getstream?id={{channel_id}}'},
        'integrations': {'playbackChannelName': 'E2E Search', 'playbackTimeoutMs': 60000},
        'errors': {'allowedApiErrorPatterns': [], 'allowedConsolePatterns': []},
    }


class Handler(BaseHTTPRequestHandler):
    def reply(self, body, content_type='application/json', status=200):
        data = (json.dumps(body) if content_type == 'application/json' else body).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlsplit(self.path)
        params = parse_qs(url.query)
        base = f'http://{self.headers["Host"]}'
        if url.path == '/playlist.m3u':
            self.reply('#EXTM3U\n' + ''.join(f'#EXTINF:-1 tvg-id="e2e-test" group-title="Test",E2E Fixture {n}\nacestream://{n + 100:040x}\n' for n in range(1, 4)), 'audio/x-mpegurl')
        elif url.path == '/guide.xml':
            self.reply(guide(), 'application/xml')
        elif url.path == '/search':
            query = params.get('query', [''])[0].casefold()
            rows = [row for row in ROWS if query in row['name'].casefold()]
            page = max(0, int(params.get('page', ['0'])[0]))
            size = min(100, max(1, int(params.get('page_size', ['10'])[0])))
            self.reply({'result': {'results': rows[page * size:(page + 1) * size], 'total': len(rows)}})
        elif url.path == '/webui/api/service':
            self.reply({'result': {'version': 'e2e-fixture', 'platform': 'synthetic'}})
        elif url.path == '/server/api':
            method = params.get('method', [''])[0]
            if method == 'get_content_id':
                infohash = params.get('infohash', [''])[0]
                match = next((row for row in ROWS if row['infohash'] == infohash), None)
                self.reply({'result': {'content_id': f'{int(infohash, 16) + 200:040x}'}} if match else {'error': 'not found'})
            elif method == 'get_status':
                self.reply({'result': {'version': {'version': 'e2e-fixture', 'platform': 'synthetic'}, 'playlist_loaded': True}})
            elif method == 'get_network_connection_status':
                self.reply({'result': {'connected': True}})
            else:
                self.reply({'error': 'unsupported fixture method'}, status=404)
        elif url.path == '/ace/status':
            self.reply({'status': 'synthetic fixture'})
        elif url.path == '/ace/getstream' and params.get('format') == ['json']:
            self.reply({'response': {'playback_url': f'{base}/content/fixture/1', 'stat_url': f'{base}/ace/stat/fixture/s', 'command_url': f'{base}/ace/cmd/fixture/s', 'is_live': 1}, 'error': None})
        elif url.path == '/ace/stat/fixture/s':
            self.reply({'response': {'status': 'dl', 'peers': 3, 'speed_down': 500, 'speed_up': 0}, 'error': None})
        elif url.path == '/ace/cmd/fixture/s':
            self.reply({'response': {'status': 'ok'}, 'error': None})
        elif url.path in ('/content/fixture/1', '/ace/getstream'):
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp2t')
            self.end_headers()
            # Bounded writes; a slow reader blocks this connection only.
            payload = self.server.media
            try:
                while True:
                    for offset in range(0, len(payload), 188 * 5):
                        chunk = payload[offset:offset + 188 * 5]
                        self.wfile.write(chunk)
                        # The pinned sample contains two seconds of media.
                        time.sleep(2 * len(chunk) / len(payload))
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass
        else:
            self.reply({'error': 'unknown fixture route'}, status=404)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=18799)
    parser.add_argument('--target', choices=('local', 'docker'), default='local')
    parser.add_argument('--output', type=Path, default=ROOT / 'e2e/.stack/controlled-scenario.json')
    args = parser.parse_args()
    media = (ROOT / 'backend/tests/docker/fixtures/sample-h264-ac3.m2ts').read_bytes()
    # Docker Desktop needs host.docker.internal; local-only runs bind loopback.
    server = ThreadingHTTPServer(('0.0.0.0' if args.target == 'docker' else '127.0.0.1', args.port), Handler)
    server.media = media
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scenario(server.server_port, args.target), indent=2) + '\n')
    print(f'Fixture scenario: {args.output}\nSynthetic upstream: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
