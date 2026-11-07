"""IPTV streams are emitted with their own URL, not base_url + id.

Every base URL pattern assumes an engine that resolves an acestream id. A
stream stored with `stream_url` (see test_iptv_streams.py) has an opaque
`url:<sha1>` id; rendered through the pattern it became
`http://host:6878/ace/getstream?id=url:<sha1>`, which no engine can play.
"""

import uuid

from app.models.models import AcestreamChannel
from app.services.playlist_service import PlaylistService

ACE = "1" * 40
IPTV_URL = "https://cdn.example.com/la1/master.m3u8"
IPTV_ID = "url:" + "a" * 40


class TestStreamLink:
    def test_own_url_wins_over_prefix(self):
        link = PlaylistService._stream_link(
            "http://h:6878/ace/getstream?id=", IPTV_ID, stream_url=IPTV_URL)
        assert link == IPTV_URL

    def test_own_url_wins_over_template_without_pid(self):
        """A pid appended to a CDN URL means nothing and can break
        it."""
        link = PlaylistService._stream_link(
            "http://h/ace/getstream?id={channel_id}&pid={pid}", IPTV_ID,
            pid=7, stream_url=IPTV_URL)
        assert link == IPTV_URL

    def test_own_url_wins_over_tv_channel_relay(self):
        link = PlaylistService._stream_link(
            "http://relay/tv/{tv_channel_id}", IPTV_ID, tv_channel_id=3,
            stream_url=IPTV_URL)
        assert link == IPTV_URL

    def test_without_own_url_nothing_changes(self):
        """Guard: acestream links do not change. Passes with and without the fix."""
        assert PlaylistService._stream_link(
            "http://h:6878/ace/getstream?id=", ACE) == \
            "http://h:6878/ace/getstream?id=" + ACE


def _channel(db_session, cid, name, stream_url=None, tv_channel_id=None):
    c = AcestreamChannel(
        id=cid, name=name, is_active=True, is_online=True,
        source_url="http://lista.example/" + uuid.uuid4().hex,
        stream_url=stream_url, tv_channel_id=tv_channel_id)
    db_session.add(c)
    db_session.commit()
    return c


class TestPlaylistOutput:
    def test_playlist_publishes_iptv_url_and_acestream_id(
            self, client, db_session):
        _channel(db_session, ACE, "Canal acestream")
        _channel(db_session, IPTV_ID, "La 1", stream_url=IPTV_URL)
        base = "http://h:6878/ace/getstream?id="
        r = client.get("/playlist.m3u", params={
            "base_url": base, "only_online": "false"})
        assert r.status_code == 200, r.text
        lines = [l for l in r.text.splitlines() if l and not l.startswith("#")]
        assert IPTV_URL in lines, lines
        assert base + ACE in lines, lines
        assert not any("url:" in l for l in lines), lines

    def test_tv_channels_playlist_too(
            self, client, db_session, seed_tv_channels):
        tv = seed_tv_channels[0]
        _channel(db_session, IPTV_ID, "La 1", stream_url=IPTV_URL,
                 tv_channel_id=tv.id)
        r = client.get("/api/v1/playlists/tv-channels/m3u")
        assert r.status_code == 200, r.text
        assert IPTV_URL in r.text, r.text
        assert "url:" not in r.text, r.text
