"""
Tests for the curated playlists: TV-channels and all-streams.
"""

import uuid
import pytest

from fastapi import status


@pytest.mark.parametrize('link', [
    'https://player.test/live.m3u8?next=/tuner/channel/1.ts',
    'https://player.test/tuner/stream/channel.m3u8',
    'acestream://channel?label=/tuner/stream/channel.ts',
])
def test_custom_formats_do_not_get_a_false_mpeg_ts_hint(link):
    from app.services.playlist_service import PlaylistService

    # _link_lines also marks /live/ links, so it needs the service's
    # live_base_url: an instance without one.
    service = PlaylistService.__new__(PlaylistService)
    service.live_base_url = None
    assert service._link_lines(link) == [link]


def test_per_source_respects_stream_filters_and_proxy_prefix(client, seed_tv_channels, db_session):
    tv = seed_tv_channels[0]
    included = _make_stream(db_session, 'Included', tv_channel_id=tv.id, group='Sports')
    offline = _make_stream(db_session, 'Offline', tv_channel_id=tv.id, group='Sports', is_online=False)
    excluded = _make_stream(db_session, 'Excluded', tv_channel_id=tv.id, group='News')
    response = client.get('/api/v1/playlists/m3u', params={
        'base_url': 'https://scraper.test/prefix/tuner/channel/{tv_channel_id}.ts?token=example',
        'per_source': 'true', 'only_online': 'true', 'include_groups': 'Sports',
    })
    assert response.status_code == 200
    assert f'https://scraper.test/prefix/tuner/channel/{tv.id}.ts?token=example' in response.text
    assert f'https://scraper.test/prefix/tuner/stream/{included.id}.ts?token=example' in response.text
    assert offline.id not in response.text
    assert excluded.id not in response.text


def _make_stream(db_session, name, tv_channel_id=None, is_online=True,
                 logo=None, tvg_id=None, tvg_name=None, group=None):
    from app.models.models import AcestreamChannel

    channel = AcestreamChannel(
        id=str(uuid.uuid4()),
        name=name,
        group=group,
        logo=logo,
        tvg_id=tvg_id,
        tvg_name=tvg_name,
        source_url=f"acestream://{uuid.uuid4().hex}",
        is_active=True,
        is_online=is_online,
        tv_channel_id=tv_channel_id,
    )
    db_session.add(channel)
    db_session.commit()
    return channel


