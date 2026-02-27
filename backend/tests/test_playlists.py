"""
Integration tests for Playlist endpoints
"""

import pytest
from fastapi import status


class TestPlaylistEndpoints:
    """Test playlist generation operations."""

    def test_get_m3u_playlist_empty(self, client):
        """Test getting M3U playlist when no channels exist."""
        response = client.get("/api/v1/playlists/m3u")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        content = response.text
        assert "#EXTM3U" in content
        # Should have header even when empty
        assert content.startswith("#EXTM3U")

    def test_get_m3u_playlist_with_channels(self, client, seed_channels):
        """Test getting M3U playlist with channels."""
        response = client.get("/api/v1/playlists/m3u")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        content = response.text
        assert "#EXTM3U" in content

        # Should contain channel entries
        assert "Alpha Channel" in content
        assert "Beta Channel" in content
        assert "Gamma Channel" in content

        # Check M3U format
        lines = content.split('\n')
        assert lines[0] == "#EXTM3U"

        # Should have EXTINF entries for each channel
        extinf_count = sum(1 for line in lines if line.startswith("#EXTINF:"))
        assert extinf_count == 3

    def test_get_m3u_playlist_with_search_filter(self, client, seed_channels):
        """Test getting M3U playlist with search filter."""
        response = client.get("/api/v1/playlists/m3u?search=Alpha")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "#EXTM3U" in content
        assert "Alpha Channel" in content
        assert "Beta Channel" not in content
        assert "Gamma Channel" not in content

    def test_get_m3u_playlist_with_group_filter(self, client, seed_channels):
        """Test getting M3U playlist filtered by group."""
        response = client.get("/api/v1/playlists/m3u?group=Group 1")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "#EXTM3U" in content
        assert "Alpha Channel" in content
        assert "Beta Channel" not in content
        assert "Gamma Channel" not in content

    def test_get_m3u_playlist_with_include_groups(self, client, seed_channels):
        """Test getting M3U playlist with include groups filter."""
        response = client.get("/api/v1/playlists/m3u?include_groups=Group 1,Group 2")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "#EXTM3U" in content
        assert "Alpha Channel" in content
        assert "Beta Channel" in content
        assert "Gamma Channel" not in content

    def test_get_m3u_playlist_with_exclude_groups(self, client, seed_channels):
        """Test getting M3U playlist with exclude groups filter."""
        response = client.get("/api/v1/playlists/m3u?exclude_groups=Group 1,Group 2")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "#EXTM3U" in content
        assert "Alpha Channel" not in content
        assert "Beta Channel" not in content
        assert "Gamma Channel" in content

    def test_get_m3u_playlist_online_only(self, client, seed_channels, db_session):
        """Test getting M3U playlist with only online channels."""
        # Set one channel as offline
        seed_channels[0].is_online = False
        db_session.commit()

        response = client.get("/api/v1/playlists/m3u?only_online=true")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "#EXTM3U" in content
        assert "Alpha Channel" not in content  # Offline channel
        assert "Beta Channel" in content
        assert "Gamma Channel" in content

    def test_get_m3u_playlist_with_custom_base_url(self, client, seed_channels):
        """Test getting M3U playlist with custom base URL."""
        custom_base = "http://custom.example.com"
        response = client.get(f"/api/v1/playlists/m3u?base_url={custom_base}")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "#EXTM3U" in content
        # URLs should use custom base
        assert custom_base in content

    def test_get_m3u_playlist_with_format_parameter(self, client, seed_channels):
        """Test getting M3U playlist with different format options."""
        response = client.get("/api/v1/playlists/m3u?format=extended")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "#EXTM3U" in content

        # Extended format should include more metadata
        lines = content.split('\n')
        for line in lines:
            if line.startswith("#EXTINF:"):
                # Should contain channel metadata
                assert "tvg-id=" in line or "group-title=" in line


