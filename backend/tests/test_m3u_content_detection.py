"""
Sources: an M3U channel list is recognised by what was downloaded, not only
by a URL ending in .m3u / .m3u8 (issue #332).
"""
import asyncio

import pytest

from app.models.url_types import RegularURL, ZeronetURL
from app.scrapers.http import HTTPScraper
from app.scrapers.zeronet import ZeronetScraper
from app.services.m3u_service import (
    has_m3u_extension,
    is_channel_playlist,
    is_m3u_source,
    looks_like_m3u,
)

ID_A = "a" * 40
ID_B = "b" * 40

PLAYLIST = (
    '#EXTM3U\n'
    f'#EXTINF:-1 group-title="Sports",Sports One\nacestream://{ID_A}\n'
    f'#EXTINF:-1,News Two\nacestream://{ID_B}\n'
    '#EXTINF:-1,Web Three\nhttp://example.com/web/index.m3u8\n'
)
# Entries without the #EXTM3U first line.
HEADERLESS = (
    f'#EXTINF:-1,Sports One\nacestream://{ID_A}\n'
    f'#EXTINF:-1,News Two\nacestream://{ID_B}\n'
)
HLS_MASTER = (
    '#EXTM3U\n#EXT-X-VERSION:3\n'
    '#EXT-X-STREAM-INF:BANDWIDTH=800000\n'
    'https://cdn.example.com/live/low/index.m3u8\n'
)


def _scrape(url, content, make_scraper=None, bare_ids=False, scrape_url=None):
    """Scrape `url` with the network stubbed: the source answers `content`
    and anything the scraper follows from it answers 404."""
    fetched = []

    async def fake_fetch(fetch_url):
        fetched.append(fetch_url)
        if len(fetched) > 1:
            raise RuntimeError("404 Not Found")
        return content

    async def noop_update(url, status, error=None):
        return None

    async def run():
        # Some scrapers need a running event loop to be built.
        scraper = make_scraper() if make_scraper else HTTPScraper(RegularURL(url))
        scraper.fetch_content = fake_fetch
        scraper.update_url_status = noop_update
        scraper.scrape_bare_ids = bare_ids
        return await (scraper.scrape(scrape_url) if scrape_url else scraper.scrape())

    channels, status = asyncio.run(run())
    return {channel[0] for channel in channels}, status, fetched


@pytest.mark.parametrize("url, expected", [
    ("http://example.com/lists/sports.m3u", True),
    ("http://example.com/lists/sports.m3u8", True),
    ("http://example.com/lists/SPORTS.M3U?raw=true", True),
    ("http://example.com/lists/sports.m3u?token=abc#top", True),
    ("ipfs://bafyexample/list.m3u", True),
    ("zero://example.bit/lista.m3u8", True),
    ("http://example.com/lists/sports", False),
    ("http://example.com/get?format=m3u", False),
    # The old workaround is a query value, not an extension.
    ("http://example.com/get?f=.m3u", False),
    # Malformed: False, never an exception.
    ("http://[bad/list.m3u", False),
    ("", False),
])
def test_has_m3u_extension(url, expected):
    assert has_m3u_extension(url) is expected


@pytest.mark.parametrize("content, expected", [
    ("#EXTM3U\n#EXTINF:-1,One\nacestream://" + "a" * 40 + "\n", True),
    ("\ufeff#EXTM3U\n#EXTINF:-1,One\nhttp://example.com/one.m3u8\n", True),
    ("\r\n \t#EXTM3U url-tvg=\"http://example.com/epg.xml\"\n", True),
    ("", False),
    ("\ufeff \n", False),
    ("<html><body><pre>#EXTM3U\n#EXTINF:-1,One</pre></body></html>", False),
    # Header-less lists are recognised by their extension only.
    ("#EXTINF:-1,One\nacestream://" + "a" * 40 + "\n", False),
    # HLS manifests describe one stream: their URIs are variants and segments.
    ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=800000\nhttps://cdn.example.com/low/index.m3u8\n", False),
    ("#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6.0,\nhttps://cdn.example.com/seg10.ts\n", False),
    ("#EXTM3U\n#EXT-X-TARGETDURATION:1\n#EXTINF:0.5,\nhttps://cdn.example.com/seg1.ts\n", False),
    # A channel list stays one even with a stray stream tag line: its entries
    # are acestream links or carry the "-1"/"0" duration of a live channel.
    (PLAYLIST + "#EXT-X-TARGETDURATION:6\n", True),
    ("#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:-1,Web\nhttp://example.com/web/index.m3u8\n", True),
    ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1\n#EXTINF:0 tvg-id=\"web\",Web\nhttp://example.com/web/index.m3u8\n", True),
    # Only a tag line makes a manifest, not a channel that mentions one.
    ("#EXTM3U\n#EXTINF:-1,Guide to #EXT-X-STREAM-INF tags\nacestream://" + "a" * 40 + "\n", True),
])
def test_is_channel_playlist(content, expected):
    assert is_channel_playlist(content) is expected


@pytest.mark.parametrize("url, content, expected", [
    # Recognised from what was downloaded.
    ("http://example.com/lists/sports", PLAYLIST, True),
    ("http://example.com/lists/sports.m3u?raw=true", HEADERLESS, True),
    ("http://example.com/lists/sports", HEADERLESS, False),
    # An address the old rule read as a playlist still is, whatever it serves:
    # the "?f=.m3u" workaround keeps working for lists without a header.
    ("http://example.com/lists/sports?f=.m3u", HEADERLESS, True),
    ("http://example.com/lists/sports#.m3u", HEADERLESS, True),
    ("ipfs://bafyexample?filename=list.m3u", HEADERLESS, True),
    ("http://example.com/live/master.m3u8", HLS_MASTER, True),
    # A stream manifest is never newly read as a list.
    ("http://example.com/live/master.m3u8?token=x", HLS_MASTER, False),
    ("http://example.com/live/master", HLS_MASTER, False),
])
def test_is_m3u_source(url, content, expected):
    assert is_m3u_source(url, content) is expected