class TestTVChannelsPlaylist:
    """Tests for /api/v1/playlists/tv-channels/m3u."""

    def test_empty_when_no_assignments(self, client, seed_tv_channels):
        """TV channels without assigned streams are skipped entirely."""
        response = client.get("/api/v1/playlists/tv-channels/m3u")
        assert response.status_code == status.HTTP_200_OK
        assert response.text.strip().startswith("#EXTM3U")
        assert "\n" not in response.text.strip(), "header only, no entries"

    def test_one_entry_per_assigned_stream(self, client, seed_tv_channels, db_session):
        tv = seed_tv_channels[0]
        _make_stream(db_session, "Solo Stream", tv_channel_id=tv.id)
        response = client.get("/api/v1/playlists/tv-channels/m3u")
        assert response.status_code == status.HTTP_200_OK
        lines = response.text.strip().split("\n")
        extinf = [l for l in lines if l.startswith("#EXTINF:")]
        assert len(extinf) == 1
        # Single stream: plain name, plain channel number, un-suffixed EPG id
        assert f",{tv.name}" in extinf[0]
        assert f'tvg-chno="{tv.channel_number}"' in extinf[0]
        assert f'tvg-id="{tv.epg_id}"' in extinf[0]

    def test_multi_stream_disambiguation(self, client, seed_tv_channels, db_session):
        """Multiple streams get '(n)' names and dotted tvg-chno, but keep the
        channel's own EPG id so players still match the EPG XML (#125)."""
        tv = seed_tv_channels[0]
        # Lower-quality stream (offline) should sort second
        _make_stream(db_session, "Feed B", tv_channel_id=tv.id, is_online=False)
        best = _make_stream(db_session, "Feed A", tv_channel_id=tv.id,
                            is_online=True, logo="http://logo", tvg_id="x")

        response = client.get("/api/v1/playlists/tv-channels/m3u")
        lines = response.text.strip().split("\n")
        extinf = [l for l in lines if l.startswith("#EXTINF:")]
        links = [l for l in lines if not l.startswith("#")]
        assert len(extinf) == 2

        # Quality-ranked: the online/metadata-rich stream comes first
        assert best.id in links[0]
        assert f",{tv.name} (1)" in extinf[0]
        assert f",{tv.name} (2)" in extinf[1]
        assert f'tvg-chno="{tv.channel_number}.1"' in extinf[0]
        assert f'tvg-chno="{tv.channel_number}.2"' in extinf[1]
        # EPG id stays un-suffixed on every stream
        assert f'tvg-id="{tv.epg_id}"' in extinf[0]
        assert f'tvg-id="{tv.epg_id}"' in extinf[1]

    def test_ordered_by_channel_number(self, client, seed_tv_channels, db_session):
        for tv in seed_tv_channels:
            _make_stream(db_session, f"Stream for {tv.id}", tv_channel_id=tv.id)
        response = client.get("/api/v1/playlists/tv-channels/m3u")
        lines = response.text.strip().split("\n")
        numbers = [l.split('tvg-chno="')[1].split('"')[0]
                   for l in lines if "tvg-chno=" in l]
        assert numbers == sorted(numbers, key=float)

    def test_favorites_only(self, client, seed_tv_channels, db_session):
        for tv in seed_tv_channels:
            _make_stream(db_session, f"Stream for {tv.id}", tv_channel_id=tv.id)
        seed_tv_channels[1].is_favorite = True
        db_session.commit()

        response = client.get("/api/v1/playlists/tv-channels/m3u?favorites_only=true")
        lines = response.text.strip().split("\n")
        extinf = [l for l in lines if l.startswith("#EXTINF:")]
        assert len(extinf) == 1
        assert seed_tv_channels[1].name in extinf[0]

    def test_search_filter(self, client, seed_tv_channels, db_session):
        for tv in seed_tv_channels:
            _make_stream(db_session, f"Stream for {tv.id}", tv_channel_id=tv.id)
        needle = seed_tv_channels[2].name

        response = client.get(f"/api/v1/playlists/tv-channels/m3u?search={needle}")
        lines = response.text.strip().split("\n")
        extinf = [l for l in lines if l.startswith("#EXTINF:")]
        assert len(extinf) == 1
        assert needle in extinf[0]

    def test_legacy_alias_matches(self, client, seed_tv_channels, db_session):
        _make_stream(db_session, "Solo", tv_channel_id=seed_tv_channels[0].id)
        legacy = client.get("/api/playlists/tv-channels/m3u")
        canonical = client.get("/api/v1/playlists/tv-channels/m3u")
        assert legacy.status_code == status.HTTP_200_OK
        assert legacy.text == canonical.text


