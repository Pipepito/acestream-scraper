"""Public base URL resolution (spec 4.3)."""
import pytest
from fastapi import status

from app.config.settings import get_settings


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_request_derived_url_when_unset(alembic_client, clean_env):
    body = alembic_client.get("/api/v1/system/public-url").json()
    assert body == {"url": "http://testserver", "source": "request", "warnings": ["unset"]}


def test_setting_wins_and_strips_slash(alembic_client, clean_env):
    put = alembic_client.put("/api/v1/config/public_base_url", json={"value": "https://scraper.example.com/"})
    assert put.status_code == status.HTTP_200_OK
    assert put.json()["value"] == "https://scraper.example.com"
    body = alembic_client.get("/api/v1/system/public-url").json()
    assert body["url"] == "https://scraper.example.com"
    assert body["source"] == "setting"
    assert body["warnings"] == ["proxied"]  # setting host differs from the request host


def test_forwarded_headers_change_source(alembic_client, clean_env, monkeypatch):
    # The test client peer is "testclient"; trust it for this test.
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "testclient")
    get_settings.cache_clear()
    import main
    from app.middleware.forwarded import ForwardedHeadersMiddleware, parse_trusted
    # Rebuild the middleware stack with the new trust list (add_middleware is import-time).
    layers = [layer for layer in main.app.user_middleware if layer.cls is ForwardedHeadersMiddleware]
    original_trusted = [layer.kwargs["trusted"] for layer in layers]
    for layer in layers:
        layer.kwargs["trusted"] = parse_trusted("testclient")
    main.app.middleware_stack = None  # force rebuild
    try:
        body = alembic_client.get(
            "/api/v1/system/public-url",
            headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "scraper.example.com"},
        ).json()
        assert body["url"] == "https://scraper.example.com"
        assert body["source"] == "forwarded"
        assert body["warnings"] == ["unset"]
    finally:
        # Restore the captured lists even when an assertion above fails, so no later
        # test in the session inherits a stack that trusts "testclient".
        for layer, trusted in zip(layers, original_trusted):
            layer.kwargs["trusted"] = trusted
        main.app.middleware_stack = None


@pytest.mark.parametrize("value", ["http://localhost:8000", "http://127.0.0.1:8000", "http://172.17.0.2:8000", "http://192.168.65.1:8000"])
def test_warnings_for_unreachable_hosts(alembic_client, clean_env, value):
    alembic_client.put("/api/v1/config/public_base_url", json={"value": value})
    body = alembic_client.get("/api/v1/system/public-url").json()
    expected = "localhost" if "localhost" in value or "127.0.0.1" in value else "docker-internal"
    assert expected in body["warnings"]


@pytest.mark.parametrize(
    "bad",
    [
        "scraper.example.com",
        "ftp://x",
        "http://host/path",
        "http://host?x=1",
        "http://user:pw@host",
        "http://[::1",  # urlsplit raises ValueError("Invalid IPv6 URL") on the unbalanced bracket
        "http://host:notaport",
    ],
)
def test_invalid_public_base_url_is_422(alembic_client, clean_env, bad):
    response = alembic_client.put("/api/v1/config/public_base_url", json={"value": bad})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_empty_value_clears_the_override(alembic_client, clean_env):
    alembic_client.put("/api/v1/config/public_base_url", json={"value": "http://scraper.lan:8000"})
    response = alembic_client.put("/api/v1/config/public_base_url", json={"value": ""})
    assert response.status_code == status.HTTP_200_OK
    assert alembic_client.get("/api/v1/system/public-url").json()["source"] == "request"


def test_env_seeds_the_setting(alembic_client, monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "http://seeded.lan:8000")
    get_settings.cache_clear()
    try:
        body = alembic_client.get("/api/v1/config/public_base_url").json()
        assert body == {"key": "public_base_url", "value": "http://seeded.lan:8000"}
    finally:
        get_settings.cache_clear()


def test_generic_key_routes_serve_public_base_url(alembic_client, clean_env):
    assert alembic_client.put("/api/v1/config/public_base_url", json={"value": "http://a.lan"}).status_code == 200
    assert alembic_client.get("/api/v1/config/public_base_url").json()["value"] == "http://a.lan"


@pytest.mark.parametrize(
    "seeded,expected",
    [
        ("https://scraper.example.com/", "https://scraper.example.com"),  # canonicalised
        ("scraper.example.com", ""),  # rejected by the same rule the API applies
        ("http://[::1", ""),
    ],
)
def test_env_seed_is_normalized(alembic_client, monkeypatch, seeded, expected):
    monkeypatch.setenv("PUBLIC_BASE_URL", seeded)
    get_settings.cache_clear()
    try:
        body = alembic_client.get("/api/v1/config/public_base_url").json()
        assert body == {"key": "public_base_url", "value": expected}
    finally:
        get_settings.cache_clear()


def test_invalid_env_seed_does_not_become_the_public_url(alembic_client, monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "scraper.example.com")
    get_settings.cache_clear()
    try:
        body = alembic_client.get("/api/v1/system/public-url").json()
        assert body == {"url": "http://testserver", "source": "request", "warnings": ["unset"]}
    finally:
        get_settings.cache_clear()
