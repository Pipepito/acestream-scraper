"""
Integration tests for TV Channel endpoints
"""

import pytest
import uuid
from fastapi import status


class TestTVChannelEndpoints:
    """Test TV channel CRUD operations."""

    def test_get_tv_channels_empty(self, client):
        """Test getting TV channels when none exist."""
        response = client.get("/api/v1/tv-channels/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {"items": [], "total": 0}

    def test_get_tv_channels_with_data(self, client, seed_tv_channels):
        """Test getting TV channels with data."""
        response = client.get("/api/v1/tv-channels/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        # Check that the names contain the expected prefixes (with timestamps)
        assert data["items"][0]["name"].startswith("Test TV Channel 1")
        assert data["items"][1]["name"].startswith("Test TV Channel 2")
        assert data["items"][2]["name"].startswith("Test TV Channel 3")

    def test_get_tv_channels_with_pagination(self, client, seed_tv_channels):
        """Test getting TV channels with pagination."""
        response = client.get("/api/v1/tv-channels/?skip=1&limit=1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 1
        # Check that the name contains the expected prefix (with timestamp)
        assert data["items"][0]["name"].startswith("Test TV Channel 2")

    def test_get_tv_channel_by_id(self, client, seed_tv_channels):
        """Test getting a specific TV channel by ID."""
        tv_channel_id = seed_tv_channels[0].id
        response = client.get(f"/api/v1/tv-channels/{tv_channel_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tv_channel_id
        assert data["name"].startswith("Test TV Channel 1")

    def test_get_tv_channel_by_id_not_found(self, client):
        """Test getting a non-existent TV channel."""
        fake_id = 99999
        response = client.get(f"/api/v1/tv-channels/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "TV Channel not found"

    def test_create_tv_channel(self, client, sample_tv_channel_data):
        """Test creating a new TV channel."""
        response = client.post("/api/v1/tv-channels/", json=sample_tv_channel_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_tv_channel_data["name"]
        assert data["description"] == sample_tv_channel_data["description"]
        assert data["logo_url"] == sample_tv_channel_data["logo_url"]
        assert data["category"] == sample_tv_channel_data["category"]
        assert data["country"] == sample_tv_channel_data["country"]
        assert data["language"] == sample_tv_channel_data["language"]
        assert data["website"] == sample_tv_channel_data["website"]
        assert data["epg_id"] == sample_tv_channel_data["epg_id"]
        assert data["channel_number"] == sample_tv_channel_data["channel_number"]
        assert data["is_active"] == sample_tv_channel_data["is_active"]
        assert data["is_favorite"] == sample_tv_channel_data["is_favorite"]

    def test_create_tv_channel_invalid_data(self, client):
        """Test creating a TV channel with invalid data."""
        invalid_data = {"name": ""}  # Missing required fields
        response = client.post("/api/v1/tv-channels/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_tv_channel(self, client, seed_tv_channels):
        """Test updating an existing TV channel."""
        tv_channel_id = seed_tv_channels[0].id
        update_data = {
            "name": "Updated TV Channel Name",
            "description": "Updated description",
            "logo_url": "https://example.com/new-tv-logo.png",
            "category": "News",
            "country": "UK",
            "language": "en-GB",
            "website": "https://updated.com",
            "epg_id": "updated.tv",
            "channel_number": 100,
            "is_active": False,
            "is_favorite": True
        }

        response = client.put(f"/api/v1/tv-channels/{tv_channel_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == tv_channel_id
        assert data["name"] == "Updated TV Channel Name"
        assert data["description"] == "Updated description"
        assert data["logo_url"] == "https://example.com/new-tv-logo.png"
        assert data["category"] == "News"
        assert data["country"] == "UK"
        assert data["language"] == "en-GB"
        assert data["website"] == "https://updated.com"
        assert data["epg_id"] == "updated.tv"
        assert data["channel_number"] == 100
        assert data["is_active"] == False
        assert data["is_favorite"] == True

    def test_update_tv_channel_not_found(self, client):
        """Test updating a non-existent TV channel."""
        fake_id = 99999
        update_data = {"name": "Updated Name"}
        response = client.put(f"/api/v1/tv-channels/{fake_id}", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_tv_channel(self, client, seed_tv_channels):
        """Test deleting a TV channel."""
        tv_channel_id = seed_tv_channels[0].id
        response = client.delete(f"/api/v1/tv-channels/{tv_channel_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify TV channel is deleted
        response = client.get(f"/api/v1/tv-channels/{tv_channel_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_tv_channel_not_found(self, client):
        """Test deleting a non-existent TV channel."""
        fake_id = 99999
        response = client.delete(f"/api/v1/tv-channels/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTVChannelAcestreamAssociations:
    """Test TV channel and acestream channel associations."""

    def test_get_tv_channel_acestreams_empty(self, client, seed_tv_channels):
        """Test getting acestreams for a TV channel with no associations."""
        tv_channel_id = seed_tv_channels[0].id
        response = client.get(f"/api/v1/tv-channels/{tv_channel_id}/acestreams")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_tv_channel_acestreams_with_data(self, client, seed_tv_channels, seed_channels, db_session):
        """Test getting acestreams for a TV channel with associations."""
        tv_channel_id = seed_tv_channels[0].id
        acestream_channel = seed_channels[0]

        # Associate acestream with TV channel
        acestream_channel.tv_channel_id = tv_channel_id
        db_session.commit()

        response = client.get(f"/api/v1/tv-channels/{tv_channel_id}/acestreams")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == acestream_channel.id
        assert data[0]["name"] == acestream_channel.name

    def test_get_tv_channel_acestreams_not_found(self, client):
        """Test getting acestreams for a non-existent TV channel."""
        fake_id = 99999
        response = client.get(f"/api/v1/tv-channels/{fake_id}/acestreams")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_associate_acestream_to_tv_channel(self, client, seed_tv_channels, seed_channels):
        """Test associating an acestream channel with a TV channel."""
        tv_channel_id = seed_tv_channels[0].id
        acestream_id = seed_channels[0].id

        association_data = {"acestream_channel_id": acestream_id}
        response = client.post(f"/api/v1/tv-channels/{tv_channel_id}/acestreams", json=association_data)
        assert response.status_code == status.HTTP_200_OK

        # Verify association was created
        response = client.get(f"/api/v1/tv-channels/{tv_channel_id}/acestreams")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == acestream_id

    def test_associate_acestream_to_tv_channel_not_found(self, client, seed_channels):
        """Test associating acestream with a non-existent TV channel."""
        fake_tv_id = 99999
        acestream_id = seed_channels[0].id

        association_data = {"acestream_channel_id": acestream_id}
        response = client.post(f"/api/v1/tv-channels/{fake_tv_id}/acestreams", json=association_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_associate_nonexistent_acestream_to_tv_channel(self, client, seed_tv_channels):
        """Test associating a non-existent acestream with a TV channel."""
        tv_channel_id = seed_tv_channels[0].id
        fake_acestream_id = str(uuid.uuid4())

        association_data = {"acestream_channel_id": fake_acestream_id}
        response = client.post(f"/api/v1/tv-channels/{tv_channel_id}/acestreams", json=association_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_acestream_from_tv_channel(self, client, seed_tv_channels, seed_channels, db_session):
        """Test removing an acestream association from a TV channel."""
        tv_channel_id = seed_tv_channels[0].id
        acestream_id = seed_channels[0].id

        # Create association first
        acestream_channel = seed_channels[0]
        acestream_channel.tv_channel_id = tv_channel_id
        db_session.commit()

        response = client.delete(f"/api/v1/tv-channels/{tv_channel_id}/acestreams/{acestream_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify association was removed
        response = client.get(f"/api/v1/tv-channels/{tv_channel_id}/acestreams")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_remove_acestream_from_tv_channel_not_found(self, client, seed_channels):
        """Test removing acestream association from a non-existent TV channel."""
        fake_tv_id = 99999
        acestream_id = seed_channels[0].id

        response = client.delete(f"/api/v1/tv-channels/{fake_tv_id}/acestreams/{acestream_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_remove_nonexistent_acestream_from_tv_channel(self, client, seed_tv_channels):
        """Test removing a non-existent acestream from a TV channel."""
        tv_channel_id = seed_tv_channels[0].id
        fake_acestream_id = str(uuid.uuid4())

        response = client.delete(f"/api/v1/tv-channels/{tv_channel_id}/acestreams/{fake_acestream_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestTVChannelBatchOperations:
    """Test TV channel batch operations."""

    def test_batch_assign_acestreams(self, client, seed_tv_channels, seed_channels):
        """Test batch assigning acestreams to TV channels."""
        assignments = [
            {
                "tv_channel_id": seed_tv_channels[0].id,
                "acestream_channel_id": seed_channels[0].id
            },
            {
                "tv_channel_id": seed_tv_channels[1].id,
                "acestream_channel_id": seed_channels[1].id
            }
        ]

        response = client.post("/api/v1/tv-channels/batch-assign", json={"assignments": assignments})
        assert response.status_code == status.HTTP_200_OK

        # Verify assignments were created
        for assignment in assignments:
            response = client.get(f"/api/v1/tv-channels/{assignment['tv_channel_id']}/acestreams")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == assignment["acestream_channel_id"]

    def test_associate_by_epg_id(self, client, seed_tv_channels, seed_channels, db_session):
        """Test associating channels by EPG ID."""
        # Set matching EPG IDs
        seed_tv_channels[0].epg_id = "match.channel"
        seed_channels[0].tvg_id = "match.channel"
        db_session.commit()

        response = client.post("/api/v1/tv-channels/associate-by-epg")
        assert response.status_code == status.HTTP_200_OK

        # Verify association was created
        response = client.get(f"/api/v1/tv-channels/{seed_tv_channels[0].id}/acestreams")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == seed_channels[0].id

    def test_bulk_update_epg_ids(self, client, seed_tv_channels):
        """Test bulk updating EPG IDs for TV channels."""
        updates = [
            {
                "tv_channel_id": seed_tv_channels[0].id,
                "epg_id": "updated.channel.1"
            },
            {
                "tv_channel_id": seed_tv_channels[1].id,
                "epg_id": "updated.channel.2"
            }
        ]

        response = client.post("/api/v1/tv-channels/bulk-update-epg", json={"updates": updates})
        assert response.status_code == status.HTTP_200_OK

        # Verify updates were applied
        for update in updates:
            response = client.get(f"/api/v1/tv-channels/{update['tv_channel_id']}")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["epg_id"] == update["epg_id"]
