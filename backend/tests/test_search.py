"""
Integration tests for Search endpoints
"""

import pytest
import uuid
from fastapi import status


class TestSearchEndpoints:
    """Test search operations."""

    def test_search_channels_empty_query(self, client, mock_search_service):
        """Test searching with empty query."""
        response = client.get("/api/v1/search")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "pagination" in data
        assert "success" in data
        assert data["success"] == True
        assert data["pagination"]["total_results"] == 2  # Based on mock data
        assert len(data["results"]) == 2

    def test_search_channels_with_query(self, client, mock_search_service):
        """Test searching with a query."""
        response = client.get("/api/v1/search?q=test")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "pagination" in data
        assert "success" in data
        assert data["pagination"]["total_results"] >= 0
        assert isinstance(data["results"], list)

    def test_search_channels_with_pagination(self, client, mock_search_service):
        """Test searching with pagination parameters."""
        response = client.get("/api/v1/search?q=test&page=2&page_size=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["page_size"] == 10

    def test_search_channels_with_category(self, client, mock_search_service):
        """Test searching with category filter."""
        response = client.get("/api/v1/search?q=test&category=entertainment")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "pagination" in data
        assert "total_results" in data["pagination"]

    def test_search_channels_with_invalid_page(self, client, mock_search_service):
        """Test searching with invalid page parameter."""
        response = client.get("/api/v1/search?q=test&page=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_channels_with_invalid_per_page(self, client, mock_search_service):
        """Test searching with invalid per_page parameter."""
        response = client.get("/api/v1/search?q=test&per_page=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_channels_with_large_per_page(self, client, mock_search_service):
        """Test searching with large per_page parameter."""
        response = client.get("/api/v1/search?q=test&per_page=1000")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should be capped at maximum allowed
        assert data["pagination"]["page_size"] <= 100


class TestSearchAddEndpoints:
    """Test adding channels from search results."""

    def test_add_channel_from_search(self, client, mock_search_service):
        """Test adding a channel from search results."""
        channel_data = {
            "id": str(uuid.uuid4()),
            "name": "Test Search Channel",
            "url": "acestream://test123456789",
            "category": "Entertainment",
            "description": "A test channel from search",
            "logo": "https://example.com/logo.png"
        }
        response = client.post("/api/v1/search/add", json=channel_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Channel added successfully"
        assert "channel" in data
        assert data["channel"]["name"] == channel_data["name"]
        assert data["channel"]["source_url"] == channel_data["url"]

    def test_add_channel_from_search_invalid_data(self, client, mock_search_service):
        """Test adding a channel with invalid data."""
        invalid_data = {"name": ""}  # Missing required fields
        response = client.post("/api/v1/search/add", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_add_channel_from_search_missing_id(self, client, mock_search_service):
        """Test adding a channel without ID."""
        channel_data = {
            "name": "Test Search Channel",
            "url": "acestream://test123456789",
            "category": "Entertainment"
        }
        response = client.post("/api/v1/search/add", json=channel_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "channel" in data
        assert data["channel"]["name"] == channel_data["name"]
        # Should generate an ID
        assert data["channel"]["id"] is not None

    def test_add_channel_from_search_duplicate(self, client, seed_channels):
        """Test adding a channel that already exists."""
        existing_channel = seed_channels[0]
        channel_data = {
            "id": existing_channel.id,
            "name": "Updated Channel Name",
            "url": "acestream://updated123456789",
            "category": "Entertainment"
        }
        response = client.post("/api/v1/search/add", json=channel_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Channel updated successfully"
        assert data["channel"]["name"] == channel_data["name"]

    def test_add_channel_with_tv_channel_association(self, client, seed_tv_channels):
        """Test adding a channel with TV channel association."""
        tv_channel_id = seed_tv_channels[0].id
        channel_data = {
            "id": str(uuid.uuid4()),
            "name": "Test Search Channel",
            "url": "acestream://test123456789",
            "category": "Entertainment",
            "tv_channel_id": tv_channel_id
        }
        response = client.post("/api/v1/search/add", json=channel_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["channel"]["tv_channel_id"] == tv_channel_id


class TestSearchAddMultipleEndpoints:
    """Test adding multiple channels from search results."""

    def test_add_multiple_channels_from_search(self, client):
        """Test adding multiple channels from search results."""
        channels_data = [
            {
                "id": str(uuid.uuid4()),
                "name": "Test Search Channel 1",
                "url": "acestream://test123456789",
                "category": "Entertainment"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Test Search Channel 2",
                "url": "acestream://test987654321",
                "category": "Sports"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Test Search Channel 3",
                "url": "acestream://test555666777",
                "category": "News"
            }
        ]

        response = client.post("/api/v1/search/add_multiple", json={"channels": channels_data})
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "3 channels processed successfully"
        assert "added_channels" in data
        assert data["added_count"] == 3
        assert len(data["added_channels"]) == 3
        assert data["updated_count"] == 0

    def test_add_multiple_channels_empty_list(self, client):
        """Test adding multiple channels with empty list."""
        response = client.post("/api/v1/search/add_multiple", json={"channels": []})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_multiple_channels_mixed_results(self, client, seed_channels):
        """Test adding multiple channels with mixed results (new and existing)."""
        existing_channel = seed_channels[0]
        channels_data = [
            {
                "id": existing_channel.id,
                "name": "Updated Channel Name",
                "url": "acestream://updated123456789",
                "category": "Entertainment"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "New Search Channel",
                "url": "acestream://new123456789",
                "category": "Sports"
            }
        ]

        response = client.post("/api/v1/search/add_multiple", json={"channels": channels_data})
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "2 channels processed successfully"
        assert data["added_count"] == 1
        assert data["updated_count"] == 1
        assert data["failed_count"] == 0

    def test_add_multiple_channels_with_errors(self, client):
        """Test adding multiple channels with some invalid data."""
        channels_data = [
            {
                "id": str(uuid.uuid4()),
                "name": "Valid Channel",
                "url": "acestream://valid123456789",
                "category": "Entertainment"
            },
            {
                "name": "",  # Invalid: empty name
                "url": "acestream://invalid123456789",
                "category": "Sports"
            }
        ]

        response = client.post("/api/v1/search/add_multiple", json={"channels": channels_data})
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["added_count"] == 1
        assert data["failed_count"] == 1
        assert len(data["results"]) == 2

        # Check that valid channel was added
        valid_result = next(r for r in data["results"] if r["success"])
        assert valid_result["channel"]["name"] == "Valid Channel"

        # Check that invalid channel failed
        invalid_result = next(r for r in data["results"] if not r["success"])
        assert "error" in invalid_result

    def test_add_multiple_channels_with_duplicates_in_batch(self, client):
        """Test adding multiple channels with duplicates within the batch."""
        duplicate_id = str(uuid.uuid4())
        channels_data = [
            {
                "id": duplicate_id,
                "name": "Duplicate Channel 1",
                "url": "acestream://duplicate123456789",
                "category": "Entertainment"
            },
            {
                "id": duplicate_id,
                "name": "Duplicate Channel 2",
                "url": "acestream://duplicate987654321",
                "category": "Sports"
            }
        ]

        response = client.post("/api/v1/search/add_multiple", json={"channels": channels_data})
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        # Should handle duplicates gracefully
        assert data["added_count"] <= 2

    def test_add_multiple_channels_with_associations(self, client, seed_tv_channels):
        """Test adding multiple channels with TV channel associations."""
        tv_channel_id = seed_tv_channels[0].id
        channels_data = [
            {
                "id": str(uuid.uuid4()),
                "name": "Associated Channel 1",
                "url": "acestream://assoc123456789",
                "category": "Entertainment",
                "tv_channel_id": tv_channel_id
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Associated Channel 2",
                "url": "acestream://assoc987654321",
                "category": "Sports",
                "tv_channel_id": tv_channel_id
            }
        ]

        response = client.post("/api/v1/search/add_multiple", json={"channels": channels_data})
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["added_count"] == 2

        # Verify associations were created
        for result in data["results"]:
            if result["success"]:
                assert result["channel"]["tv_channel_id"] == tv_channel_id


class TestSearchIntegration:
    """Test search integration with other components."""

    def test_search_and_verify_channel_creation(self, client, db_session):
        """Test that adding from search actually creates channels in database."""
        channel_data = {
            "id": str(uuid.uuid4()),
            "name": "Integration Test Channel",
            "url": "acestream://integration123456789",
            "category": "Entertainment"
        }

        # Add channel from search
        response = client.post("/api/v1/search/add", json=channel_data)
        assert response.status_code == status.HTTP_201_CREATED
        created_channel = response.json()["channel"]

        # Verify channel exists in database
        response = client.get(f"/api/v1/channels/{created_channel['id']}")
        assert response.status_code == status.HTTP_200_OK
        channel = response.json()
        assert channel["name"] == channel_data["name"]
        assert channel["source_url"] == channel_data["url"]

    def test_search_integration_with_tv_channels(self, client, seed_tv_channels):
        """Test search integration with TV channel associations."""
        tv_channel = seed_tv_channels[0]

        # Add channel from search with TV channel association
        channel_data = {
            "id": str(uuid.uuid4()),
            "name": "TV Integration Channel",
            "url": "acestream://tvintegration123456789",
            "category": "Entertainment",
            "tv_channel_id": tv_channel.id
        }

        response = client.post("/api/v1/search/add", json=channel_data)
        assert response.status_code == status.HTTP_201_CREATED
        created_channel = response.json()["channel"]

        # Verify TV channel association
        response = client.get(f"/api/v1/tv-channels/{tv_channel.id}/acestreams")
        assert response.status_code == status.HTTP_200_OK
        acestreams = response.json()
        assert len(acestreams) == 1
        assert acestreams[0]["id"] == created_channel["id"]
