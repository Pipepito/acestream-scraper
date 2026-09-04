"""
Integration tests for TV Channel endpoints
"""

import pytest
import uuid
from fastapi import status

from app.models.models import AcestreamChannel, EPGChannel, EPGSource, TVChannel
from app.repositories.channel_repository import ChannelRepository


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


class TestTVChannelCreateFromEPG:
    def test_create_tv_channels_from_epg_creates_channel_and_matches_by_epg_id(self, client, seed_epg_channels, seed_channels, db_session):
        epg_channel = seed_epg_channels[0]
        acestream_channel = seed_channels[0]
        acestream_channel.tvg_id = epg_channel.channel_xml_id
        db_session.commit()

        response = client.post("/api/v1/tv-channels/from-epg", json={"epg_channel_ids": [epg_channel.id]})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["created_count"] == 1
        assert data["associated_count"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["epg_id"] == epg_channel.channel_xml_id

        refreshed_acestream_response = client.get(f"/api/v1/tv-channels/{data['items'][0]['id']}/acestreams")
        assert refreshed_acestream_response.status_code == status.HTTP_200_OK
        associated = refreshed_acestream_response.json()
        assert len(associated) == 1
        assert associated[0]["id"] == acestream_channel.id

    def test_create_tv_channels_from_epg_matches_existing_acestream_by_name(self, client, seed_epg_channels, seed_channels, db_session):
        epg_channel = seed_epg_channels[1]
        acestream_channel = seed_channels[1]
        epg_channel.name = "Eurosport 1 HD"
        acestream_channel.name = "EUROSPORT 1"
        acestream_channel.tvg_id = None
        acestream_channel.tvg_name = None
        db_session.commit()

        response = client.post("/api/v1/tv-channels/from-epg", json={"epg_channel_ids": [epg_channel.id]})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["created_count"] == 1
        assert data["associated_count"] == 1

        refreshed_acestream_response = client.get(f"/api/v1/tv-channels/{data['items'][0]['id']}/acestreams")
        assert refreshed_acestream_response.status_code == status.HTTP_200_OK
        associated = refreshed_acestream_response.json()
        assert len(associated) == 1
        assert associated[0]["id"] == acestream_channel.id

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


@pytest.fixture
def seeded_match_data(db_session):
    primary_source = EPGSource(url="https://example.com/epg-primary.xml", name="Primary Source", enabled=True)
    secondary_source = EPGSource(url="https://example.com/epg-secondary.xml", name="Secondary Source", enabled=True)
    db_session.add_all([primary_source, secondary_source])
    db_session.flush()

    epg_channels = {
        "xml_exact": EPGChannel(
            epg_source_id=primary_source.id,
            channel_xml_id="xml-match-1",
            name="Alpha Sports HD",
            language="en",
        ),
        "normalized_exact": EPGChannel(
            epg_source_id=primary_source.id,
            channel_xml_id="name-match-1",
            name="Canal Plus Liga HD",
            language="es",
        ),
        "fuzzy": EPGChannel(
            epg_source_id=primary_source.id,
            channel_xml_id="fuzzy-match-1",
            name="Premier Sports 1 HD",
            language="en",
        ),
        "multi_candidate": EPGChannel(
            epg_source_id=secondary_source.id,
            channel_xml_id="multi-match-1",
            name="Arena Vision 2",
            language="en",
        ),
        "conflict_winner": EPGChannel(
            epg_source_id=secondary_source.id,
            channel_xml_id="shared-match-1",
            name="Shared Sports One",
            language="en",
        ),
        "conflict_loser": EPGChannel(
            epg_source_id=secondary_source.id,
            channel_xml_id="shared-match-2",
            name="Shared Sports Uno",
            language="en",
        ),
    }
    db_session.add_all(list(epg_channels.values()))

    acestream_channels = [
        AcestreamChannel(
            id=str(uuid.uuid4()),
            name="Alpha Sports",
            tvg_id="xml-match-1",
            tvg_name="Alpha Sports",
            source_url="https://example.com/a1.m3u8",
            is_active=True,
            is_online=True,
        ),
        AcestreamChannel(
            id=str(uuid.uuid4()),
            name="Canal Liga",
            tvg_id=None,
            tvg_name="Canal Plus Liga",
            source_url="https://example.com/a2.m3u8",
            is_active=True,
            is_online=True,
        ),
        AcestreamChannel(
            id=str(uuid.uuid4()),
            name="Premier Sport One",
            tvg_id=None,
            tvg_name=None,
            source_url="https://example.com/a3.m3u8",
            is_active=True,
            is_online=True,
        ),
        AcestreamChannel(
            id=str(uuid.uuid4()),
            name="Arena Vision 2",
            tvg_id=None,
            tvg_name=None,
            source_url="https://example.com/a4.m3u8",
            is_active=True,
            is_online=True,
        ),
        AcestreamChannel(
            id=str(uuid.uuid4()),
            name="Arena Vision Two",
            tvg_id=None,
            tvg_name=None,
            source_url="https://example.com/a5.m3u8",
            is_active=True,
            is_online=True,
        ),
        AcestreamChannel(
            id=str(uuid.uuid4()),
            name="Shared Sports 1",
            tvg_id=None,
            tvg_name=None,
            source_url="https://example.com/a6.m3u8",
            is_active=True,
            is_online=True,
        ),
    ]
    db_session.add_all(acestream_channels)
    db_session.commit()

    return {
        "sources": {"primary": primary_source, "secondary": secondary_source},
        "epg_channels": epg_channels,
        "acestream_channels": acestream_channels,
    }


@pytest.fixture
def seeded_unmatched_data(db_session):
    source = EPGSource(url="https://example.com/epg-unmatched.xml", name="Unmatched Source", enabled=True)
    db_session.add(source)
    db_session.flush()

    epg_channels = [
        EPGChannel(epg_source_id=source.id, channel_xml_id="nomatch-1", name="Documentary Planet", language="en"),
        EPGChannel(epg_source_id=source.id, channel_xml_id="nomatch-2", name="Cinema World", language="en"),
    ]
    db_session.add_all(
        epg_channels
        + [
            AcestreamChannel(
                id=str(uuid.uuid4()),
                name="Fishing Network",
                tvg_id="other-id",
                tvg_name="Fishing Network",
                source_url="https://example.com/u1.m3u8",
                is_active=True,
                is_online=True,
            ),
        ]
    )
    db_session.commit()

    return {"source": source, "epg_channels": epg_channels}


@pytest.fixture
def seeded_conflict_data(db_session):
    source = EPGSource(url="https://example.com/epg-conflict.xml", name="Conflict Source", enabled=True)
    db_session.add(source)
    db_session.flush()

    winner = EPGChannel(epg_source_id=source.id, channel_xml_id="winner-id", name="Arena Sports 1", language="en")
    loser = EPGChannel(epg_source_id=source.id, channel_xml_id="loser-id", name="Arena Sports Uno", language="en")
    shared = AcestreamChannel(
        id="shared-candidate",
        name="Arena Sports 1",
        tvg_id=None,
        tvg_name=None,
        source_url="https://example.com/conflict.m3u8",
        is_active=True,
        is_online=True,
    )

    db_session.add_all([winner, loser, shared])
    db_session.commit()

    return {"source": source, "winner": winner, "loser": loser, "shared": shared}


class TestTVChannelEPGMatchAnalysis:
    def test_analyze_epg_matches_returns_summary_and_rows(self, client, seeded_match_data):
        response = client.post("/api/v1/tv-channels/analyze-epg-matches", json={"strictness": "balanced"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["summary"]["epg_channels_analyzed"] == 6
        assert data["summary"]["matched_epg_channels"] >= 5
        assert data["summary"]["matched_acestream_channels"] >= 5
        assert data["summary"]["creatable_rows"] >= 5
        assert len(data["rows"]) == 6

    def test_analyze_epg_matches_applies_strictness_thresholds(self, client, seeded_match_data):
        loose = client.post("/api/v1/tv-channels/analyze-epg-matches", json={"strictness": "loose"})
        strict = client.post("/api/v1/tv-channels/analyze-epg-matches", json={"strictness": "strict"})

        assert loose.status_code == status.HTTP_200_OK
        assert strict.status_code == status.HTTP_200_OK
        loose_data = loose.json()
        strict_data = strict.json()
        assert loose_data["summary"]["matched_epg_channels"] >= strict_data["summary"]["matched_epg_channels"]
        loose_fuzzy_row = next(row for row in loose_data["rows"] if row["epg_channel_xml_id"] == "fuzzy-match-1")
        strict_fuzzy_row = next(row for row in strict_data["rows"] if row["epg_channel_xml_id"] == "fuzzy-match-1")
        assert len(loose_fuzzy_row["candidates"]) == 1
        assert strict_fuzzy_row["candidates"] == []

    def test_analyze_epg_matches_honors_source_filter(self, client, seeded_match_data):
        source_id = seeded_match_data["sources"]["secondary"].id
        response = client.post(
            "/api/v1/tv-channels/analyze-epg-matches",
            json={"strictness": "balanced", "source_id": source_id},
        )

        assert response.status_code == status.HTTP_200_OK
        rows = response.json()["rows"]
        assert rows
        assert all(row["epg_source_id"] == source_id for row in rows)

    def test_analyze_epg_matches_returns_clean_zero_summary_when_no_matches_exist(self, client, seeded_unmatched_data):
        response = client.post("/api/v1/tv-channels/analyze-epg-matches", json={"strictness": "balanced"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["summary"]["epg_channels_analyzed"] == 2
        assert data["summary"]["matched_epg_channels"] == 0
        assert data["summary"]["matched_acestream_channels"] == 0
        assert data["summary"]["creatable_rows"] == 0
        assert all(row["candidates"] == [] for row in data["rows"])

    def test_analyze_epg_matches_includes_scores_and_match_stages(self, client, seeded_match_data):
        response = client.post("/api/v1/tv-channels/analyze-epg-matches", json={"strictness": "balanced"})

        assert response.status_code == status.HTTP_200_OK
        rows = response.json()["rows"]
        xml_row = next(row for row in rows if row["epg_channel_xml_id"] == "xml-match-1")
        assert xml_row["best_match_type"] == "xml_id_exact"
        assert xml_row["best_match_confidence"] == "high"
        first_candidate = xml_row["candidates"][0]
        assert first_candidate["match_stage"] == "xml_id_exact"
        assert first_candidate["score"] == pytest.approx(1.0)

    def test_analyze_epg_matches_resolves_shared_acestream_candidates_deterministically(self, client, seeded_conflict_data):
        response = client.post("/api/v1/tv-channels/analyze-epg-matches", json={"strictness": "balanced"})

        assert response.status_code == status.HTTP_200_OK
        rows = response.json()["rows"]
        winner_row = next(row for row in rows if row["epg_channel_xml_id"] == "winner-id")
        loser_row = next(row for row in rows if row["epg_channel_xml_id"] == "loser-id")
        assert [candidate["acestream_channel_id"] for candidate in winner_row["candidates"]] == ["shared-candidate"]
        assert loser_row["candidates"] == []
        assert winner_row["is_creatable"] is True
        assert loser_row["is_creatable"] is False

    def test_analyze_epg_matches_rejects_workloads_over_budget(self, client, seeded_match_data, monkeypatch):
        monkeypatch.setattr("app.services.epg_match_service.MAX_ANALYSIS_COMPARISONS", 1)

        response = client.post("/api/v1/tv-channels/analyze-epg-matches", json={"strictness": "balanced"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "budget" in response.json()["detail"].lower()

    def test_analyze_epg_matches_marks_duplicate_existing_conflicts_as_not_creatable(self, client, seeded_match_data, db_session):
        epg_channel = seeded_match_data["epg_channels"]["xml_exact"]
        db_session.add_all([
            TVChannel(name="Duplicate Existing 1", epg_id=epg_channel.channel_xml_id),
            TVChannel(name="Duplicate Existing 2", epg_id=epg_channel.channel_xml_id),
        ])
        db_session.commit()

        response = client.post("/api/v1/tv-channels/analyze-epg-matches", json={"strictness": "balanced"})

        assert response.status_code == status.HTTP_200_OK
        row = next(row for row in response.json()["rows"] if row["epg_channel_xml_id"] == epg_channel.channel_xml_id)
        assert row["is_creatable"] is False
        assert row["existing_tv_channel_count"] == 2
        assert row["has_duplicate_existing_conflict"] is True


class TestTVChannelCreateFromEPGAnalysis:
    def test_create_from_epg_analysis_creates_tv_channels_and_associates_all_candidates(self, client, seeded_match_data):
        epg_channels = seeded_match_data["epg_channels"]

        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "balanced", "epg_channel_ids": [epg_channels["xml_exact"].id, epg_channels["multi_candidate"].id]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["created_count"] == 2
        assert data["associated_count"] == 3
        assert len(data["row_outcomes"]) == 2

        tv_channel_ids = [row["tv_channel_id"] for row in data["row_outcomes"] if row["status"] == "created"]
        associations = []
        for tv_channel_id in tv_channel_ids:
            asociated_response = client.get(f"/api/v1/tv-channels/{tv_channel_id}/acestreams")
            assert asociated_response.status_code == status.HTTP_200_OK
            associations.extend(asociated_response.json())
        assert len(associations) == 3

    def test_create_from_epg_analysis_revalidates_matches_server_side(self, client, seeded_match_data, db_session):
        epg_channel = seeded_match_data["epg_channels"]["fuzzy"]
        candidate = seeded_match_data["acestream_channels"][2]
        candidate.name = "Completely Different Name"
        db_session.commit()

        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "strict", "epg_channel_ids": [epg_channel.id]},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "no accepted matches" in response.json()["detail"].lower()

    def test_create_from_epg_analysis_reports_row_level_partial_success(self, client, seeded_match_data, db_session):
        duplicate_one = TVChannel(name="Duplicate One", epg_id=seeded_match_data["epg_channels"]["xml_exact"].channel_xml_id)
        duplicate_two = TVChannel(name="Duplicate Two", epg_id=seeded_match_data["epg_channels"]["xml_exact"].channel_xml_id)
        db_session.add_all([duplicate_one, duplicate_two])
        db_session.commit()

        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={
                "strictness": "balanced",
                "epg_channel_ids": [
                    seeded_match_data["epg_channels"]["xml_exact"].id,
                    seeded_match_data["epg_channels"]["multi_candidate"].id,
                ],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["created_count"] == 1
        assert data["skipped_count"] == 1
        assert any(row["status"] == "duplicate_existing_conflict" for row in data["row_outcomes"])
        assert any(row["status"] == "created" for row in data["row_outcomes"])

    def test_create_from_epg_analysis_enforces_candidate_uniqueness_across_created_rows(self, client, seeded_conflict_data):
        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "balanced", "epg_channel_ids": [seeded_conflict_data["winner"].id, seeded_conflict_data["loser"].id]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        created_rows = [row for row in data["row_outcomes"] if row["status"] == "created"]
        skipped_rows = [row for row in data["row_outcomes"] if row["status"] != "created"]
        assert len(created_rows) == 1
        assert len(skipped_rows) == 1

        tv_channel_id = created_rows[0]["tv_channel_id"]
        associated = client.get(f"/api/v1/tv-channels/{tv_channel_id}/acestreams")
        assert associated.status_code == status.HTTP_200_OK
        associated_ids = [row["id"] for row in associated.json()]
        assert associated_ids == ["shared-candidate"]

    def test_create_from_epg_analysis_limits_uniqueness_to_selected_rows(self, client, seeded_conflict_data):
        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "balanced", "epg_channel_ids": [seeded_conflict_data["loser"].id]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["created_count"] == 1
        assert data["failure_count"] == 0
        assert data["row_outcomes"][0]["status"] == "created"

        associated = client.get(f"/api/v1/tv-channels/{data['row_outcomes'][0]['tv_channel_id']}/acestreams")
        assert associated.status_code == status.HTTP_200_OK
        assert [row["id"] for row in associated.json()] == ["shared-candidate"]

    def test_create_from_epg_analysis_does_not_steal_existing_acestream_associations(self, client, seeded_match_data, db_session):
        protected_channel = TVChannel(name="Protected Existing", epg_id="protected-existing")
        db_session.add(protected_channel)
        db_session.flush()

        protected_acestream = seeded_match_data["acestream_channels"][0]
        protected_acestream.tv_channel_id = protected_channel.id
        db_session.commit()

        epg_channel = seeded_match_data["epg_channels"]["xml_exact"]
        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "balanced", "epg_channel_ids": [epg_channel.id]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["created_count"] == 0
        assert data["failure_count"] == 1
        assert data["row_outcomes"][0]["status"] == "failed"

        db_session.refresh(protected_acestream)
        assert protected_acestream.tv_channel_id == protected_channel.id
        assert db_session.query(TVChannel).filter(TVChannel.epg_id == epg_channel.channel_xml_id).all() == []

    def test_create_from_epg_analysis_rolls_back_failed_row_without_orphan_tv_channel(self, client, seeded_match_data, monkeypatch, db_session):
        original_assign = ChannelRepository.assign_acestreams_to_tv_channel
        failing_epg_id = seeded_match_data["epg_channels"]["multi_candidate"].channel_xml_id
        successful_epg_id = seeded_match_data["epg_channels"]["xml_exact"].channel_xml_id

        def fail_once_for_target(self, acestream_ids, tv_channel_id):
            tv_channel = self.get_tv_channel_by_id(tv_channel_id)
            if tv_channel and tv_channel.epg_id == failing_epg_id:
                raise RuntimeError("forced association failure")
            return original_assign(self, acestream_ids, tv_channel_id)

        monkeypatch.setattr(ChannelRepository, "assign_acestreams_to_tv_channel", fail_once_for_target)

        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={
                "strictness": "balanced",
                "epg_channel_ids": [
                    seeded_match_data["epg_channels"]["xml_exact"].id,
                    seeded_match_data["epg_channels"]["multi_candidate"].id,
                ],
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        failed_row = next(row for row in data["row_outcomes"] if row["epg_channel_id"] == seeded_match_data["epg_channels"]["multi_candidate"].id)
        assert failed_row["status"] == "failed"

        orphan = db_session.query(TVChannel).filter(TVChannel.epg_id == failing_epg_id).all()
        assert orphan == []

        successful_channel = db_session.query(TVChannel).filter(TVChannel.epg_id == successful_epg_id).one_or_none()
        assert successful_channel is not None

        associated = client.get(f"/api/v1/tv-channels/{successful_channel.id}/acestreams")
        assert associated.status_code == status.HTTP_200_OK
        assert [row["id"] for row in associated.json()] == [seeded_match_data["acestream_channels"][0].id]

    def test_create_from_epg_analysis_skips_existing_epg_id(self, client, seeded_match_data, db_session):
        existing = TVChannel(name="Existing", epg_id=seeded_match_data["epg_channels"]["xml_exact"].channel_xml_id)
        db_session.add(existing)
        db_session.commit()

        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "balanced", "epg_channel_ids": [seeded_match_data["epg_channels"]["xml_exact"].id]},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["created_count"] == 0
        assert data["skipped_count"] == 1
        assert data["row_outcomes"][0]["status"] == "skipped_existing"

    def test_create_from_epg_analysis_rejects_duplicate_existing_epg_id_conflicts(self, client, seeded_match_data, db_session):
        epg_id = seeded_match_data["epg_channels"]["xml_exact"].channel_xml_id
        db_session.add_all([TVChannel(name="Duplicate 1", epg_id=epg_id), TVChannel(name="Duplicate 2", epg_id=epg_id)])
        db_session.commit()

        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "balanced", "epg_channel_ids": [seeded_match_data["epg_channels"]["xml_exact"].id]},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["row_outcomes"][0]["status"] == "duplicate_existing_conflict"

    def test_create_from_epg_analysis_rejects_invalid_strictness(self, client, seeded_match_data):
        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "invalid", "epg_channel_ids": [seeded_match_data["epg_channels"]["xml_exact"].id]},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_from_epg_analysis_rejects_empty_epg_channel_ids(self, client):
        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "balanced", "epg_channel_ids": []},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_from_epg_analysis_rejects_when_revalidation_yields_no_matches(self, client, seeded_unmatched_data):
        unmatched_channel_id = seeded_unmatched_data["epg_channels"][0].id
        response = client.post(
            "/api/v1/tv-channels/create-from-epg-analysis",
            json={"strictness": "balanced", "epg_channel_ids": [unmatched_channel_id]},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "no accepted matches" in response.json()["detail"].lower()


class TestAssignAcestreamsToTVChannel:
    """Regression tests for ChannelRepository.assign_acestreams_to_tv_channel."""

    @staticmethod
    def _tv_channel(db_session, name):
        tv = TVChannel(name=f"{name}-{uuid.uuid4().hex[:8]}")
        db_session.add(tv)
        db_session.commit()
        return tv

    @staticmethod
    def _acestream(db_session, char, tv_channel_id=None):
        channel = AcestreamChannel(id=char * 40, name=f"channel-{char}",
                                   tv_channel_id=tv_channel_id)
        db_session.add(channel)
        db_session.commit()
        return channel

    def test_ignores_ids_not_yet_persisted(self, db_session):
        """IDs absent from the database are not a conflict.

        auto_create_tv_channels_from_epg assigns channels parsed from an M3U
        before they are inserted. Treating a missing row as "already
        associated" aborted the whole scrape of any source carrying tvg-id.
        """
        repo = ChannelRepository(db_session)
        tv = self._tv_channel(db_session, "not-persisted")
        persisted = self._acestream(db_session, "a")

        updated = repo.assign_acestreams_to_tv_channel(
            [persisted.id, "b" * 40], tv.id
        )

        assert updated == 1
        db_session.refresh(persisted)
        assert persisted.tv_channel_id == tv.id

    def test_reassigning_to_same_tv_channel_is_idempotent(self, db_session):
        """Re-running an assignment must not raise."""
        repo = ChannelRepository(db_session)
        tv = self._tv_channel(db_session, "idempotent")
        channel = self._acestream(db_session, "c")

        repo.assign_acestreams_to_tv_channel([channel.id], tv.id)
        repo.assign_acestreams_to_tv_channel([channel.id], tv.id)

        db_session.refresh(channel)
        assert channel.tv_channel_id == tv.id

    def test_raises_when_owned_by_another_tv_channel(self, db_session):
        """The real conflict still raises, and names the offending IDs."""
        repo = ChannelRepository(db_session)
        owner = self._tv_channel(db_session, "owner")
        other = self._tv_channel(db_session, "other")
        taken = self._acestream(db_session, "d", tv_channel_id=owner.id)

        with pytest.raises(ValueError) as excinfo:
            repo.assign_acestreams_to_tv_channel([taken.id], other.id)

        assert taken.id in str(excinfo.value)
