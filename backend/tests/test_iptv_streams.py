"""Playlists whose entries are plain URLs, not acestream ids.

Until now `M3UService.extract_channels_from_m3u` dropped, in silence, every
line that did not carry an acestream id. Importing an ordinary IPTV playlist
produced zero channels and reported no error, which is indistinguishable from
an empty playlist.

Measured on a running installation: 592 of 1,599 sources (37%) are plain HTTP, and they
reach 458 of 802 channels -- more than half the grid.
"""

import pytest
from app.services.m3u_service import M3UService


IPTV = """#EXTM3U
#EXTINF:-1 tvg-id="La1.es" group-title="TDT",La 1
https://cdn.example.com/la1/master.m3u8
#EXTINF:-1 tvg-id="La2.es" group-title="TDT",La 2
https://cdn.example.com/la2/master.m3u8
"""

MIXED = """#EXTM3U
#EXTINF:-1 group-title="Deportes",Canal de acestream
acestream://1111111111111111111111111111111111111111
#EXTINF:-1 group-title="Deportes",Canal de IPTV
https://cdn.example.com/dep/master.m3u8
"""

JUNK = """#EXTM3U
#EXTINF:-1,Algo que no se puede abrir
rtmp://servidor/directo
#EXTINF:-1,Otra cosa
/ruta/relativa.ts
"""


@pytest.fixture
def service():
    return M3UService()


def extract(service, text):
    """`extract_channels_from_content` parses; `extract_channels_from_m3u`
    DOWNLOADS and then parses. The former is what matters here."""
    return service.extract_channels_from_content(text)


def test_iptv_playlist_no_longer_yields_zero(service):
    """The case behind the change: it used to return [] without a word."""
    channels = extract(service, IPTV)
    assert len(channels) == 2, channels
    assert [c[1] for c in channels] == ['La 1', 'La 2']


def test_url_is_stored_so_it_can_be_served(service):
    channels = extract(service, IPTV)
    urls = [c[2].get('stream_url') for c in channels]
    assert urls == ['https://cdn.example.com/la1/master.m3u8',
                    'https://cdn.example.com/la2/master.m3u8'], urls


def test_id_cannot_be_mistaken_for_acestream(service):
    """Bare 40 hex is a content id or an infohash. This is neither.

    That way, all the code that asks the engine about a 40-hex id keeps
    ignoring these streams without touching a line.
    """
    import re
    channels = extract(service, IPTV)
    # WITHOUT THIS the test passes by looping over an empty list, so it would
    # pass just the same with the old code and prove nothing.
    assert len(channels) == 2, channels
    for cid, _n, _m in channels:
        assert cid.startswith('url:'), cid
        assert not re.fullmatch(r'[a-fA-F0-9]{40}', cid), cid


def test_id_is_stable_across_scrapes(service):
    """If it changed, every scrape would duplicate the row instead of updating it."""
    a = extract(service, IPTV)
    b = extract(service, IPTV)
    # Same as above: two empty lists are equal too.
    assert len(a) == 2, a
    assert [c[0] for c in a] == [c[0] for c in b]


def test_acestream_entries_unchanged(service):
    """The acestream entry of a MIXED playlist still comes in as before, with no URL.

    This is not a regression guard -- it also checks that the IPTV entry
    comes in -- so it fails without the fix. Stated so it is not counted as
    coverage of something it does not cover.
    """
    channels = extract(service, MIXED)
    assert len(channels) == 2, channels
    ace = [c for c in channels if c[0] == '1' * 40]
    assert len(ace) == 1, channels
    assert ace[0][2].get('stream_url') is None, ace


def test_unopenable_lines_are_still_dropped(service):
    """rtmp and relative paths are not channels; letting them through would
    turn junk into catalogue rows."""
    assert extract(service, JUNK) == []


def test_group_and_tvg_id_are_kept(service):
    """They are what later links the channel to its guide."""
    _cid, _n, meta = extract(service, IPTV)[0]
    assert meta.get('tvg_id') == 'La1.es', meta
    assert meta.get('group_title') == 'TDT', meta
