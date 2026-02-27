"""
Integration tests for Health endpoints
"""

import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test health monitoring endpoints."""

    def test_get_health_status(self, client):
        """Test getting application health status."""
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should contain basic health information
        assert "status" in data
        assert "version" in data
        assert "acestream" in data

        # Status should be healthy or degraded (depends on external services)
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

        # Version should be present
        assert data["version"] is not None

        # Acestream status should be checked
        assert "status" in data["acestream"]

    def test_health_status_structure(self, client):
        """Test the structure of health status response."""
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check required fields based on actual schema
        required_fields = ["status", "version", "acestream", "settings"]
        for field in required_fields:
            assert field in data

        # Check acestream sub-structure
        assert isinstance(data["acestream"], dict)
        assert "status" in data["acestream"]

        # Optional fields that might be present
        optional_fields = ["uptime", "memory", "cpu", "dependencies"]
        for field in optional_fields:
            if field in data:
                assert data[field] is not None

    def test_health_status_with_database_info(self, client, db_session):
        """Test health status includes database information."""
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Database should be accessible
        assert data["database"]["status"] in ["connected", "healthy"]

        # May include additional database info
        if "connection_pool" in data["database"]:
            assert isinstance(data["database"]["connection_pool"], dict)
        if "tables" in data["database"]:
            assert isinstance(data["database"]["tables"], (list, int))

    def test_health_status_response_time(self, client):
        """Test that health endpoint responds quickly."""
        import time

        start_time = time.time()
        response = client.get("/api/v1/health")
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK

        # Health check should be fast (less than 1 second)
        response_time = end_time - start_time
        assert response_time < 1.0


class TestStatsEndpoints:
    """Test statistics endpoints."""

    def test_get_stats(self, client):
        """Test getting application statistics."""
        response = client.get("/api/v1/stats")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should contain various statistics
        assert isinstance(data, dict)

        # May contain these statistics
        possible_stats = [
            "channels", "tv_channels", "epg_sources", "epg_channels",
            "epg_programs", "scraped_urls", "uptime", "requests"
        ]

        # At least some stats should be present
        assert len(data) > 0

        # All values should be numeric or string
        for key, value in data.items():
            assert isinstance(value, (int, float, str, dict))

    def test_get_stats_with_data(self, client, seed_all_data):
        """Test getting statistics with data in database."""
        response = client.get("/api/v1/stats")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should reflect the seeded data
        if "total_channels" in data:
            assert data["total_channels"] >= 3  # We seeded 3 channels
        if "tv_channels" in data:
            assert data["tv_channels"] >= 3  # We seeded 3 TV channels
        if "epg_sources" in data:
            assert data["epg_sources"] >= 2  # We seeded 2 EPG sources
        if "epg_channels" in data:
            assert data["epg_channels"] >= 2  # We seeded 2 EPG channels
        if "epg_programs" in data:
            assert data["epg_programs"] >= 6  # We seeded 6 programs (3 per channel)
        if "scraped_urls" in data:
            assert data["scraped_urls"] >= 3  # We seeded 3 URLs

    def test_get_stats_categories(self, client, seed_all_data):
        """Test statistics are categorized properly."""
        response = client.get("/api/v1/stats")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check for different categories of stats
        database_stats = ["channels", "tv_channels", "epg_sources", "epg_channels", "epg_programs", "scraped_urls"]
        system_stats = ["uptime", "memory", "cpu"]
        application_stats = ["requests", "errors", "version"]

        # At least some database stats should be present
        database_stat_count = sum(1 for stat in database_stats if stat in data)
        assert database_stat_count > 0

    def test_get_stats_numerical_values(self, client, seed_all_data):
        """Test that count statistics are numerical."""
        response = client.get("/api/v1/stats")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Count fields should be integers
        count_fields = ["total_channels", "tv_channels", "epg_sources", "epg_channels", "epg_programs", "scraped_urls"]

        for field in count_fields:
            if field in data:
                assert isinstance(data[field], int)
                assert data[field] >= 0

    def test_get_stats_consistency(self, client, seed_all_data):
        """Test that statistics are consistent across multiple calls."""
        # Get stats twice
        response1 = client.get("/api/v1/stats")
        response2 = client.get("/api/v1/stats")

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        data1 = response1.json()
        data2 = response2.json()

        # Database counts should be the same
        count_fields = ["total_channels", "tv_channels", "epg_sources", "epg_channels", "epg_programs", "scraped_urls"]

        for field in count_fields:
            if field in data1 and field in data2:
                assert data1[field] == data2[field]


class TestHealthIntegration:
    """Test health endpoints integration with system state."""

    def test_health_reflects_database_state(self, client, db_session):
        """Test that health status reflects database connectivity."""
        response = client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # With working database, should be healthy
        assert data["status"] == "healthy"
        assert data["database"]["status"] in ["connected", "healthy"]

    def test_stats_update_with_database_changes(self, client, db_session):
        """Test that stats update when database changes."""
        # Get initial stats
        response = client.get("/api/v1/stats")
        assert response.status_code == status.HTTP_200_OK
        initial_data = response.json()
        initial_channels = initial_data.get("channels", 0)

        # Add a channel
        from app.models.models import AcestreamChannel
        import uuid

        new_channel = AcestreamChannel(
            id=str(uuid.uuid4()),
            name="Stats Test Channel",
            group="Stats Group",
            source_url="acestream://stats123456789",
            is_active=True,
            is_online=True
        )
        db_session.add(new_channel)
        db_session.commit()

        # Get updated stats
        response = client.get("/api/v1/stats")
        assert response.status_code == status.HTTP_200_OK
        updated_data = response.json()
        updated_channels = updated_data.get("channels", 0)

        # Channel count should have increased
        assert updated_channels == initial_channels + 1

    def test_health_endpoint_error_handling(self, client):
        """Test health endpoint handles errors gracefully."""
        response = client.get("/api/v1/health")

        # Should always return a response, even if there are issues
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "status" in data
        else:
            # Service unavailable should still have some info
            data = response.json()
            assert "status" in data
            assert data["status"] in ["unhealthy", "error", "degraded"]

    def test_stats_endpoint_performance(self, client, seed_all_data):
        """Test that stats endpoint performs well with data."""
        import time

        start_time = time.time()
        response = client.get("/api/v1/stats")
        end_time = time.time()

        assert response.status_code == status.HTTP_200_OK

        # Stats should be computed quickly (less than 2 seconds)
        response_time = end_time - start_time
        assert response_time < 2.0

    def test_health_and_stats_compatibility(self, client):
        """Test that health and stats endpoints are compatible."""
        health_response = client.get("/api/v1/health")
        stats_response = client.get("/api/v1/stats")

        assert health_response.status_code == status.HTTP_200_OK
        assert stats_response.status_code == status.HTTP_200_OK

        health_data = health_response.json()
        stats_data = stats_response.json()

        # Both should provide information about the system
        assert "status" in health_data
        assert len(stats_data) > 0

        # If health includes version, stats might too
        if "version" in health_data and "version" in stats_data:
            assert health_data["version"] == stats_data["version"]
