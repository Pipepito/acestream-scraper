"""
Tests for the outbound URL guard (#149): SSRF protection for user-supplied
scrape and EPG source URLs.
"""

import socket

import pytest

from app.utils import url_guard
from app.utils.url_guard import BlockedURLError, validate_outbound_url


def _fake_resolver(mapping):
    def fake_getaddrinfo(host, port, proto=0, **kwargs):
        if host in mapping:
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (mapping[host], 0))]
        raise socket.gaierror(f"unknown host {host}")
    return fake_getaddrinfo


@pytest.fixture
def resolver(monkeypatch):
    def install(mapping):
        monkeypatch.setattr(socket, "getaddrinfo", _fake_resolver(mapping))
    return install


class TestAlwaysBlocked:
    def test_non_http_scheme(self):
        with pytest.raises(BlockedURLError):
            validate_outbound_url("file:///etc/passwd")
        with pytest.raises(BlockedURLError):
            validate_outbound_url("ftp://example.com/list.m3u")

    def test_missing_host(self):
        with pytest.raises(BlockedURLError):
            validate_outbound_url("http://")

    def test_unresolvable_host(self, resolver):
        resolver({})
        with pytest.raises(BlockedURLError):
            validate_outbound_url("http://does-not-exist.invalid/")

    def test_metadata_endpoint_blocked_even_in_permissive_mode(self, resolver, monkeypatch):
        monkeypatch.setenv("ALLOW_PRIVATE_SCRAPE_TARGETS", "true")
        resolver({
            "metadata.internal": "169.254.169.254",
            "169.254.169.254": "169.254.169.254",
        })
        with pytest.raises(BlockedURLError, match="metadata"):
            validate_outbound_url("http://metadata.internal/latest/meta-data/")
        with pytest.raises(BlockedURLError, match="metadata"):
            validate_outbound_url("http://169.254.169.254/latest/meta-data/")

    def test_ipv6_mapped_metadata_blocked_in_permissive_mode(self, monkeypatch):
        monkeypatch.setenv("ALLOW_PRIVATE_SCRAPE_TARGETS", "true")
        with pytest.raises(BlockedURLError, match="metadata"):
            validate_outbound_url("http://[::ffff:169.254.169.254]/latest/meta-data/")


class TestPermissiveDefault:
    def test_private_targets_allowed_by_default(self, resolver, monkeypatch):
        monkeypatch.delenv("ALLOW_PRIVATE_SCRAPE_TARGETS", raising=False)
        resolver({"nas.local": "192.168.1.50"})
        assert validate_outbound_url("http://nas.local/playlist.m3u") is None

    def test_localhost_allowed_by_default(self, monkeypatch):
        monkeypatch.delenv("ALLOW_PRIVATE_SCRAPE_TARGETS", raising=False)
        assert validate_outbound_url("http://127.0.0.1:6878/status") is None


class TestStrictMode:
    @pytest.fixture(autouse=True)
    def strict(self, monkeypatch):
        monkeypatch.setenv("ALLOW_PRIVATE_SCRAPE_TARGETS", "false")

    def test_blocks_loopback(self):
        with pytest.raises(BlockedURLError, match="non-public"):
            validate_outbound_url("http://127.0.0.1/admin")

    def test_blocks_private_ranges(self, resolver):
        resolver({"internal.example.com": "10.0.0.5"})
        with pytest.raises(BlockedURLError, match="non-public"):
            validate_outbound_url("https://internal.example.com/")

    def test_blocks_link_local(self):
        with pytest.raises(BlockedURLError):
            validate_outbound_url("http://169.254.10.10/")

    def test_allows_public_addresses(self, resolver):
        resolver({"example.com": "93.184.216.34"})
        assert validate_outbound_url("https://example.com/list.m3u") is None

    def test_zeronet_host_is_exempt(self, resolver, monkeypatch):
        monkeypatch.setenv("ZERONET_URL", "http://host.docker.internal:43110")
        resolver({"host.docker.internal": "172.17.0.1"})
        assert validate_outbound_url("http://host.docker.internal:43110/site") is None

    def test_non_zeronet_private_host_still_blocked(self, resolver, monkeypatch):
        monkeypatch.setenv("ZERONET_URL", "http://host.docker.internal:43110")
        resolver({"other.internal": "172.17.0.2"})
        with pytest.raises(BlockedURLError):
            validate_outbound_url("http://other.internal/")


class TestRedirectGuarding:
    def test_epg_fetch_blocks_redirect_to_metadata(self, resolver, monkeypatch):
        """A public EPG source 302ing to the metadata endpoint must be
        stopped at the hop, not transparently followed."""
        from types import SimpleNamespace

        from app.services import epg_service as epg_module

        monkeypatch.setenv("ALLOW_PRIVATE_SCRAPE_TARGETS", "true")
        resolver({
            "public.example.com": "93.184.216.34",
            "169.254.169.254": "169.254.169.254",
        })

        calls = []

        class FakeResponse:
            status_code = 302
            headers = {"Location": "http://169.254.169.254/latest/meta-data/"}
            content = b""
            is_redirect = True
            is_permanent_redirect = False

            def raise_for_status(self):
                pass

        def fake_get(url, timeout=None, allow_redirects=True):
            assert allow_redirects is False
            calls.append(url)
            return FakeResponse()

        monkeypatch.setattr(epg_module.requests, "get", fake_get)

        service = epg_module.EPGService(db=None)
        source = SimpleNamespace(id=1, url="http://public.example.com/epg.xml")
        result = service._fetch_epg_from_source(source)

        assert result["success"] is False
        assert "metadata" in result["error"]
        # The metadata URL itself was never fetched
        assert calls == ["http://public.example.com/epg.xml"]
