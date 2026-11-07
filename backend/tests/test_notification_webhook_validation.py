"""Webhook configuration remains readable and never commits malformed URLs."""
import pytest

from app.repositories.settings_repository import SettingsRepository
from app.services.config_service import ConfigService, MASK


VALID = "https://hooks.example/message?token=private"
INVALID = [
    "https://hooks.example:invalid/message",
    "https://hooks.example:65536/message",
    "http://hooks.example:0/message",
    "http://[broken",
    "https://",
    "https:///message",
    "https://user:private@",
    "https://bad host/message",
    "https://hooks.example/a\nb",
    "https://hooks.example/a\tb",
    "https://hooks.example/\x00private",
    "https://hooks.example/\x7fprivate",
    "https://hooks.example\\@other.example/message",
    "https://hooks.example/message#private",
    "ftp://hooks.example/message",
]


@pytest.mark.parametrize("value", INVALID)
def test_invalid_url_is_rejected_before_persistence(client, db_session, value):
    repository = SettingsRepository(db_session)
    repository.set_setting(repository.NOTIFICATION_WEBHOOK_URL, VALID)

    response = client.put("/api/v1/config/notification_webhook_url", json={"value": value})

    assert response.status_code == 422
    assert "private" not in response.text
    db_session.expire_all()
    assert repository.get_setting(repository.NOTIFICATION_WEBHOOK_URL) == VALID
    assert client.get("/api/v1/config/notification_webhook_url").status_code == 200
    assert client.get("/api/v1/config/all").status_code == 200


@pytest.mark.parametrize("value", INVALID)
def test_old_invalid_url_can_be_read_replaced_and_cleared(client, db_session, value):
    repository = SettingsRepository(db_session)
    repository.set_setting(repository.NOTIFICATION_WEBHOOK_URL, value)

    response = client.get("/api/v1/config/notification_webhook_url")
    assert response.status_code == 200
    assert response.json()["value"] == MASK
    response = client.get("/api/v1/config/all")
    assert response.status_code == 200
    assert response.json()["settings"]["notification_webhook_url"] == MASK
    assert "private" not in response.text
    assert client.put("/api/v1/config/notification_webhook_url", json={"value": MASK}).status_code == 422

    assert client.put("/api/v1/config/notification_webhook_url", json={"value": VALID}).status_code == 200
    db_session.expire_all()
    assert repository.get_setting(repository.NOTIFICATION_WEBHOOK_URL) == VALID

    repository.set_setting(repository.NOTIFICATION_WEBHOOK_URL, value)
    assert client.put("/api/v1/config/notification_webhook_url", json={"value": ""}).status_code == 200
    db_session.expire_all()
    assert repository.get_setting(repository.NOTIFICATION_WEBHOOK_URL) == ""


@pytest.mark.parametrize(("url", "masked"), [
    ("http://localhost:8123/api/webhook/private", "http://localhost:8123/•••"),
    ("https://[2001:db8::1]:8443/message?token=private", "https://[2001:db8::1]:8443/•••"),
    ("https://user:private@hooks.example/path", "https://hooks.example/•••"),
    ("https://hooks.example/%2fSigned?sig=A%2BB&key=x+y", "https://hooks.example/•••"),
    ("https://hooks.example:443", "https://hooks.example:443"),
])
def test_valid_urls_keep_exact_bytes_and_mask_secrets(client, db_session, url, masked, monkeypatch):
    # Saving settings must not require that a LAN/offline host resolves.
    monkeypatch.setattr("socket.getaddrinfo", lambda *a, **k: pytest.fail("Unexpected DNS lookup"))
    response = client.put("/api/v1/config/notification_webhook_url", json={"value": f" {url} "})
    assert response.status_code == 200
    assert response.json()["value"] == masked
    db_session.expire_all()
    repository = SettingsRepository(db_session)
    assert repository.get_setting(repository.NOTIFICATION_WEBHOOK_URL) == url
    assert client.put("/api/v1/config/notification_webhook_url", json={"value": masked}).status_code == 200
    db_session.expire_all()
    assert repository.get_setting(repository.NOTIFICATION_WEBHOOK_URL) == url


def test_service_validation_also_protects_non_api_callers(db_session):
    from fastapi import HTTPException

    service = ConfigService(SettingsRepository(db_session))
    with pytest.raises(HTTPException) as exc:
        service.set_notification_webhook_url("http://[broken")
    assert exc.value.status_code == 422
