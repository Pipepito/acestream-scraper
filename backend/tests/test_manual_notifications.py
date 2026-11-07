"""Explicit user actions notify once, without leaking upstream details."""
import asyncio
import threading
from datetime import datetime, timezone

import pytest

from app.services import notification_service
from app.services.channel_status_service import ChannelStatusService
from app.services.scraper_service import ScraperService


@pytest.fixture
def sent(monkeypatch):
    events = []

    def notify(event, title, message, data=None):
        events.append({"event": event, "title": title, "message": message, "data": data})
        return True

    monkeypatch.setattr(notification_service, "notify", notify)
    return events


@pytest.mark.parametrize("run_async", [False, True])
@pytest.mark.parametrize("status", ["OK", "error: upstream details"])
def test_manual_scrape_notifies_once(client, monkeypatch, sent, run_async, status):
    async def scrape(*args):
        return [], status

    monkeypatch.setattr(ScraperService, "scrape_url", scrape)
    response = client.post("/api/v1/scrapers/scrape", json={
        "url": "https://source.example/list?token=private",
        "url_type": "regular", "run_async": run_async,
    })

    assert response.status_code == 200
    assert len(sent) == 1
    assert sent[0]["event"] == "url_scraping.completed"
    assert sent[0]["data"] == {
        "processed": 1, "failures": int(status.startswith("error")), "channels": 0,
        "import_exclusions": {"excluded_candidates": 0},
    }
    assert "private" not in str(sent)
    assert "upstream details" not in str(sent)


@pytest.mark.parametrize("batch", [False, True])
def test_saved_source_actions_send_one_summary(client, monkeypatch, sent, batch):
    async def scrape(*args):
        return [], "OK"

    monkeypatch.setattr(ScraperService, "scrape_url", scrape)
    source_ids = []
    for name in ("one", "two"):
        response = client.post("/api/v1/scrapers/urls", json={
            "url": f"https://source.example/{name}.m3u", "url_type": "regular",
        })
        assert response.status_code == 201
        source_ids.append(response.json()["id"])

    path = "/api/v1/scrapers/urls/scrape_all" if batch else f"/api/v1/scrapers/urls/{source_ids[0]}/scrape"
    assert client.post(path).status_code == 200
    assert len(sent) == 1
    assert sent[0]["data"]["processed"] == (2 if batch else 1)


def test_failed_manual_scrape_notifies_without_exception_text(client, monkeypatch, sent):
    async def scrape(*args):
        raise RuntimeError("https://source.example/list?token=private")

    monkeypatch.setattr(ScraperService, "scrape_url", scrape)
    response = client.post("/api/v1/scrapers/scrape", json={
        "url": "https://source.example/list", "url_type": "regular",
    })
    assert response.status_code == 502
    assert len(sent) == 1
    assert sent[0]["event"] == "url_scraping.failed"
    assert sent[0]["data"] == {"task": "url_scraping", "error": "RuntimeError"}
    assert "private" not in str(sent)


@pytest.mark.parametrize("status", ["online", "offline", "skipped"])
@pytest.mark.parametrize("prefix", ["/api/v1/channels", "/api/v1/acestream-channels"])
def test_individual_check_notifies_only_when_checked(
    client, seed_channels, monkeypatch, sent, status, prefix,
):
    channel = seed_channels[0]

    async def check(*args):
        return {
            "channel_id": channel.id, "status": status, "is_online": status == "online",
            "network_status": "found", "last_checked": datetime.now(timezone.utc),
            "message": "upstream details", "error": "secret",
        }

    monkeypatch.setattr(ChannelStatusService, "check_channel_status", check)
    response = client.post(f"{prefix}/{channel.id}/check_status")
    assert response.status_code == 200
    assert response.json()["status"] == status
    if status == "skipped":
        assert sent == []
    else:
        assert len(sent) == 1
        assert sent[0]["event"] == "channel_check.completed"
        assert sent[0]["data"] == {
            "channel_id": channel.id, "status": status, "is_online": status == "online",
            "network_status": "found",
        }
        assert "secret" not in str(sent)
        assert "upstream details" not in str(sent)


def test_missing_channel_does_not_notify(client, sent):
    assert client.post("/api/v1/channels/missing/check_status").status_code == 404
    assert sent == []


def test_manual_check_exception_notifies_and_still_raises(db_session, seed_channels, monkeypatch, sent):
    async def check(*args):
        raise RuntimeError("private")

    monkeypatch.setattr(ChannelStatusService, "check_channel_status", check)
    with pytest.raises(RuntimeError, match="private"):
        asyncio.run(ChannelStatusService(db_session).check_channel_status_manually(seed_channels[0]))
    assert len(sent) == 1
    assert sent[0]["event"] == "channel_check.failed"
    assert sent[0]["data"] == {"channel_id": seed_channels[0].id, "error": "RuntimeError"}
    assert "private" not in str(sent)


def test_cancellation_is_not_reported_as_a_failed_check(db_session, seed_channels, monkeypatch, sent):
    async def check(*args):
        raise asyncio.CancelledError()

    monkeypatch.setattr(ChannelStatusService, "check_channel_status", check)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(ChannelStatusService(db_session).check_channel_status_manually(seed_channels[0]))
    assert sent == []


def test_delivery_runs_off_the_manual_job_event_loop(monkeypatch, sent):
    from app.services import manual_job_service

    monkeypatch.setattr(manual_job_service.task_service, "set_manual_state", lambda *args: None)
    monkeypatch.setattr(manual_job_service.task_service, "persist_current_state", lambda *args: None)
    delivery_threads = []
    monkeypatch.setattr(notification_service, "scraping_completed",
                        lambda result: delivery_threads.append(threading.get_ident()))

    async def scrape():
        return [], "OK"

    event_loop_thread = threading.get_ident()
    assert asyncio.run(manual_job_service.run_manual_job("url_scraping", scrape)) == ([], "OK")
    assert len(delivery_threads) == 1
    assert delivery_threads[0] != event_loop_thread


def test_failed_webhook_does_not_fail_the_manual_action(client, monkeypatch):
    async def scrape(*args):
        return [], "OK"

    monkeypatch.setattr(ScraperService, "scrape_url", scrape)
    monkeypatch.setattr(notification_service, "webhook_url", lambda: "http://hook.example/")

    def fail(*args):
        raise RuntimeError("private")

    monkeypatch.setattr(notification_service.url_guard, "validate_outbound_url", fail)
    response = client.post("/api/v1/scrapers/scrape", json={
        "url": "https://source.example/list", "url_type": "regular",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_scheduled_channel_pass_sends_only_its_summary(
    db_session, seed_channels, monkeypatch, sent,
):
    from app.tasks import channel_status_task

    async def check(self, channel, **kwargs):
        return {"channel_id": channel.id, "status": "online", "is_online": True}

    monkeypatch.setattr(channel_status_task, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(ChannelStatusService, "_get_engine_url", lambda self: "http://engine/")
    monkeypatch.setattr(ChannelStatusService, "check_channel_status", check)
    monkeypatch.setattr(channel_status_task.task_service.shutdown_event, "is_set", lambda: False)
    result = channel_status_task.run_channel_status_task()
    assert result["checked"] == 3
    assert [event["event"] for event in sent] == ["channel_status.completed"]
