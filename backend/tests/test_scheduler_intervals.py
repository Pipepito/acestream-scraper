"""Scheduler intervals follow the stored settings instead of hard-coded seconds."""
from __future__ import annotations

from unittest.mock import MagicMock

from app.services.task_service import TaskService


def test_reschedule_task_changes_the_interval_and_state():
    service = TaskService()
    service.start()
    try:
        service.add_interval_task(lambda: None, seconds=3600, job_id="x")
        assert service.reschedule_task("x", 7200) is True
        assert service.get_task_state("x")["interval_seconds"] == 7200
        assert service.scheduler.get_job("x").trigger.interval.total_seconds() == 7200
        assert service.reschedule_task("missing", 60) is False
    finally:
        service.shutdown()


def test_put_rescrape_interval_reschedules_url_scraping(client, monkeypatch):
    reschedule = MagicMock(return_value=True)
    monkeypatch.setattr("app.api.endpoints.config.task_service.reschedule_task", reschedule)

    response = client.put("/api/v1/config/rescrape_interval", json={"value": "2"})

    assert response.status_code == 200
    reschedule.assert_called_once_with("url_scraping", 2 * 3600)
    assert client.get("/api/v1/config/rescrape_interval").json()["value"] == "2"


def test_epg_refresh_interval_round_trips_and_reschedules(client, monkeypatch):
    reschedule = MagicMock(return_value=True)
    monkeypatch.setattr("app.api.endpoints.config.task_service.reschedule_task", reschedule)

    assert client.get("/api/v1/config/epg_refresh_interval").json() == {"key": "epg_refresh_interval", "value": "6"}
    response = client.put("/api/v1/config/epg_refresh_interval", json={"value": "3"})
    assert response.status_code == 200
    reschedule.assert_called_once_with("epg_refresh", 3 * 3600)
    assert client.get("/api/v1/config/epg_refresh_interval").json()["value"] == "3"

    bad = client.put("/api/v1/config/epg_refresh_interval", json={"value": "0"})
    assert bad.status_code == 422
