"""
Tests for the playlist refresh=true trigger (v1 parity: async fire-and-forget)
and TaskService.run_task_now.
"""

import threading
import time

from fastapi import status

from app.services.task_service import TaskService


class TestPlaylistRefreshParam:
    """refresh=true triggers the url_scraping task without blocking."""

    def test_refresh_triggers_url_scraping(self, client, seed_channels, monkeypatch):
        from app.api.endpoints import playlists as playlists_module

        calls = []
        monkeypatch.setattr(
            playlists_module.task_service, "run_task_now",
            lambda job_id: calls.append(job_id) or "triggered",
        )

        response = client.get("/api/v1/playlists/m3u?refresh=true")
        assert response.status_code == status.HTTP_200_OK
        assert response.text.startswith("#EXTM3U")
        assert calls == ["url_scraping"]

    def test_no_refresh_does_not_trigger(self, client, seed_channels, monkeypatch):
        from app.api.endpoints import playlists as playlists_module

        calls = []
        monkeypatch.setattr(
            playlists_module.task_service, "run_task_now",
            lambda job_id: calls.append(job_id) or "triggered",
        )

        response = client.get("/api/v1/playlists/m3u")
        assert response.status_code == status.HTTP_200_OK
        assert calls == []

    def test_refresh_on_legacy_route(self, client, seed_channels, monkeypatch):
        from app.api.endpoints import playlists as playlists_module

        calls = []
        monkeypatch.setattr(
            playlists_module.task_service, "run_task_now",
            lambda job_id: calls.append(job_id) or "triggered",
        )

        response = client.get("/playlist.m3u?refresh=true")
        assert response.status_code == status.HTTP_200_OK
        assert calls == ["url_scraping"]

    def test_refresh_failure_does_not_break_playlist(self, client, seed_channels, monkeypatch):
        from app.api.endpoints import playlists as playlists_module

        def boom(job_id):
            raise RuntimeError("scheduler exploded")

        monkeypatch.setattr(playlists_module.task_service, "run_task_now", boom)

        response = client.get("/api/v1/playlists/m3u?refresh=true")
        assert response.status_code == status.HTTP_200_OK
        assert response.text.startswith("#EXTM3U")


class TestRunTaskNow:
    """TaskService.run_task_now trigger/guard semantics."""

    def test_unavailable_when_scheduler_stopped(self):
        service = TaskService()
        assert service.run_task_now("url_scraping") == "unavailable"

    def test_unavailable_for_unknown_job(self):
        service = TaskService()
        service.start()
        try:
            assert service.run_task_now("nope") == "unavailable"
        finally:
            service.shutdown()

    def test_already_running_guard(self):
        service = TaskService()
        state = service._ensure_task_state("url_scraping")
        state["status"] = "running"
        assert service.run_task_now("url_scraping") == "already_running"

    def test_triggered_runs_job_immediately(self):
        service = TaskService()
        ran = threading.Event()
        service.start()
        try:
            service.add_interval_task(lambda: ran.set(), seconds=3600, job_id="probe")
            assert service.run_task_now("probe") == "triggered"
            assert ran.wait(timeout=10), "job did not run after immediate trigger"
        finally:
            service.shutdown()