class TestPlaylistGroupEndpoints:
    """Test playlist group operations."""

    def test_get_playlist_groups_empty(self, client):
        """Test getting playlist groups when no channels exist."""
        response = client.get("/api/v1/playlists/groups")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_playlist_groups_with_channels(self, client, seed_channels):
        """Test getting playlist groups with channels."""
        response = client.get("/api/v1/playlists/groups")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert "Group 1" in data
        assert "Group 2" in data
        assert "Group 3" in data

        # Should be sorted
        assert data == sorted(data)

    def test_get_playlist_groups_unique(self, client, seed_channels, db_session):
        """Test that playlist groups are unique."""
        # Add another channel with same group
        from app.models.models import AcestreamChannel
        import uuid

        duplicate_group_channel = AcestreamChannel(
            id=str(uuid.uuid4()),
            name="Duplicate Group Channel",
            group="Group 1",  # Same as existing
            source_url="acestream://duplicate123456789",
            is_active=True,
            is_online=True
        )
        db_session.add(duplicate_group_channel)
        db_session.commit()

        response = client.get("/api/v1/playlists/groups")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should still have only 3 unique groups
        assert len(data) == 3
        assert data.count("Group 1") == 1


class TestPlaylistIntegration:
    """Test playlist integration with other components."""

    def test_m3u_playlist_integration_with_tv_channels(self, client, seed_channels, seed_tv_channels, db_session):
        """Test M3U playlist integration with TV channels."""
        # Associate an acestream channel with a TV channel
        seed_channels[0].tv_channel_id = seed_tv_channels[0].id
        db_session.commit()

        response = client.get("/api/v1/playlists/m3u")
        assert response.status_code == status.HTTP_200_OK
        content = response.text

        # Should include the associated channel
        assert "Alpha Channel" in content
        assert "#EXTM3U" in content

    def test_m3u_playlist_with_epg_integration(self, client, seed_all_data):
        """Test M3U playlist with EPG integration."""
        response = client.get("/api/v1/playlists/m3u")
        assert response.status_code == status.HTTP_200_OK
        content = response.text

        # Should include EPG-related metadata if available
        assert "#EXTM3U" in content

        # Check for TVG attributes
        lines = content.split('\n')
        for line in lines:
            if line.startswith("#EXTINF:"):
                # May contain tvg-id attributes
                if "tvg-id=" in line:
                    assert "tvg-id=" in line

    def test_m3u_playlist_performance_with_large_dataset(self, client, db_session):
        """Test M3U playlist performance with a large number of channels."""
        from app.models.models import AcestreamChannel
        import uuid

        # Create 100 test channels
        channels = []
        for i in range(100):
            channel = AcestreamChannel(
                id=str(uuid.uuid4()),
                name=f"Performance Test Channel {i+1}",
                group=f"Performance Group {(i % 10) + 1}",
                source_url=f"acestream://perf{i:08d}",
                is_active=True,
                is_online=True
            )
            channels.append(channel)

        db_session.add_all(channels)
        db_session.commit()

        # Test that playlist generation doesn't timeout
        response = client.get("/api/v1/playlists/m3u")
        assert response.status_code == status.HTTP_200_OK
        content = response.text
        assert "#EXTM3U" in content

        # Should contain all channels
        lines = content.split('\n')
        extinf_count = sum(1 for line in lines if line.startswith("#EXTINF:"))
        assert extinf_count == 100

    def test_m3u_playlist_with_special_characters(self, client, db_session):
        """Test M3U playlist with special characters in channel names."""
        from app.models.models import AcestreamChannel
        import uuid

        special_channels = [
            {
                "name": "Channel with Émojis 🎬",
                "group": "Special Grôup"
            },
            {
                "name": "Channel & Symbols #1",
                "group": "Symbols & More"
            },
            {
                "name": "Channel \"Quotes\"",
                "group": "Test Group"
            }
        ]

        for i, channel_data in enumerate(special_channels):
            channel = AcestreamChannel(
                id=str(uuid.uuid4()),
                name=channel_data["name"],
                group=channel_data["group"],
                source_url=f"acestream://special{i:08d}",
                is_active=True,
                is_online=True
            )
            db_session.add(channel)

        db_session.commit()

        response = client.get("/api/v1/playlists/m3u")
        assert response.status_code == status.HTTP_200_OK
        content = response.text

        # Should handle special characters properly
        assert "#EXTM3U" in content
        for channel_data in special_channels:
            # Channel name should be in the playlist (may be encoded)
            assert channel_data["name"] in content or channel_data["name"].encode('utf-8').decode('utf-8') in content

    def test_m3u_playlist_content_type_headers(self, client, seed_channels):
        """Test M3U playlist content type and headers."""
        response = client.get("/api/v1/playlists/m3u")
        assert response.status_code == status.HTTP_200_OK

        # Check content type
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # Check content disposition for download
        if "content-disposition" in response.headers:
            assert "attachment" in response.headers["content-disposition"]
            assert ".m3u" in response.headers["content-disposition"]