class TestAllStreamsPlaylist:
    """Tests for /api/v1/playlists/all-streams/m3u."""

    def test_tv_channels_first_then_unassigned(self, client, seed_tv_channels, db_session):
        assigned = _make_stream(db_session, "Assigned Stream",
                                tv_channel_id=seed_tv_channels[0].id)
        unassigned = _make_stream(db_session, "Loose Stream")

        response = client.get("/api/v1/playlists/all-streams/m3u")
        assert response.status_code == status.HTTP_200_OK
        text = response.text
        assert text.index(assigned.id) < text.index(unassigned.id)

    def test_unassigned_numbering_starts_at_9000(self, client, seed_tv_channels, db_session):
        _make_stream(db_session, "First Loose")
        _make_stream(db_session, "Second Loose")

        response = client.get("/api/v1/playlists/all-streams/m3u")
        lines = response.text.strip().split("\n")
        numbers = [l.split('tvg-chno="')[1].split('"')[0]
                   for l in lines if "tvg-chno=" in l]
        assert "9000" in numbers
        assert "9001" in numbers

    def test_unassigned_fallback_group(self, client, db_session):
        _make_stream(db_session, "No Group Stream", group=None)
        response = client.get("/api/v1/playlists/all-streams/m3u")
        assert 'group-title="Unassigned Streams"' in response.text

    def test_include_unassigned_false(self, client, seed_tv_channels, db_session):
        assigned = _make_stream(db_session, "Assigned", tv_channel_id=seed_tv_channels[0].id)
        loose = _make_stream(db_session, "Loose Stream")

        response = client.get("/api/v1/playlists/all-streams/m3u?include_unassigned=false")
        assert loose.id not in response.text
        assert assigned.id in response.text

    def test_legacy_alias_matches(self, client, seed_tv_channels, db_session):
        _make_stream(db_session, "Loose Stream")
        legacy = client.get("/api/playlists/all-streams/m3u")
        canonical = client.get("/api/v1/playlists/all-streams/m3u")
        assert legacy.status_code == status.HTTP_200_OK
        assert legacy.text == canonical.text

    def test_legacy_api_m3u_alias_matches_public(self, client, seed_channels):
        legacy = client.get("/api/playlists/m3u")
        public = client.get("/playlists/m3u")
        assert legacy.status_code == status.HTTP_200_OK
        assert legacy.text == public.text


class TestDisplayNameCollisions:
    """Regression tests: display names must be unique across suffix sources."""

    def test_multi_stream_and_dedup_suffixes_never_collide(self, client, db_session):
        """A multi-stream channel 'DAZN' plus two unassigned 'DAZN' streams
        must not produce two entries both named 'DAZN (2)'."""
        from app.models.models import TVChannel

        tv = TVChannel(name="DAZN", channel_number=5, is_active=True)
        db_session.add(tv)
        db_session.commit()
        _make_stream(db_session, "Feed A", tv_channel_id=tv.id)
        _make_stream(db_session, "Feed B", tv_channel_id=tv.id)
        _make_stream(db_session, "DAZN")
        _make_stream(db_session, "DAZN")

        response = client.get("/api/v1/playlists/all-streams/m3u")
        names = [l.split('tvg-name="')[1].split('"')[0]
                 for l in response.text.split("\n") if "tvg-name=" in l]
        assert len(names) == 4
        assert len(set(names)) == 4, f"duplicate display names: {names}"

    def test_attribute_values_are_quote_safe(self, client, db_session):
        """Quotes in scraped names/groups must not break EXTINF attributes."""
        _make_stream(db_session, 'Canal 24" Ultra', group='The "Best" Group')

        response = client.get("/api/v1/playlists/all-streams/m3u")
        extinf = [l for l in response.text.split("\n") if l.startswith("#EXTINF:")]
        assert len(extinf) == 1
        attrs_part = extinf[0].split(",", 1)[0]
        # Attribute values must contain no embedded double quotes: the
        # quote count is exactly 2 per attribute.
        assert attrs_part.count('"') == 2 * attrs_part.count('="')
        assert "Canal 24' Ultra" in extinf[0]


