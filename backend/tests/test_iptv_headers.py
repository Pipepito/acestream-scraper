"""Headers a playlist publishes for an IPTV stream reach the player.

Some CDNs answer 403 without a Referer or a User-Agent. On a public TDT list
30 of 576 entries publish `#EXTVLCOPT:http-referrer`, and their domains were
exactly the ones answering 403: the "blocked" channels were only missing the
header the list itself was publishing.

Kodi reads `url|Name=value&...` and sends those headers to the playlist and
to every segment. Values must be percent-encoded: unescaped, Kodi cuts each
at its first space and a 120-character User-Agent arrives as `Mozilla/5.0`.
"""
import uuid

from app.models.models import AcestreamChannel
from app.services.m3u_service import M3UService
from app.services.playlist_service import PlaylistService

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/135.0.0.0 Safari/537.36"
REF = "https://player.instantvideocloud.net/"
URL = "https://liveingesta318.cdnmedia.tv/101weblive/antequera/playlist.m3u8"

PLAYLIST = f"""#EXTM3U
#EXTINF:-1 tvg-id="101TV.Antequera" group-title="Andalucía",101TV Antequera
#EXTVLCOPT:http-referrer={REF}
#EXTVLCOPT:http-user-agent={UA}
{URL}
#EXTINF:-1,Sin cabeceras
https://cdn.example.com/otro.m3u8
#EXTINF:-1,Un acestream
#EXTVLCOPT:http-referrer=https://no.importa/
acestream://{'1' * 40}
"""


def _read():
    return {c[1]: c[2] for c in M3UService().extract_channels_from_content(PLAYLIST)}


def test_headers_are_read_from_their_own_entry():
    m = _read()["101TV Antequera"]
    assert m.get("stream_headers") == {"Referer": REF, "User-Agent": UA}, m


def test_headers_do_not_carry_over_to_next_entry():
    """Each #EXTINF starts from scratch: one entry's headers are not the next one's."""
    m = _read()
    # Without this it would also pass if NO header were read at all.
    assert m["101TV Antequera"].get("stream_headers"), m
    assert "stream_headers" not in m["Sin cabeceras"]


def test_acestream_entry_gets_no_headers():
    """It goes through the engine, not HTTP: headers mean nothing there."""
    m = _read()
    assert m["101TV Antequera"].get("stream_headers"), m
    assert "stream_headers" not in m["Un acestream"]


def test_headers_are_emitted_escaped_and_in_order():
    link = PlaylistService._stream_link(
        "acestream://", "url:x", stream_url=URL,
        stream_headers={"Referer": REF, "User-Agent": UA})
    url, _, pipe = link.partition("|")
    assert url == URL
    assert pipe.startswith("User-Agent=Mozilla%2F5.0%20%28"), pipe
    assert "&Referer=https%3A%2F%2Fplayer.instantvideocloud.net%2F" in pipe, pipe


def test_no_space_reaches_kodi():
    """Kodi cuts a header value at its first unescaped space."""
    link = PlaylistService._stream_link(
        "x", "url:x", stream_url=URL, stream_headers={"User-Agent": UA})
    assert "|User-Agent=" in link, link      # that it really carries them
    assert " " not in link, link


def test_headers_are_appended_when_url_already_has_pipe():
    link = PlaylistService._stream_link(
        "x", "url:x", stream_url=URL + "|Origin=https%3A%2F%2Fa",
        stream_headers={"Referer": REF})
    assert link.count("|") == 1, link
    assert link.endswith("&Referer=https%3A%2F%2Fplayer.instantvideocloud.net%2F"), link


def test_without_headers_url_is_emitted_unchanged():
    """Guard: what already worked stays the same."""
    assert PlaylistService._stream_link("x", "url:x", stream_url=URL) == URL


def test_playlist_publishes_headers(client, db_session):
    db_session.add(AcestreamChannel(
        id="url:" + "b" * 40, name="101TV Antequera", is_active=True,
        is_online=True, source_url="http://l/" + uuid.uuid4().hex,
        stream_url=URL, stream_headers={"Referer": REF}))
    db_session.commit()
    r = client.get("/playlist.m3u", params={"only_online": "false"})
    assert r.status_code == 200, r.text
    # Through our manifest route (see test_hls_manifest), still carrying the
    # header: the segments go straight to the CDN and need it.
    assert ("/live/url%3A" + "b" * 40 + "|Referer=https%3A%2F%2Fplayer.instantvideocloud.net%2F") in r.text, r.text


# A stream without headers stored the JSON text 'null', which SQL counts as
# NOT NULL: on a test database `stream_headers IS NOT NULL` said 576
# of 576 IPTV streams had headers when 36 did.

def test_missing_headers_are_stored_as_real_null(db_session):
    from sqlalchemy import text
    db_session.add(AcestreamChannel(id=f"url:{uuid.uuid4().hex}", name="Sin",
                                    stream_url=URL, stream_headers=None))
    db_session.commit()
    assert db_session.execute(text(
        "SELECT count(*) FROM acestream_channels WHERE stream_headers IS NOT NULL"
    )).scalar_one() == 0


# The default playlist (only_online=true) had no HTTP channel until it was
# checked: measured, 0 entries with only_online=true against 592 without it.

def test_default_playlist_includes_unchecked_http_streams(client, db_session):
    ace_unknown = "a" * 40
    db_session.add_all([
        AcestreamChannel(id="url:" + "c" * 40, name="HTTP sin comprobar", is_active=True,
                         is_online=None, stream_url="https://cdn.example.com/x.m3u8"),
        AcestreamChannel(id="url:" + "d" * 40, name="HTTP caida", is_active=True,
                         is_online=False, stream_url="https://cdn.example.com/y.m3u8"),
        AcestreamChannel(id=ace_unknown, name="Ace sin comprobar", is_active=True, is_online=None),
        AcestreamChannel(id="e" * 40, name="Ace viva", is_active=True, is_online=True),
    ])
    db_session.commit()
    body = client.get("/playlist.m3u").text  # only_online defaults to true
    assert "HTTP sin comprobar" in body
    assert "Ace viva" in body
    # What only_online meant still holds for everything that WAS checked,
    # and for acestream ids, which wait on the engine.
    assert "HTTP caida" not in body
    assert "Ace sin comprobar" not in body
