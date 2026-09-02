"""
Tests for the IPFS URL type and scraper: ipfs://ipns:// sources are fetched
through the configured IPFS HTTP gateway, mirroring the ZeroNet integration.
"""
import asyncio

import pytest

from app.models.url_types import IpfsURL, create_url_object
from app.scrapers import create_scraper_for_url
from app.scrapers.ipfs import IpfsScraper


CID = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"

M3U_CONTENT = """#EXTM3U
#EXTINF:-1 group-title="Sports" tvg-logo="http://logo/1.png",Sports One
acestream://aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
#EXTINF:-1,News Two
acestream://bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
"""


class TestIpfsURLType:
    def test_auto_detects_ipfs_scheme(self):
        url_obj = create_url_object(f"ipfs://{CID}/list.m3u")
        assert isinstance(url_obj, IpfsURL)
        assert url_obj.type_name == "ipfs"

    def test_auto_detects_ipns_scheme(self):
        url_obj = create_url_object("ipns://channels.example.org/list.m3u")
        assert isinstance(url_obj, IpfsURL)

    def test_native_urls_are_already_normalized(self):
        url_obj = IpfsURL(f"ipfs://{CID}/list.m3u")
        assert url_obj.get_normalized_url() == f"ipfs://{CID}/list.m3u"

    def test_gateway_url_normalizes_to_native_scheme(self):
        url_obj = IpfsURL(f"https://ipfs.io/ipfs/{CID}/list.m3u")
        assert url_obj.get_normalized_url() == f"ipfs://{CID}/list.m3u"

    def test_gateway_ipns_url_normalizes_to_native_scheme(self):
        url_obj = IpfsURL("http://127.0.0.1:8081/ipns/channels.example.org/list.m3u")
        assert url_obj.get_normalized_url() == "ipns://channels.example.org/list.m3u"

    def test_internal_url_targets_configured_gateway(self):
        url_obj = IpfsURL(f"ipfs://{CID}/list.m3u")
        internal = url_obj.get_internal_url("http://127.0.0.1:8081")
        assert internal == f"http://127.0.0.1:8081/ipfs/{CID}/list.m3u"

    def test_internal_url_normalizes_foreign_gateway_through_local_one(self):
        url_obj = IpfsURL(f"https://ipfs.io/ipfs/{CID}/list.m3u")
        internal = url_obj.get_internal_url("http://127.0.0.1:8081/")
        assert internal == f"http://127.0.0.1:8081/ipfs/{CID}/list.m3u"

    def test_to_gateway_url_passes_plain_http_through(self):
        assert IpfsURL.to_gateway_url("http://example.com/list.m3u", "http://127.0.0.1:8081") == "http://example.com/list.m3u"

    def test_plain_http_url_is_not_a_valid_ipfs_url(self):
        assert not IpfsURL.is_valid_url("https://example.com/list.m3u")
        with pytest.raises(ValueError):
            IpfsURL("https://example.com/list.m3u")

    def test_empty_cid_is_invalid(self):
        assert not IpfsURL.is_valid_url("ipfs://")

    def test_explicit_ipfs_type_keeps_user_url_for_manual_overrides(self):
        url_obj = create_url_object("https://example.com/custom", url_type="ipfs")
        assert isinstance(url_obj, IpfsURL)
        assert url_obj.get_normalized_url() == "https://example.com/custom"


class TestIpfsScraperFactory:
    def test_auto_detected_ipfs_url_gets_ipfs_scraper(self):
        scraper = create_scraper_for_url(f"ipfs://{CID}/list.m3u", "auto")
        assert isinstance(scraper, IpfsScraper)
        assert scraper.timeout == 30
        assert scraper.retries == 3

    def test_explicit_ipfs_type_gets_ipfs_scraper(self):
        scraper = create_scraper_for_url("https://example.com/anything", "ipfs")
        assert isinstance(scraper, IpfsScraper)

    def test_regular_urls_are_unaffected(self):
        scraper = create_scraper_for_url("https://example.com/list.m3u", "auto")
        assert not isinstance(scraper, IpfsScraper)


class TestIpfsScraper:
    def _scraper(self, url: str, url_type: str = "auto") -> IpfsScraper:
        return create_scraper_for_url(url, url_type)

    def test_resolve_fetch_url_maps_native_scheme_onto_gateway(self):
        scraper = self._scraper(f"ipfs://{CID}/list.m3u")
        scraper.gateway_url = "http://127.0.0.1:8081"
        assert scraper.resolve_fetch_url(f"ipfs://{CID}/list.m3u") == f"http://127.0.0.1:8081/ipfs/{CID}/list.m3u"
        assert scraper.resolve_fetch_url("http://example.com/sub.m3u") == "http://example.com/sub.m3u"

    def test_scrape_detects_m3u_content_without_extension(self, db_session, monkeypatch):
        # A bare CID has no .m3u suffix: playlist detection must sniff the
        # fetched content instead of relying on the URL.
        scraper = self._scraper(f"ipfs://{CID}")
        scraper.db = db_session

        async def fake_fetch(url):
            return M3U_CONTENT

        monkeypatch.setattr(scraper, "fetch_content", fake_fetch)
        channels, status = asyncio.run(scraper.scrape())

        assert status == "OK"
        ids = {channel_id for channel_id, _name, _meta in channels}
        assert ids == {
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        }
        by_id = {channel_id: (name, meta) for channel_id, name, meta in channels}
        assert by_id["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"][0] == "Sports One"

    def test_scrape_extracts_acestream_links_from_html(self, db_session, monkeypatch):
        scraper = self._scraper(f"ipfs://{CID}/index.html")
        scraper.db = db_session

        html = """
        <html><body><script>
        const linksData = {"links": [
            {"name": "HTML Channel", "url": "acestream://cccccccccccccccccccccccccccccccccccccccc"}
        ]};
        </script></body></html>
        """

        async def fake_fetch(url):
            return html

        monkeypatch.setattr(scraper, "fetch_content", fake_fetch)
        channels, status = asyncio.run(scraper.scrape())

        assert status == "OK"
        assert channels == [("cccccccccccccccccccccccccccccccccccccccc", "HTML Channel", {})]

    def test_relative_m3u_links_resolve_through_the_gateway(self, db_session, monkeypatch):
        """A page under ipns://<name>/ linking href="list.m3u" must fetch
        http://<gateway>/ipns/<name>/list.m3u, not a scheme-less "list.m3u"."""
        scraper = self._scraper("ipns://k51example/")
        scraper.db = db_session
        scraper.gateway_url = "http://gateway.test:8080"
        fetched = []

        async def fake_fetch(url):
            fetched.append(url)
            if url.endswith("/list.m3u"):
                return M3U_CONTENT
            return '<html><body><a href="list.m3u">playlist</a></body></html>'

        monkeypatch.setattr(scraper, "fetch_content", fake_fetch)
        channels, status = asyncio.run(scraper.scrape())

        assert status == "OK"
        assert "http://gateway.test:8080/ipns/k51example/list.m3u" in fetched
        assert {channel_id for channel_id, _name, _meta in channels} == {
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        }

    def test_scrape_records_error_status_when_gateway_fetch_fails(self, db_session, monkeypatch):
        scraper = self._scraper(f"ipfs://{CID}")
        scraper.db = db_session

        async def fake_fetch(url):
            raise Exception("gateway unreachable")

        monkeypatch.setattr(scraper, "fetch_content", fake_fetch)
        channels, status = asyncio.run(scraper.scrape())

        assert channels == []
        assert status.startswith("Error:")
        assert "gateway unreachable" in status
