"""Environment parsing contract for Settings (things the docs promise)."""
from __future__ import annotations

import pytest

from app.config.settings import Settings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://localhost:3000", ["http://localhost:3000"]),
        ("http://localhost:3000, http://127.0.0.1:3000", ["http://localhost:3000", "http://127.0.0.1:3000"]),
        ('["http://a.test", "http://b.test"]', ["http://a.test", "http://b.test"]),
        ("", []),
    ],
)
def test_cors_origins_accepts_comma_separated_and_json_env(monkeypatch: pytest.MonkeyPatch, raw: str, expected: list[str]) -> None:
    monkeypatch.setenv("CORS_ORIGINS", raw)
    settings = Settings(_env_file=None)
    assert settings.CORS_ORIGINS == expected


def test_cors_origins_default_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert Settings(_env_file=None).CORS_ORIGINS == ["http://localhost:3000"]


DEFAULT_TUNER_NETWORKS = "127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10"
DEFAULT_FORWARDED_ALLOW_IPS = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"


def test_media_integration_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "PUBLIC_BASE_URL", "FORWARDED_ALLOW_IPS", "TUNER_ALLOWED_NETWORKS", "PLAYER_HLS_DIR",
        "PLAYER_MAX_SESSIONS", "PLAYER_START_TIMEOUT_SECONDS", "FFMPEG_BINARY_PATH",
        "MEDIA_SERVER_MIN_REFRESH_MINUTES",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = Settings(_env_file=None)
    assert settings.PUBLIC_BASE_URL == ""
    assert settings.FORWARDED_ALLOW_IPS == DEFAULT_FORWARDED_ALLOW_IPS
    assert settings.TUNER_ALLOWED_NETWORKS == DEFAULT_TUNER_NETWORKS
    assert settings.PLAYER_HLS_DIR == "/tmp/acestream-player"
    assert settings.PLAYER_MAX_SESSIONS == 3
    assert settings.PLAYER_START_TIMEOUT_SECONDS == 45
    assert settings.FFMPEG_BINARY_PATH == ""
    assert settings.MEDIA_SERVER_MIN_REFRESH_MINUTES == 30


def test_media_integration_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://scraper.example.com")
    monkeypatch.setenv("PLAYER_MAX_SESSIONS", "5")
    monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "*")
    settings = Settings(_env_file=None)
    assert settings.PUBLIC_BASE_URL == "https://scraper.example.com"
    assert settings.PLAYER_MAX_SESSIONS == 5
    assert settings.TUNER_ALLOWED_NETWORKS == "*"
