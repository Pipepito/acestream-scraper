"""
Integration tests for Channel endpoints
"""

import pytest
import uuid
from unittest.mock import AsyncMock
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

    def test_get_channels_includes_linked_tv_favorite_metadata(self, client, seed_channels, seed_tv_channels, db_session):
        """Test getting channels includes linked TV metadata for favorites UI."""
        seed_tv_channels[0].name = 'Arena TV'
        seed_tv_channels[0].is_favorite = True
        seed_channels[0].tv_channel_id = seed_tv_channels[0].id
        db_session.commit()

        response = client.get('/api/v1/channels/')

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        alpha = next(item for item in data['items'] if item['id'] == seed_channels[0].id)
        assert alpha['tv_channel_id'] == seed_tv_channels[0].id
        assert alpha['tv_channel_name'] == 'Arena TV'
        assert alpha['tv_channel_is_favorite'] is True

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

    def test_bulk_activate_channels_endpoint(self, client, seed_channels):
        """Test bulk activate/deactivate endpoint updates channels in one call."""
        payload = {
            "acestreamchannel_ids": [channel.id for channel in seed_channels],
            "active": False,
        }
        response = client.post("/api/v1/channels/bulk_activate", json=payload)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == len(seed_channels)
        assert all(item["is_active"] is False for item in data)


class TestChannelStatusEndpoints:
    """Test channel status checking endpoints."""

    @pytest.fixture(autouse=True)
    def engine_transport(self, monkeypatch):
        from app.services.channel_status_service import ChannelStatusService
        from app.services.probe_queue import ProbeQueue
        # Exercise the actual queue, readiness and persistence without a live
        # engine or real recovery/cooldown waits in endpoint contract tests.
        async def fetch(_self, url, params, timeout):
            if url.endswith('/server/api'):
                return 200, {'result': {'version': {}}}, None
            assert url.endswith('/ace/getstream')
            return 200, {'error': 'Stream unavailable', 'response': {}}, None
        monkeypatch.setattr(ChannelStatusService, '_fetch_engine_response', fetch)
        monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0, outage_backoff=0))

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

    @pytest.mark.parametrize("outcome,code", [("triggered", 200), ("already_running", 200), ("unavailable", 503)])
    def test_run_existing_status_job(self, client, monkeypatch, outcome, code, db_session):
        from app.repositories.settings_repository import SettingsRepository
        SettingsRepository(db_session).set_setting("ace_engine_url", "http://engine.test:6878")
        from unittest.mock import Mock
        from app.services.task_service import task_service
        trigger = Mock(return_value=outcome)
        monkeypatch.setattr(task_service, "run_task_now", trigger)
        response = client.post("/api/v1/background-tasks/channel_status/run")
        assert response.status_code == code
        trigger.assert_called_once_with("channel_status")
        if code == 200:
            assert response.json()["status"] == outcome

    def test_manual_bulk_endpoint_removed(self, client):
        assert client.post("/api/v1/channels/check_status_all").status_code in (404, 405)

    def test_engine_outage_preserves_single_channel_status(self, client, seed_channels, monkeypatch, db_session):
        from app.services.channel_status_service import ChannelStatusService
        channel = seed_channels[0]
        before = (channel.is_online, channel.last_checked)
        monkeypatch.setattr(ChannelStatusService, '_wait_for_engine', AsyncMock(return_value=False))
        response = client.post(f'/api/v1/channels/{channel.id}/check_status')
        assert response.status_code == 200
        assert response.json()['status'] == 'skipped'
        db_session.refresh(channel)
        assert (channel.is_online, channel.last_checked) == before

    def test_export_csv_is_reachable(self, client, seed_channels):
        """The CSV export must not be shadowed by the /{acestreamchannel_id} route."""
        response = client.get("/api/v1/acestream-channels/export_csv")
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"].startswith("text/csv")
        lines = [line for line in response.text.splitlines() if line.strip()]
        assert lines[0].startswith("id,name,source_url")
        assert len(lines) == 1 + 3

    def test_export_csv_includes_every_channel(self, client, db_session):
        """The export is a backup: it must not stop at the list endpoint's default page size."""
        from app.models.models import AcestreamChannel

        for index in range(150):
            db_session.add(AcestreamChannel(id=f"{index:040x}", name=f"Bulk channel {index:03d}", is_active=True))
        db_session.commit()

        response = client.get("/api/v1/acestream-channels/export_csv")
        assert response.status_code == status.HTTP_200_OK
        lines = [line for line in response.text.splitlines() if line.strip()]
        assert len(lines) == 1 + 150

    def test_unknown_filters_are_ignored_not_500(self, client, seed_channels):
        """Acestream channels have no country/language columns; stray params must not crash the list."""
        response = client.get("/api/v1/acestream-channels/?country=ES&language=es")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 3

    def test_legacy_tv_alias_is_gone(self, client):
        """/acestream-channels/tv/ pointed at a method that never existed (always 500)."""
        response = client.get("/api/v1/acestream-channels/tv/")
        assert response.status_code == status.HTTP_404_NOT_FOUND

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


def test_scheduled_status_scan_has_no_hundred_channel_limit(db_session, monkeypatch):
    from unittest.mock import Mock
    from app.models.models import AcestreamChannel
    from app.tasks import channel_status_task as task
    from app.repositories.settings_repository import SettingsRepository
    SettingsRepository(db_session).set_setting("ace_engine_url", "http://engine.test:6878")
    db_session.add_all([AcestreamChannel(id=f'{i:040x}', name=f'Stream {i}', is_active=True) for i in range(151)])
    db_session.add(AcestreamChannel(id='f' * 40, name='Hidden', is_active=False))
    db_session.commit()
    monkeypatch.setattr(task, 'SessionLocal', lambda: db_session)
    monkeypatch.setattr(task.task_service.shutdown_event, 'is_set', Mock(return_value=False))
    check = AsyncMock(return_value={'status': 'skipped'})
    monkeypatch.setattr(task.ChannelStatusService, 'check_channel_status', check)
    result = task.run_channel_status_task()
    assert check.call_count == 151
    assert result == {'checked': 0, 'skipped': 151, 'failed': 0}


def test_retired_manual_status_is_not_exposed(monkeypatch):
    from app.services.background_task_status_service import BackgroundTaskStatusService
    service = BackgroundTaskStatusService()
    monkeypatch.setattr(service._task_service, 'get_jobs', lambda: [])
    monkeypatch.setattr(service._task_service, 'get_task_states', lambda: {'manual_channel_status': {}, 'channel_status': {}})
    monkeypatch.setattr(service._task_service, 'get_task_state', lambda name: {})
    assert [s.task_name for s in service.get_all_statuses()] == ['channel_status']
