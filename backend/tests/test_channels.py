"""
Integration tests for Channel endpoints
"""

import pytest
import uuid
from fastapi import status


class TestChannelEndpoints:
    """Test channel CRUD operations."""

    def test_get_channels_empty(self, client):
        """Test getting channels when none exist."""
        response = client.get("/api/v1/channels/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == {"items": [], "total": 0}

    def test_get_channels_with_data(self, client, seed_channels):
        """Test getting channels with data."""
        response = client.get("/api/v1/channels/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["items"][0]["name"] == "Alpha Channel"
        assert data["items"][1]["name"] == "Beta Channel"
        assert data["items"][2]["name"] == "Gamma Channel"

    def test_get_channels_with_search(self, client, seed_channels):
        """Test getting channels with search filter."""
        response = client.get("/api/v1/channels/?search=Alpha")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Alpha Channel"

    def test_get_channels_with_pagination(self, client, seed_channels):
        """Test getting channels with pagination."""
        response = client.get("/api/v1/channels/?skip=1&limit=1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Beta Channel"

    def test_get_channels_with_group_filter(self, client, seed_channels):
        """Test getting channels with group filter."""
        response = client.get("/api/v1/channels/?group=Group 1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["group"] == "Group 1"

    def test_get_channel_by_id(self, client, seed_channels):
        """Test getting a specific channel by ID."""
        channel_id = seed_channels[0].id
        response = client.get(f"/api/v1/channels/{channel_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == channel_id
        assert data["name"] == "Alpha Channel"

    def test_get_channel_by_id_not_found(self, client):
        """Test getting a non-existent channel."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/channels/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "Channel not found"

    def test_create_channel(self, client, sample_channel_data):
        """Test creating a new channel."""
        response = client.post("/api/v1/channels/", json=sample_channel_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_channel_data["name"]
        assert data["group"] == sample_channel_data["group"]
        assert data["logo"] == sample_channel_data["logo"]
        assert data["tvg_id"] == sample_channel_data["tvg_id"]
        assert data["tvg_name"] == sample_channel_data["tvg_name"]
        assert data["source_url"] == sample_channel_data["source_url"]
        assert data["is_active"] == sample_channel_data["is_active"]
        assert data["is_online"] == sample_channel_data["is_online"]

    def test_create_channel_with_existing_id(self, client, seed_channels, sample_channel_data):
        """Test creating a channel with an existing ID (should update)."""
        existing_id = seed_channels[0].id
        sample_channel_data["id"] = existing_id
        sample_channel_data["name"] = "Updated Channel Name"

        response = client.post("/api/v1/channels/", json=sample_channel_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == existing_id
        assert data["name"] == "Updated Channel Name"

    def test_create_channel_invalid_data(self, client):
        """Test creating a channel with invalid data."""
        invalid_data = {"name": ""}  # Missing required fields
        response = client.post("/api/v1/channels/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_channel(self, client, seed_channels):
        """Test updating an existing channel."""
        channel_id = seed_channels[0].id
        update_data = {
            "name": "Updated Channel Name",
            "group": "Updated Group",
            "logo": "https://example.com/new-logo.png",
            "tvg_id": "updated.channel",
            "tvg_name": "Updated Channel",
            "source_url": "acestream://updated123456789",
            "is_active": False,
            "is_online": False
        }

        response = client.put(f"/api/v1/channels/{channel_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == channel_id
        assert data["name"] == "Updated Channel Name"
        assert data["group"] == "Updated Group"
        assert data["logo"] == "https://example.com/new-logo.png"
        assert data["tvg_id"] == "updated.channel"
        assert data["tvg_name"] == "Updated Channel"
        assert data["source_url"] == "acestream://updated123456789"
        assert data["is_active"] == False
        assert data["is_online"] == False

    def test_update_channel_not_found(self, client):
        """Test updating a non-existent channel."""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "Updated Name"}
        response = client.put(f"/api/v1/channels/{fake_id}", json=update_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_channel(self, client, seed_channels):
        """Test deleting a channel."""
        channel_id = seed_channels[0].id
        response = client.delete(f"/api/v1/channels/{channel_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify channel is deleted
        response = client.get(f"/api/v1/channels/{channel_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_channel_not_found(self, client):
        """Test deleting a non-existent channel."""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/v1/channels/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestChannelStatusEndpoints:
    """Test channel status checking endpoints."""

    def test_check_channel_status(self, client, seed_channels):
        """Test checking status of a specific channel."""
        channel_id = seed_channels[0].id
        response = client.post(f"/api/v1/channels/{channel_id}/check_status")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "channel_id" in data
        assert "is_online" in data
        assert "last_checked" in data
        assert data["channel_id"] == channel_id

    def test_check_channel_status_not_found(self, client):
        """Test checking status of a non-existent channel."""
        fake_id = str(uuid.uuid4())
        response = client.post(f"/api/v1/channels/{fake_id}/check_status")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_check_all_channels_status(self, client, seed_channels):
        """Test checking status of all channels."""
        response = client.post("/api/v1/channels/check_status_all")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "total_checked" in data
        assert "online_count" in data
        assert "offline_count" in data
        assert data["total_checked"] == 3
        assert len(data["results"]) == 3

    def test_check_all_channels_status_with_limit(self, client, seed_channels):
        """Test checking status of channels with limit."""
        response = client.post("/api/v1/channels/check_status_all?limit=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_checked"] == 2
        assert len(data["results"]) == 2

    def test_get_status_summary(self, client, seed_channels):
        """Test getting channel status summary."""
        response = client.get("/api/v1/channels/status_summary")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_channels" in data
        assert "active_channels" in data
        assert "online_channels" in data
        assert "offline_channels" in data
        assert "last_checked_channels" in data
        assert data["total_channels"] == 3
        assert data["active_channels"] == 3


class TestChannelGroupEndpoints:
    """Test channel group-related endpoints."""

    def test_get_channel_groups(self, client, seed_channels):
        """Test getting unique channel groups."""
        response = client.get("/api/v1/channels/groups")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert "Group 1" in data
        assert "Group 2" in data
        assert "Group 3" in data

    def test_get_channels_by_group(self, client, seed_channels):
        """Test getting channels filtered by group."""
        response = client.get("/api/v1/channels/?group=Group 1")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["group"] == "Group 1"
