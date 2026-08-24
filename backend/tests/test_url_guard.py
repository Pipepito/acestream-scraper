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
