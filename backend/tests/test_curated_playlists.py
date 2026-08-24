"""
Tests for the curated playlists: TV-channels and all-streams.
"""

import uuid

from fastapi import status


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
        assert response.text.strip() == "#EXTM3U"

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
