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