@pytest.mark.parametrize('path', ['/api/v1/playlists/m3u', '/api/v1/playlists/tv-channels/m3u', '/api/v1/playlists/all-streams/m3u'])
def test_tv_id_template_emits_one_stable_entry_and_excludes_unassigned(client, seed_tv_channels, db_session, path):
    tv = seed_tv_channels[0]
    first = _make_stream(db_session, 'A', tv_channel_id=tv.id, is_online=True)
    _make_stream(db_session, 'B', tv_channel_id=tv.id, is_online=True)
    _make_stream(db_session, 'Unassigned', is_online=True)
    pattern = 'http://scraper.test/tuner/channel/{tv_channel_id}.ts'
    response = client.get(path, params={'base_url': pattern, 'only_online': 'false', 'include_unassigned': 'false'})
    assert response.status_code == 200
    links = [line for line in response.text.splitlines() if line and not line.startswith('#')]
    assert links == [f'http://scraper.test/tuner/channel/{tv.id}.ts']
    assert first.id not in response.text
    assert f'tvg-chno="{tv.channel_number}"' in response.text
    assert f'tvg-id="{tv.epg_id}"' in response.text


def test_tv_relay_search_uses_tv_name_and_keeps_source_filters(client, seed_tv_channels, db_session):
    tv = seed_tv_channels[0]
    _make_stream(db_session, 'Different source name', tv_channel_id=tv.id, is_online=True)
    params = {'base_url': 'http://scraper/tuner/channel/{tv_channel_id}.ts', 'search': tv.name}
    response = client.get('/api/v1/playlists/m3u', params=params)
    assert f'/tuner/channel/{tv.id}.ts' in response.text
    response = client.get('/api/v1/playlists/m3u', params={**params, 'search': 'not a channel'})
    assert '#EXTINF' not in response.text


@pytest.mark.parametrize('relay', [False, True])
def test_optional_unassigned_streams_are_last_and_filtered(client, seed_tv_channels, db_session, relay):
    tv = seed_tv_channels[0]
    assigned = _make_stream(db_session, 'Z assigned', tv_channel_id=tv.id, is_online=True, group='Keep')
    loose = _make_stream(db_session, 'A loose', is_online=True, group='Keep')
    offline = _make_stream(db_session, 'Offline', is_online=False, group='Keep')
    excluded = _make_stream(db_session, 'Excluded', is_online=True, group='Other')
    params = {'include_unassigned': 'true', 'only_online': 'true', 'group': 'Keep',
              'base_url': 'http://scraper.test/tuner/channel/{tv_channel_id}.ts' if relay else 'acestream://{channel_id}'}
    response = client.get('/api/v1/playlists/m3u', params=params)
    assert response.status_code == 200
    links = [line for line in response.text.splitlines() if line and not line.startswith('#')]
    assert links == ([f'http://scraper.test/tuner/channel/{tv.id}.ts', f'http://scraper.test/tuner/stream/{loose.id}.ts'] if relay else [f'acestream://{assigned.id}', f'acestream://{loose.id}'])
    assert offline.id not in response.text
    assert excluded.id not in response.text
    assert loose.id not in client.get('/api/v1/playlists/m3u', params={**params, 'include_unassigned': 'false'}).text
    assert loose.id not in client.get('/api/v1/playlists/m3u', params={**params, 'favorites_only': 'true'}).text
    searched = client.get('/api/v1/playlists/m3u', params={**params, 'search': 'A loose'})
    assert loose.id in searched.text
    assert assigned.id not in searched.text


def test_all_streams_relay_appends_unassigned(client, seed_tv_channels, db_session):
    tv = seed_tv_channels[0]
    _make_stream(db_session, 'Assigned', tv_channel_id=tv.id)
    loose = _make_stream(db_session, 'Loose')
    response = client.get('/api/v1/playlists/all-streams/m3u', params={'base_url': 'http://scraper.test/tuner/channel/{tv_channel_id}.ts'})
    assert response.status_code == 200
    assert response.text.index(f'/tuner/channel/{tv.id}.ts') < response.text.index(f'/tuner/stream/{loose.id}.ts')
    assert 'tvg-chno="9000"' in response.text


