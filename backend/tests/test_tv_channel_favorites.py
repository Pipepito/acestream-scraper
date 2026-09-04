"""
Tests for TV channel favorites (list filter + toggle) and unassigned
acestream matching/filtering.
"""

import uuid

from fastapi import status


class TestTVChannelFavorites:
    """Favorites filter and toggle endpoints."""

    def test_list_favorites_filter(self, client, seed_tv_channels, db_session):
        seed_tv_channels[0].is_favorite = True
        db_session.commit()

        response = client.get("/api/v1/tv-channels/?favorites=true")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == seed_tv_channels[0].id

    def test_list_search_filter(self, client, seed_tv_channels):
        needle = seed_tv_channels[1].name
        response = client.get(f"/api/v1/tv-channels/?search={needle}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == needle

    def test_favorite_toggle(self, client, seed_tv_channels):
        tv_id = seed_tv_channels[0].id
        response = client.post(f"/api/v1/tv-channels/{tv_id}/favorite")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["is_favorite"] is True

        response = client.post(f"/api/v1/tv-channels/{tv_id}/favorite")
        assert response.json()["is_favorite"] is False

    def test_favorite_explicit_value(self, client, seed_tv_channels):
        tv_id = seed_tv_channels[0].id
        response = client.post(f"/api/v1/tv-channels/{tv_id}/favorite?value=true")
        assert response.json()["is_favorite"] is True
        # Setting the same value again is idempotent
        response = client.post(f"/api/v1/tv-channels/{tv_id}/favorite?value=true")
        assert response.json()["is_favorite"] is True

    def test_favorite_unknown_channel(self, client):
        response = client.post("/api/v1/tv-channels/999999/favorite")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAcestreamMatches:
    """Unassigned acestream suggestions for the assign flow."""

    def _make_stream(self, db_session, name, tvg_id=None, tv_channel_id=None):
        from app.models.models import AcestreamChannel

        channel = AcestreamChannel(
            id=str(uuid.uuid4()),
            name=name,
            tvg_id=tvg_id,
            source_url=f"acestream://{uuid.uuid4().hex}",
            is_active=True,
            is_online=True,
            tv_channel_id=tv_channel_id,
        )
        db_session.add(channel)
        db_session.commit()
        return channel

    def test_matches_by_name_and_epg_id(self, client, seed_tv_channels, db_session):
        tv = seed_tv_channels[0]
        by_name = self._make_stream(db_session, tv.name)
        by_epg = self._make_stream(db_session, "Different Name", tvg_id=tv.epg_id)
        self._make_stream(db_session, "Unrelated Stream")

        response = client.get(f"/api/v1/tv-channels/{tv.id}/acestream-matches")
        assert response.status_code == status.HTTP_200_OK
        ids = {item["id"] for item in response.json()}
        assert ids == {by_name.id, by_epg.id}

    def test_matches_exclude_assigned_streams(self, client, seed_tv_channels, db_session):
        tv = seed_tv_channels[0]
        other = seed_tv_channels[1]
        self._make_stream(db_session, tv.name, tv_channel_id=other.id)

        response = client.get(f"/api/v1/tv-channels/{tv.id}/acestream-matches")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_matches_unknown_channel(self, client):
        response = client.get("/api/v1/tv-channels/999999/acestream-matches")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUnassignedChannelFilter:
    """assigned=false filter on the channels list."""

    def test_assigned_filter(self, client, seed_channels, seed_tv_channels, db_session):
        seed_channels[0].tv_channel_id = seed_tv_channels[0].id
        db_session.commit()

        response = client.get("/api/v1/channels/?assigned=false")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        names = {item["name"] for item in data["items"]}
        assert seed_channels[0].name not in names
        assert {seed_channels[1].name, seed_channels[2].name} <= names

        response = client.get("/api/v1/channels/?assigned=true")
        data = response.json()
        names = {item["name"] for item in data["items"]}
        assert names == {seed_channels[0].name}
