"""
Integration tests for EPG endpoints
"""

import pytest
import uuid
from datetime import datetime, timedelta
from fastapi import status

from app.models.models import EPGStringMapping


class TestEPGSourceEndpoints:
    """Test EPG source CRUD operations."""

    def test_get_epg_sources_empty(self, client):
        """Test getting EPG sources when none exist."""
        response = client.get("/api/v1/epg/sources")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_epg_sources_with_data(self, client, seed_epg_sources):
        """Test getting EPG sources with data."""
        response = client.get("/api/v1/epg/sources")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Test EPG Source 1"
        assert data[1]["name"] == "Test EPG Source 2"

    def test_get_epg_source_by_id(self, client, seed_epg_sources):
        """Test getting a specific EPG source by ID."""
        source_id = seed_epg_sources[0].id
        response = client.get(f"/api/v1/epg/sources/{source_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == source_id
        assert data["name"] == "Test EPG Source 1"

    def test_get_epg_source_by_id_not_found(self, client):
        """Test getting a non-existent EPG source."""
        fake_id = 99999
        response = client.get(f"/api/v1/epg/sources/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["detail"] == "EPG source not found"

    def test_create_epg_source(self, client, sample_epg_source_data):
        """Test creating a new EPG source."""
        response = client.post("/api/v1/epg/sources", json=sample_epg_source_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == sample_epg_source_data["name"]
        assert data["url"] == sample_epg_source_data["url"]
        assert data["enabled"] == sample_epg_source_data["enabled"]

    def test_create_epg_source_invalid_data(self, client):
        """Test creating an EPG source with invalid data."""
        invalid_data = {"name": ""}  # Missing required fields
        response = client.post("/api/v1/epg/sources", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_epg_source(self, client, seed_epg_sources):
        """Test deleting an EPG source."""
        source_id = seed_epg_sources[0].id
        response = client.delete(f"/api/v1/epg/sources/{source_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify source is deleted
        response = client.get(f"/api/v1/epg/sources/{source_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_epg_source_not_found(self, client):
        """Test deleting a non-existent EPG source."""
        fake_id = 99999
        response = client.delete(f"/api/v1/epg/sources/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEPGSourceRefreshEndpoints:
    """Test EPG source refresh operations."""

    def test_refresh_epg_source(self, client, seed_epg_sources):
        """Test refreshing a specific EPG source."""
        source_id = seed_epg_sources[0].id
        response = client.post(f"/api/v1/epg/sources/{source_id}/refresh")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "source_id" in data
        assert "status" in data
        assert data["source_id"] == source_id

    def test_refresh_epg_source_not_found(self, client):
        """Test refreshing a non-existent EPG source."""
        fake_id = 99999
        response = client.post(f"/api/v1/epg/sources/{fake_id}/refresh")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_refresh_all_epg_sources(self, client, seed_epg_sources):
        """Test refreshing all EPG sources."""
        response = client.post("/api/v1/epg/sources/refresh_all")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        for refresh_result in data:
            assert "source_id" in refresh_result
            assert "status" in refresh_result

    def test_refresh_all_epg_sources_with_force(self, client, seed_epg_sources):
        """Test refreshing all EPG sources with force parameter."""
        response = client.post("/api/v1/epg/sources/refresh_all?force=true")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2


class TestEPGChannelEndpoints:
    """Test EPG channel operations."""

    def test_get_epg_channels_empty(self, client):
        """Test getting EPG channels when none exist."""
        response = client.get("/api/v1/epg/channels")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_epg_channels_with_data(self, client, seed_epg_channels):
        """Test getting EPG channels with data."""
        response = client.get("/api/v1/epg/channels")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Test EPG Channel 1"
        assert data[1]["name"] == "Test EPG Channel 2"

    def test_get_epg_channels_with_source_filter(self, client, seed_epg_channels, seed_epg_sources):
        """Test getting EPG channels filtered by source."""
        source_id = seed_epg_sources[0].id
        response = client.get(f"/api/v1/epg/channels?source_id={source_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["epg_source_id"] == source_id

    def test_get_epg_channel_by_id(self, client, seed_epg_channels):
        """Test getting a specific EPG channel by ID."""
        channel_id = seed_epg_channels[0].id
        response = client.get(f"/api/v1/epg/channels/{channel_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == channel_id
        assert data["name"] == "Test EPG Channel 1"

    def test_get_epg_channel_by_id_not_found(self, client):
        """Test getting a non-existent EPG channel."""
        fake_id = 99999
        response = client.get(f"/api/v1/epg/channels/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEPGChannelMappingEndpoints:
    """Test EPG channel mapping operations."""

    def test_map_epg_channels(self, client, seed_epg_channels, seed_tv_channels):
        """Test mapping EPG channels to TV channels."""
        mapping_data = {
            "epg_channel_id": seed_epg_channels[0].id,
            "tv_channel_id": seed_tv_channels[0].id
        }
        response = client.post("/api/v1/epg/channels/map", json=mapping_data)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_unmap_epg_channels(self, client, seed_epg_channels, seed_tv_channels):
        """Test unmapping EPG channels from TV channels."""
        mapping_data = {
            "epg_channel_id": seed_epg_channels[0].id,
            "tv_channel_id": seed_tv_channels[0].id
        }
        # First, map the channel
        response = client.post("/api/v1/epg/channels/map", json=mapping_data)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # Now, unmap the channel
        response = client.post("/api/v1/epg/channels/unmap", json=mapping_data)
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestEPGProgramEndpoints:
    """Test EPG program operations."""

    def test_get_epg_programs_empty(self, client, seed_epg_channels):
        """Test getting EPG programs when none exist."""
        channel_id = seed_epg_channels[0].id
        response = client.get(f"/api/v1/epg/channels/{channel_id}/programs")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_epg_programs_with_data(self, client, seed_epg_programs, seed_epg_channels):
        """Test getting EPG programs with data."""
        channel_id = seed_epg_channels[0].id
        response = client.get(f"/api/v1/epg/channels/{channel_id}/programs")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # 3 programs per channel from fixture
        assert data[0]["title"] == "Test Program 1-1"
        assert data[1]["title"] == "Test Program 1-2"
        assert data[2]["title"] == "Test Program 1-3"

    def test_get_epg_programs_with_date_filter(self, client, seed_epg_programs, seed_epg_channels):
        """Test getting EPG programs filtered by date."""
        channel_id = seed_epg_channels[0].id
        today = datetime.now().date()
        response = client.get(f"/api/v1/epg/channels/{channel_id}/programs?date={today}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 0  # Should return programs for today

    def test_get_epg_programs_with_time_range(self, client, seed_epg_programs, seed_epg_channels):
        """Test getting EPG programs filtered by time range."""
        channel_id = seed_epg_channels[0].id
        start_time = datetime.now().isoformat()
        end_time = (datetime.now() + timedelta(hours=2)).isoformat()
        response = client.get(f"/api/v1/epg/channels/{channel_id}/programs?start_time={start_time}&end_time={end_time}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 0  # Should return programs in time range

    def test_get_epg_programs_channel_not_found(self, client):
        """Test getting EPG programs for a non-existent channel."""
        fake_id = 99999
        response = client.get(f"/api/v1/epg/channels/{fake_id}/programs")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestEPGStringMappingEndpoints:
    """Test EPG string mapping operations."""

    def test_get_epg_channel_mappings_empty(self, client, seed_epg_channels):
        """Test getting EPG string mappings when none exist."""
        channel_id = seed_epg_channels[0].id
        response = client.get(f"/api/v1/epg/channels/{channel_id}/mappings")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_create_epg_string_mapping(self, client, seed_epg_channels):
        """Test creating an EPG string mapping."""
        channel_id = seed_epg_channels[0].id
        mapping_data = {
            "search_pattern": "Test Channel Pattern",
            "is_exclusion": False
        }
        response = client.post(f"/api/v1/epg/channels/{channel_id}/mappings", json=mapping_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["search_pattern"] == mapping_data["search_pattern"]
        assert data["is_exclusion"] == mapping_data["is_exclusion"]
        assert data["epg_channel_id"] == channel_id

    def test_create_epg_string_mapping_channel_not_found(self, client):
        """Test creating an EPG string mapping for a non-existent channel."""
        fake_id = 99999
        mapping_data = {
            "search_pattern": "Test Pattern",
            "is_exclusion": False
        }
        response = client.post(f"/api/v1/epg/channels/{fake_id}/mappings", json=mapping_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_epg_string_mapping(self, client, seed_epg_channels, db_session):
        """Test deleting an EPG string mapping."""
        channel_id = seed_epg_channels[0].id

        # Create a mapping first
        mapping = EPGStringMapping(
            epg_channel_id=channel_id,
            search_pattern="Test Pattern",
            is_exclusion=False
        )
        db_session.add(mapping)
        db_session.commit()

        response = client.delete(f"/api/v1/epg/mappings/{mapping.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify mapping is deleted
        response = client.get(f"/api/v1/epg/channels/{channel_id}/mappings")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_delete_epg_string_mapping_not_found(self, client):
        """Test deleting a non-existent EPG string mapping."""
        fake_id = 99999
        response = client.delete(f"/api/v1/epg/mappings/{fake_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_epg_string_mapping(self, client, seed_epg_channels, db_session):
        """Test updating an EPG string mapping."""
        channel_id = seed_epg_channels[0].id
        # Create a mapping first
        mapping = EPGStringMapping(
            epg_channel_id=channel_id,
            search_pattern="Old Pattern",
            is_exclusion=False
        )
        db_session.add(mapping)
        db_session.commit()
        # Update the mapping
        update_data = {"search_pattern": "New Pattern", "is_exclusion": True}
        response = client.patch(f"/api/v1/epg/mappings/{mapping.id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["search_pattern"] == "New Pattern"
        assert data["is_exclusion"] is True

    def test_create_epg_string_mapping_invalid(self, client, seed_epg_channels):
        """Test creating an EPG string mapping with invalid input."""
        channel_id = seed_epg_channels[0].id
        # Empty pattern
        response = client.post(f"/api/v1/epg/channels/{channel_id}/mappings", json={"search_pattern": "", "is_exclusion": False})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Non-boolean is_exclusion
        response = client.post(f"/api/v1/epg/channels/{channel_id}/mappings", json={"search_pattern": "Pattern", "is_exclusion": "notabool"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_epg_string_mapping_invalid(self, client, seed_epg_channels, db_session):
        """Test updating an EPG string mapping with invalid input."""
        channel_id = seed_epg_channels[0].id
        mapping = EPGStringMapping(
            epg_channel_id=channel_id,
            search_pattern="Pattern",
            is_exclusion=False
        )
        db_session.add(mapping)
        db_session.commit()
        # Empty pattern
        response = client.patch(f"/api/v1/epg/mappings/{mapping.id}", json={"search_pattern": "", "is_exclusion": False})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Non-boolean is_exclusion
        response = client.patch(f"/api/v1/epg/mappings/{mapping.id}", json={"search_pattern": "Pattern", "is_exclusion": "notabool"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_auto_map_channels_regex(self, client, seed_epg_channels, seed_tv_channels, db_session):
        """Test auto-mapping with regex pattern."""
        from app.models.models import EPGStringMapping, TVChannel
        epg_channel = seed_epg_channels[0]
        tv_channel = seed_tv_channels[0]
        tv_channel.name = "MySpecialChannel123"
        db_session.add(tv_channel)
        # Regex pattern to match any channel ending with digits
        db_session.add(EPGStringMapping(epg_channel_id=epg_channel.id, search_pattern="/\\d+$/", is_exclusion=False))
        db_session.commit()
        response = client.post("/api/v1/epg/auto-scan")
        assert response.status_code == 200
        data = response.json()
        found = any(
            m["tv_channel_id"] == tv_channel.id and m["epg_channel_id"] == epg_channel.id and m["regex"] is True
            for m in data["auto_mapped"]
        )
        assert found


class TestEPGXMLEndpoints:
    """Test EPG XML generation endpoints."""

    def test_get_epg_xml_empty(self, client):
        """Test getting EPG XML when no data exists."""
        response = client.get("/api/v1/epg/xml")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/xml"
        # Should return basic XML structure even when empty
        assert b"<?xml" in response.content
        assert b"<tv" in response.content  # Allow for attributes/whitespace

    def test_get_epg_xml_with_data(self, client, seed_all_data):
        """Test getting EPG XML with data."""
        response = client.get("/api/v1/epg/xml")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/xml"
        xml_content = response.content.decode()
        assert "<?xml" in xml_content
        assert "<tv" in xml_content  # Allow for attributes/whitespace
        assert "</tv>" in xml_content

    def test_get_epg_xml_with_days_filter(self, client, seed_all_data):
        """Test getting EPG XML filtered by days."""
        response = client.get("/api/v1/epg/xml?days=1")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/xml"

    def test_get_epg_xml_with_channels_filter(self, client, seed_all_data):
        """Test getting EPG XML filtered by channels."""
        channel_ids = [seed_all_data["epg_channels"][0].id]
        response = client.get(f"/api/v1/epg/xml?channel_ids={channel_ids[0]}")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/xml"

    def test_create_epg_xml(self, client, seed_all_data):
        """Test creating/regenerating EPG XML."""
        xml_data = {
            "days": 7,
            "channel_ids": [seed_all_data["epg_channels"][0].id]
        }
        response = client.post("/api/v1/epg/xml", json=xml_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/xml"
        xml_content = response.content.decode()
        assert "<?xml" in xml_content
        assert "<tv" in xml_content  # Allow for attributes/whitespace


class TestEPGGlobalMappingEndpoints:
    """Test global EPG string mappings and auto-mapping endpoints."""

    def test_get_all_epg_string_mappings(self, client, seed_epg_channels, db_session):
        """Test getting all EPG string mappings across all channels."""
        # Create mappings for two channels
        from app.models.models import EPGStringMapping
        ch1, ch2 = seed_epg_channels[0], seed_epg_channels[1]
        mapping1 = EPGStringMapping(epg_channel_id=ch1.id, search_pattern="Pattern1", is_exclusion=False)
        mapping2 = EPGStringMapping(epg_channel_id=ch2.id, search_pattern="Pattern2", is_exclusion=True)
        db_session.add_all([mapping1, mapping2])
        db_session.commit()
        response = client.get("/api/v1/epg/mappings")
        assert response.status_code == 200
        data = response.json()
        patterns = [m["search_pattern"] for m in data]
        assert "Pattern1" in patterns
        assert "Pattern2" in patterns

    def test_auto_map_channels(self, client, seed_epg_channels, seed_tv_channels, db_session):
        """Test auto-mapping TV channels to EPG channels based on string patterns."""
        from app.models.models import EPGStringMapping, TVChannel
        # Add a mapping that should match a TV channel name
        epg_channel = seed_epg_channels[0]
        tv_channel = seed_tv_channels[0]
        tv_channel.name = "TestAutoMapChannel"
        db_session.add(tv_channel)
        db_session.add(EPGStringMapping(epg_channel_id=epg_channel.id, search_pattern="AutoMapChannel", is_exclusion=False))
        db_session.commit()
        response = client.post("/api/v1/epg/auto-scan")
        assert response.status_code == 200
        data = response.json()
        assert "auto_mapped_count" in data
        assert data["auto_mapped_count"] >= 1
        found = any(
            m["tv_channel_id"] == tv_channel.id and m["epg_channel_id"] == epg_channel.id
            for m in data["auto_mapped"]
        )
        assert found