@pytest.mark.parametrize('path', ['/playlists/m3u', '/playlist.m3u', '/api/playlists/m3u', '/api/v1/playlists/playlists/m3u'])
def test_unassigned_option_in_compatibility_urls(client, db_session, path):
    loose = _make_stream(db_session, 'Loose', is_online=True)
    for include in ('true', 'false'):
        response = client.get(path, params={'include_unassigned': include})
        assert response.status_code == 200
        assert (loose.id in response.text) == (include == 'true')


@pytest.mark.parametrize('path', ['/api/v1/playlists/m3u', '/api/v1/playlists/tv-channels/m3u', '/api/v1/playlists/all-streams/m3u'])
def test_relay_links_tell_kodi_they_are_mpeg_ts(client, seed_tv_channels, db_session, path):
    """Without the line Kodi probes the type in its interface thread: through
    the relay a dead acestream left the remote unresponsive for 13 s, 0 s with
    it. A user's own link format may be anything, so it is left alone."""
    tv = seed_tv_channels[0]
    _make_stream(db_session, 'A', tv_channel_id=tv.id, is_online=True)
    _make_stream(db_session, 'Loose', is_online=True)
    relay = client.get(path, params={'base_url': 'http://scraper.test/tuner/channel/{tv_channel_id}.ts',
                                     'only_online': 'false', 'include_unassigned': 'true'}).text.splitlines()
    links = [i for i, line in enumerate(relay) if '/tuner/' in line and not line.startswith('#')]
    assert links and all(relay[i - 1] == '#KODIPROP:mimetype=video/mp2t' for i in links)
    own = client.get(path, params={'base_url': 'acestream://{channel_id}', 'only_online': 'false'}).text
    assert '#KODIPROP' not in own


@pytest.mark.parametrize('path', ['/playlists/m3u', '/playlist.m3u', '/api/playlists/m3u', '/api/v1/playlists/m3u', '/api/v1/playlists/playlists/m3u'])
def test_per_source_lists_each_source_under_its_relayed_channel(client, seed_tv_channels, db_session, path):
    """Under each relayed channel, one entry per source, to switch by hand
    when the automatic choice fails: named as the playlist publishes it plus
    the start of the acestream id, numbered N.1, N.2..., with the channel's
    guide and group, opening that source alone through the raw relay."""
    tv, other = seed_tv_channels[0], seed_tv_channels[1]
    first = _make_stream(db_session, 'Channel 1080p --> SOURCE', tv_channel_id=tv.id)
    second = _make_stream(db_session, 'Channel 720p', tv_channel_id=tv.id)
    _make_stream(db_session, 'Other source', tv_channel_id=other.id)
    params = {'base_url': 'http://scraper.test/tuner/channel/{tv_channel_id}.ts', 'only_online': 'false',
              'include_unassigned': 'false', 'per_source': 'true'}
    lines = client.get(path, params=params).text.splitlines()
    links = [line for line in lines if line and not line.startswith('#')]
    start = links.index(f'http://scraper.test/tuner/channel/{tv.id}.ts')
    assert set(links[start + 1:start + 3]) == {f'http://scraper.test/tuner/stream/{first.id}.ts',
                                               f'http://scraper.test/tuner/stream/{second.id}.ts'}
    assert links.count(f'http://scraper.test/tuner/channel/{other.id}.ts') == 1
    at = lines.index(f'http://scraper.test/tuner/stream/{first.id}.ts')
    assert lines[at - 1] == '#KODIPROP:mimetype=video/mp2t'
    extinf = lines[at - 2]
    assert extinf.endswith(f',Channel 1080p --> SOURCE [{first.id[:8]}]')
    assert f'tvg-chno="{tv.channel_number}.' in extinf
    assert f'tvg-id="{tv.epg_id}"' in extinf
    assert f'group-title="{tv.category}"' in extinf
    # Off by default, and meaningless for a format that already lists sources.
    assert first.id not in client.get(path, params={**params, 'per_source': 'false'}).text
    own = client.get(path, params={**params, 'base_url': 'acestream://{channel_id}'}).text
    assert own.count(f'acestream://{first.id}') == 1