@pytest.mark.parametrize("url", [
    "http://example.com/lists/sports",
    "http://example.com/lists/sports.m3u?raw=true",
    "http://example.com/get?format=m3u",
    "http://example.com/lists/sports.m3u",
])
def test_playlist_is_read_whatever_the_url_ends_with(url):
    ids, status, fetched = _scrape(url, PLAYLIST)

    assert status == "OK"
    # Both acestream entries, plus the http entry as a url: stream.
    assert len(ids) == 3 and {ID_A, ID_B} <= ids
    # Read as a list, not as a page: the .m3u8 entry inside is not fetched.
    assert fetched == [url]


def test_playlist_with_byte_order_mark_is_detected():
    ids, _status, fetched = _scrape("http://example.com/lists/sports", "\ufeff" + PLAYLIST)

    assert {ID_A, ID_B} <= ids
    assert len(fetched) == 1


def test_html_page_is_still_parsed_as_html():
    page = f'<html><body><a href="acestream://{ID_A}">Sports One</a></body></html>'
    ids, status, _fetched = _scrape("http://example.com/lists/sports", page)

    assert status == "OK"
    assert ids == {ID_A}


@pytest.mark.parametrize("url", [
    "http://example.com/live/master?token=x",
    "http://example.com/live/master.m3u8?token=x",
])
def test_hls_stream_manifest_is_not_newly_read_as_a_list(url):
    # A stream address, not a list: its variants must not become channels.
    ids, status, _fetched = _scrape(url, HLS_MASTER)

    assert status == "OK"
    assert ids == set()


def test_old_workaround_url_still_reads_a_list_without_header():
    ids, status, fetched = _scrape("http://example.com/lists/sports?f=.m3u", HEADERLESS)

    assert status == "OK"
    assert ids == {ID_A, ID_B}
    assert len(fetched) == 1


def test_detected_playlist_without_entries_is_still_read_as_a_page():
    # Raw hashes are not M3U entries; with the bare-ID option the page reader
    # finds them, as it did before the header was recognised.
    body = f"#EXTM3U\n#EXTINF:-1,Sports One\n{ID_A}\n#EXTINF:-1,News Two\n{ID_B}\n"
    ids, status, _fetched = _scrape("http://example.com/lists/sports", body, bare_ids=True)

    assert status == "OK"
    assert ids == {ID_A, ID_B}


def test_m3u_extension_keeps_playlist_parsing_without_header():
    body = f"#EXTINF:-1,Sports One\nacestream://{ID_A}\n"
    ids, _status, fetched = _scrape("http://example.com/lists/sports.m3u", body)

    assert ids == {ID_A}
    assert len(fetched) == 1


def test_zeronet_playlist_without_extension_uses_the_same_rule():
    # ZeroNet only special-cases paths ending in .m3u; anything else falls
    # back to the base scraper, so it gets the content check too.
    url = "zero://example.bit/lists/sports"
    ids, _status, fetched = _scrape(url, PLAYLIST, lambda: ZeronetScraper(ZeronetURL(url)))

    assert {ID_A, ID_B} <= ids
    assert len(fetched) == 1


def test_zeronet_old_workaround_url_still_reads_a_list_without_header():
    url = "zero://example.bit/lists/sports?f=.m3u"
    ids, _status, fetched = _scrape(url, HEADERLESS, lambda: ZeronetScraper(ZeronetURL(url)))

    assert ids == {ID_A, ID_B}
    assert len(fetched) == 1


@pytest.mark.parametrize("content, expected", [
    ("\ufeff#EXTM3U\n#EXTINF:-1,Web\nhttp://example.com/web/index.m3u8\n", True),
    ("#EXTINF:-1,Web\nhttp://example.com/web/index.m3u8\n", True),
    (f"Sports One acestream://{ID_A}\n", True),
    ("<html><body><p>Site is loading</p></body></html>", False),
    ("", False),
])
def test_looks_like_m3u(content, expected):
    assert looks_like_m3u(content) is expected


def test_html_page_quoting_a_playlist_is_still_read_as_a_page():
    # The header counts only at the start of the download. Read as a page,
    # the scraper follows the list it links to; read as a list, it would not.
    page = (
        f'<html><body><pre>#EXTM3U\n#EXTINF:-1,Example\nacestream://{ID_A}\n</pre>'
        '<a href="http://example.com/nested.m3u">the list</a></body></html>'
    )
    url = "http://example.com/docs/playlists"
    _ids, status, fetched = _scrape(url, page)

    assert status == "OK"
    assert fetched == [url, "http://example.com/nested.m3u"]


@pytest.mark.parametrize("valid, malformed, make_scraper", [
    ("http://example.com/lists/sports", "http://[bad/list.m3u", None),
    ("zero://example.bit/lists/sports", "zero://[bad/list.m3u",
     lambda: ZeronetScraper(ZeronetURL("zero://example.bit/lists/sports"))),
])
def test_malformed_url_is_reported_as_an_error_not_raised(valid, malformed, make_scraper):
    ids, status, fetched = _scrape(valid, PLAYLIST, make_scraper, scrape_url=malformed)

    assert ids == set()
    assert status.startswith("Error:")
    assert fetched == []
