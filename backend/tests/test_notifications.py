"""Task notifications through one webhook (#41)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from app.services import notification_service


@pytest.fixture
def webhook(monkeypatch):
    """A real HTTP server on loopback that records each POST."""
    received, status = [], [200]

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = self.rfile.read(int(self.headers['Content-Length']))
            received.append({'path': self.path, 'type': self.headers['Content-Type'], 'json': json.loads(body)})
            self.send_response(status[0])
            self.end_headers()

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = 'http://127.0.0.1:%d/message?token=x' % server.server_address[1]
    monkeypatch.setattr(notification_service, 'webhook_url', lambda: url)
    try:
        yield received, status
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_a_finished_scrape_is_posted_as_json(webhook):
    received, _ = webhook
    assert notification_service.scraping_completed({'processed': 5, 'failures': 1}) is True
    [sent] = received
    assert sent['path'] == '/message?token=x' and sent['type'] == 'application/json'
    assert sent['json'] == {'event': 'url_scraping.completed', 'title': 'URL scraping finished',
                            'message': '5 URL(s) scraped, 1 failed', 'data': {'processed': 5, 'failures': 1}}


def test_a_finished_channel_check_says_how_many_are_online(webhook):
    received, _ = webhook
    notification_service.channel_status_completed({'checked': 10, 'online': 7, 'offline': 3, 'failed': 0, 'skipped': 2})
    assert received[0]['json']['message'] == '10 checked: 7 online, 3 offline, 0 failed'


def test_a_check_that_did_nothing_sends_nothing(webhook):
    received, _ = webhook
    notification_service.channel_status_completed({'checked': 0, 'message': 'No engine configured; status checks are disabled.'})
    assert received == []


def test_a_failure_names_the_error_type_not_its_text(webhook):
    """Exception text can carry URLs with credentials."""
    received, _ = webhook
    notification_service.task_failed('url_scraping', RuntimeError('http://user:secret@host/list.m3u'))
    sent = received[0]['json']
    assert sent['event'] == 'url_scraping.failed' and 'secret' not in json.dumps(sent)


def test_a_webhook_error_does_not_raise(webhook):
    received, status = webhook
    status[0] = 500
    assert notification_service.notify('x', 't', 'm') is False
    assert len(received) == 1


def test_an_unreachable_webhook_does_not_raise(monkeypatch):
    monkeypatch.setattr(notification_service, 'webhook_url', lambda: 'http://127.0.0.1:9/nowhere')
    assert notification_service.notify('x', 't', 'm') is False


def test_without_a_webhook_nothing_is_sent(monkeypatch):
    calls = []
    monkeypatch.setattr(notification_service, 'webhook_url', lambda: '')
    monkeypatch.setattr(notification_service.outbound_http, 'source_post_json', lambda *a, **k: calls.append(a))
    assert notification_service.notify('x', 't', 'm') is False and calls == []


def test_the_scraping_task_notifies_when_it_ends(monkeypatch):
    from app.tasks import url_scraping_task
    sent = []
    monkeypatch.setattr(url_scraping_task.notification_service, 'scraping_completed', lambda result: sent.append(result))
    monkeypatch.setattr(url_scraping_task.ScraperService, 'get_enabled_urls', lambda self: [])
    url_scraping_task.run_url_scraping_task()
    assert sent == [{'processed': 0, 'failures': 0}]


def test_the_api_saves_clears_and_rejects_the_webhook(client):
    assert client.get('/api/v1/config/notification_webhook_url').json()['value'] == ''
    response = client.put('/api/v1/config/notification_webhook_url', json={'value': ' https://gotify.lan/message?token=t '})
    assert response.status_code == 200 and response.json()['value'] == 'https://gotify.lan/•••'
    assert client.put('/api/v1/config/notification_webhook_url', json={'value': 'ftp://x'}).status_code == 422
    assert client.put('/api/v1/config/notification_webhook_url', json={'value': ''}).json()['value'] == ''


@pytest.mark.parametrize('url, shown', [
    ('https://gotify.lan/message?token=secret', 'https://gotify.lan/•••'),          # Gotify: in the query
    ('http://192.168.1.5:8123/api/webhook/secret', 'http://192.168.1.5:8123/•••'),  # Home Assistant: in the path
    ('https://api.telegram.org/botsecret/sendMessage', 'https://api.telegram.org/•••'),
    ('https://user:secret@hook.lan', 'https://hook.lan/•••'),
    ('https://hook.lan', 'https://hook.lan'),
])
def test_the_api_never_returns_the_secret(client, url, shown):
    """Secrets are never returned: only scheme and host are shown."""
    client.put('/api/v1/config/notification_webhook_url', json={'value': url})
    assert client.get('/api/v1/config/notification_webhook_url').json()['value'] == shown
    assert client.get('/api/v1/config/all').json()['settings']['notification_webhook_url'] == shown
    assert 'secret' not in client.get('/api/v1/config/all').text


def test_a_masked_url_cannot_be_saved_as_a_new_one(client):
    response = client.put('/api/v1/config/notification_webhook_url', json={'value': 'https://other.lan/•••'})
    assert response.status_code == 422


def test_saving_the_masked_value_keeps_the_real_url(client, db_session):
    from app.repositories.settings_repository import SettingsRepository
    client.put('/api/v1/config/notification_webhook_url', json={'value': 'https://gotify.lan/message?token=secret'})
    shown = client.get('/api/v1/config/notification_webhook_url').json()['value']
    assert client.put('/api/v1/config/notification_webhook_url', json={'value': shown}).status_code == 200
    db_session.expire_all()
    assert SettingsRepository(db_session).get_setting('notification_webhook_url') == 'https://gotify.lan/message?token=secret'


def test_the_test_button_needs_a_webhook(client):
    assert client.post('/api/v1/config/notification_webhook_url/test').status_code == 422


@pytest.mark.parametrize("reason,text", [("viewing", "playback active"), ("shutdown", "application stopping")])
def test_incomplete_channel_pass_reports_deferred_work(webhook, reason, text):
    received, _ = webhook
    result = {"checked": 1, "online": 1, "offline": 0, "failed": 0, "skipped": 0,
              "deferred": 2, "stop_reason": reason}
    assert notification_service.channel_status_completed(result)
    sent = received[0]["json"]
    assert sent["title"] == "Channel check incomplete"
    assert sent["message"] == f"1 checked: 1 online, 0 offline, 0 failed; 2 deferred ({text})"
    assert sent["data"] == result
