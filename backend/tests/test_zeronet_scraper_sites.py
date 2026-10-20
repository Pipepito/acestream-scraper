"""ZeroNet sources against a node that does not hold the site yet.

Measured on 2026-10-20 against the embedded node (zeronet-conservancy), with
sources added and scraped through the API:

- zero://<site>/<file> saved as type "zeronet" was refused by the outbound
  guard ("URL scheme 'zero' is not allowed"): the zero:// -> node mapping was
  skipped together with validation.
- http://<node>:43110/<site>/<file> for a site the node did not hold got the
  node's "Add new site" form back on every retry and failed after 185 s; the
  node never added the site by itself. /data/zeronet has no volume, so the node
  is empty after every container recreation.
- With the site present, a bare links.json ({"links": [{name, url}]}) gave
  status OK and 0 channels.
"""
import asyncio
import json

import pytest
from aiohttp import web

from app.scrapers import create_scraper_for_url
from app.scrapers import zeronet as zeronet_module
from app.scrapers.zeronet import ZeronetScraper

SITE = "18D6dPcsjLrjg2hhnYqKzNh2W6QtXrDwF"
ID_A = "02b9307c5c97c86914cc5939d6bbeb5b4ec60b47"
ID_B = "61a38b6c3b6c3fdffcb2f61053f3437e569eb666"
LINKS_JSON = json.dumps({"links": [
    {"name": "La1", "url": f"acestream://{ID_A}"},
    {"name": "La1 UHD", "url": f"acestream://{ID_B}"},
]})
ADD_PAGE = ('<html><head><title>Add new site</title></head><body><form action="/add/" method="POST">'
            '<input type="hidden" name="add_nonce" value="abc123">'
            f'<input type="hidden" name="address" value="{SITE}"></form></body></html>')


def _scraper(url, url_type="zeronet"):
    """The scraper builds an aiohttp CookieJar, which needs a running loop."""
    async def build():
        return create_scraper_for_url(url, url_type)
    return asyncio.run(build())


def test_zero_scheme_maps_to_the_node_even_for_type_zeronet():
    scraper = _scraper(f"zero://{SITE}/links.json")
    assert scraper.url_obj.skip_validation is True
    assert scraper.url_obj.get_internal_url("127.0.0.1") == f"http://127.0.0.1:43110/{SITE}/links.json"


def test_http_node_url_saved_as_zeronet_is_left_as_given():
    url = f"http://192.168.1.5:43110/{SITE}/links.json"
    assert _scraper(url).url_obj.get_internal_url("127.0.0.1") == url


def test_channels_from_json_reads_named_acestream_links():
    channels = ZeronetScraper.channels_from_json(LINKS_JSON)
    assert channels == [(ID_A, "La1", {}), (ID_B, "La1 UHD", {})]


@pytest.mark.parametrize("content", ["not json", "{}", '{"links": [{"name": "x", "url": "http://a"}]}'])
def test_channels_from_json_without_links_is_empty(content):
    assert ZeronetScraper.channels_from_json(content) == []


def test_zero_url_is_fetched_from_the_configured_node_not_the_site(monkeypatch):
    requested = []

    class FakeResponse:
        headers = {"Content-Type": "application/json"}

        def raise_for_status(self):
            pass

        async def text(self):
            return LINKS_JSON

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    class FakeSession:
        def get(self, url, **kwargs):
            requested.append(url)
            return FakeResponse()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    recorded = _record_status(monkeypatch)
    monkeypatch.setattr(zeronet_module, "source_session", lambda **kw: FakeSession())
    monkeypatch.setattr(zeronet_module, "validate_outbound_url", lambda url: None)
    url = f"zero://{SITE}/links.json"

    async def run():
        scraper = create_scraper_for_url(url, "zeronet")
        scraper.zeronet_url = "http://127.0.0.1:43110"
        return await scraper.scrape(url)
    channels, status = asyncio.run(run())
    assert requested == [f"http://127.0.0.1:43110/{SITE}/links.json"]
    assert [c[0] for c in channels] == [ID_A, ID_B]
    assert recorded == [(url, "OK")]


def test_node_without_the_site_gets_it_added_and_the_file_read(monkeypatch):
    """A fake node that behaves like the real one: the file gives the Add new
    site form until the site's root page has been requested."""
    state = {"added": False, "requests": []}

    async def root(request):
        state["requests"].append(request.path)
        state["added"] = True
        return web.Response(text="<html>wrapper</html>", content_type="text/html")

    async def links(request):
        state["requests"].append(request.path)
        if not state["added"]:
            return web.Response(text=ADD_PAGE, content_type="text/html")
        return web.Response(text=LINKS_JSON, content_type="application/json")

    async def scenario():
        app = web.Application()
        app.router.add_get(f"/{SITE}/", root)
        app.router.add_get(f"/{SITE}/links.json", links)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        node = f"http://127.0.0.1:{port}"
        monkeypatch.setenv("ZERONET_URL", node)  # the guard exempts the node's host
        url = f"{node}/{SITE}/links.json"
        scraper = create_scraper_for_url(url, "zeronet")
        scraper.retries = 3
        try:
            return await scraper.scrape(url)
        finally:
            await runner.cleanup()

    recorded = _record_status(monkeypatch)
    monkeypatch.setattr(zeronet_module.asyncio, "sleep", _no_sleep)
    channels, status = asyncio.run(scenario())
    assert [s for _, s in recorded] == ["OK"]
    assert [c[0] for c in channels] == [ID_A, ID_B]
    assert state["requests"] == [f"/{SITE}/links.json", f"/{SITE}/", f"/{SITE}/links.json"]


_real_sleep = asyncio.sleep


async def _no_sleep(seconds, *a, **k):
    await _real_sleep(0)


def _record_status(monkeypatch):
    """The JSON and M3U paths return early; they must still record the source's
    status (they used to leave it at "active" with no processing time)."""
    recorded = []

    async def record(self, url, status, error=None):
        recorded.append((url, status))
    monkeypatch.setattr(ZeronetScraper, "update_url_status", record)
    return recorded


def test_m3u_path_records_ok_and_errors(monkeypatch):
    recorded = _record_status(monkeypatch)
    m3u = f"#EXTM3U\n#EXTINF:-1,La1\nacestream://{ID_A}\n"
    url = f"zero://{SITE}/lista.m3u"

    async def run(fail):
        scraper = create_scraper_for_url(url, "zeronet")

        async def fetch(u):
            if fail:
                raise ValueError("node down")
            return m3u
        scraper.fetch_content = fetch
        return await scraper.scrape(url)

    channels, _ = asyncio.run(run(False))
    assert [c[0] for c in channels] == [ID_A]
    channels, status = asyncio.run(run(True))
    assert channels == [] and status == "Error: node down"
    assert recorded == [(url, "OK"), (url, "Error: node down")]
