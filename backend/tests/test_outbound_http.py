"""Connection-level regressions for source DNS pinning and redirect validation."""
import ipaddress
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock

import pytest
import requests

from app.utils import url_guard
from app.utils.outbound_http import PinnedHTTPAdapter, source_get, source_session


@pytest.fixture
def origin(monkeypatch):
    seen = []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers['Host']))
            if self.path == '/redirect':
                self.send_response(302)
                self.send_header('Location', 'http://169.254.169.254/latest')
            else:
                self.send_response(200)
            self.end_headers()
            self.wfile.write(b'checked origin')
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv('ALLOW_PRIVATE_SCRAPE_TARGETS', 'true')
    # The hostname has no real DNS entry: only the checked answer can connect.
    def resolve(host):
        return [ipaddress.ip_address('127.0.0.1' if host == 'pinned.example' else host)]
    monkeypatch.setattr(url_guard, '_resolve_addresses', resolve)
    yield f'http://pinned.example:{server.server_port}', seen
    server.shutdown()
    server.server_close()
    thread.join()


def test_sync_client_pins_connection_and_preserves_host(origin, monkeypatch):
    url, seen = origin
    monkeypatch.setenv('HTTP_PROXY', 'http://169.254.169.254:8080')
    assert source_get(url).content == b'checked origin'
    assert seen == [('/', url.removeprefix('http://'))]


@pytest.mark.asyncio
async def test_async_connection_and_redirect_to_literal_metadata(origin):
    url, seen = origin
    async with source_session() as session:
        async with session.get(url) as response:
            assert await response.text() == 'checked origin'
        with pytest.raises(url_guard.BlockedURLError, match='metadata'):
            async with session.get(url + '/redirect'):
                pass
    assert [path for path, host in seen] == ['/', '/redirect']
    assert all(host == url.removeprefix('http://') for path, host in seen)


@pytest.mark.asyncio
async def test_dns_rebinding_is_rejected_at_the_connection(origin, monkeypatch):
    url, seen = origin
    answers = iter(['127.0.0.1', '169.254.169.254'])
    monkeypatch.setattr(url_guard, '_resolve_addresses', lambda host: [ipaddress.ip_address(next(answers))])
    async with source_session() as session:
        with pytest.raises(url_guard.BlockedURLError, match='metadata'):
            async with session.get(url):
                pass
    assert seen == []


def test_tls_pool_keeps_hostname_verification_and_sni(monkeypatch):
    monkeypatch.setenv('ALLOW_PRIVATE_SCRAPE_TARGETS', 'false')
    monkeypatch.setattr(url_guard, '_resolve_addresses', lambda host: [ipaddress.ip_address('8.8.8.8')])
    adapter = PinnedHTTPAdapter()
    adapter.poolmanager = Mock()
    request = requests.Request('GET', 'https://source.example:8443/guide').prepare()
    adapter.get_connection_with_tls_context(request, verify=True)
    args, kwargs = adapter.poolmanager.connection_from_host.call_args
    assert args == ('8.8.8.8',)
    assert kwargs['pool_kwargs']['server_hostname'] == 'source.example'
    assert kwargs['pool_kwargs']['assert_hostname'] == 'source.example'
    assert kwargs['pool_kwargs'].get('cert_reqs') != 'CERT_NONE'
    adapter.add_headers(request)
    assert request.headers['Host'] == 'source.example:8443'


@pytest.mark.parametrize('url', ['http://169.254.169.254/', 'https://[fd00:ec2::254]/'])
def test_sync_client_rejects_metadata_before_creating_a_pool(monkeypatch, url):
    from urllib.parse import urlsplit
    monkeypatch.setattr(url_guard, '_resolve_addresses', lambda host: [ipaddress.ip_address(urlsplit(url).hostname)])
    adapter = PinnedHTTPAdapter()
    adapter.poolmanager = Mock()
    with pytest.raises(url_guard.BlockedURLError, match='metadata'):
        adapter.get_connection(url)
    adapter.poolmanager.connection_from_host.assert_not_called()


def test_connection_falls_back_only_to_validated_addresses(origin, monkeypatch):
    url, seen = origin
    monkeypatch.setattr(url_guard, '_resolve_addresses', lambda host: [ipaddress.ip_address('::1'), ipaddress.ip_address('127.0.0.1')])
    assert source_get(url, timeout=3).content == b'checked origin'
    assert len(seen) == 1


def test_real_https_keeps_certificate_identity_sni_and_rejects_untrusted_cert(tmp_path, monkeypatch):
    import ssl
    import subprocess
    key, cert = tmp_path / 'key.pem', tmp_path / 'cert.pem'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(key),
                    '-out', str(cert), '-days', '1', '-subj', '/CN=pinned.example',
                    '-addext', 'subjectAltName=DNS:pinned.example'], check=True, capture_output=True)
    names, hosts = [], []
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hosts.append(self.headers['Host'])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'tls verified')
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    context.set_servername_callback(lambda sock, name, ctx: names.append(name))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv('ALLOW_PRIVATE_SCRAPE_TARGETS', 'true')
    monkeypatch.setattr(url_guard, '_resolve_addresses', lambda host: [ipaddress.ip_address('127.0.0.1')])
    try:
        with requests.Session() as session:
            session.trust_env = False
            session.mount('https://', PinnedHTTPAdapter())
            url = f'https://pinned.example:{server.server_port}/'
            assert session.get(url, verify=str(cert), timeout=3).content == b'tls verified'
        with pytest.raises(requests.exceptions.SSLError):
            source_get(url, timeout=3)
        with requests.Session() as session:
            session.trust_env = False
            session.mount('https://', PinnedHTTPAdapter())
            with pytest.raises(requests.exceptions.SSLError):
                session.get(url.replace('pinned.example', 'wrong.example'), verify=str(cert), timeout=3)
        assert names[0] == 'pinned.example'
        assert hosts == [f'pinned.example:{server.server_port}']
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
