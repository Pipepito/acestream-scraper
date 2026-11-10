"""
Sources: an M3U channel list is recognised by what was downloaded, not only
by a URL ending in .m3u / .m3u8 (issue #332).
"""
import pytest

from app.services.m3u_service import has_m3u_extension, is_channel_playlist


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
    ("﻿#EXTM3U\n#EXTINF:-1,One\nhttp://example.com/one.m3u8\n", True),
    ("\r\n \t#EXTM3U url-tvg=\"http://example.com/epg.xml\"\n", True),
    ("", False),
    ("﻿ \n", False),
    ("<html><body><pre>#EXTM3U\n#EXTINF:-1,One</pre></body></html>", False),
    # Header-less lists are recognised by their extension only.
    ("#EXTINF:-1,One\nacestream://" + "a" * 40 + "\n", False),
    # HLS manifests describe one stream: their URIs are variants and segments.
    ("#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=800000\nhttps://cdn.example.com/low/index.m3u8\n", False),
    ("#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6.0,\nhttps://cdn.example.com/seg10.ts\n", False),
])
def test_is_channel_playlist(content, expected):
    assert is_channel_playlist(content) is expected
