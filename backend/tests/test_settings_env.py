"""Environment parsing contract for Settings (things the docs promise)."""
from __future__ import annotations

import inspect
import re
from pathlib import Path

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


MEDIA_SECTION_MARKER = "# --- Media integrations"

# Only a floor for the set derived from Settings below: if the block parser ever
# matched nothing, the per-knob loop would pass vacuously. The knobs actually
# checked are whatever Settings declares, not this list.
SPEC_MANDATED_MEDIA_ENV = {
    "PUBLIC_BASE_URL",
    "TUNER_ALLOWED_NETWORKS",
    "PLAYER_HLS_DIR",
    "PLAYER_MAX_SESSIONS",
    "PLAYER_START_TIMEOUT_SECONDS",
    "FORWARDED_ALLOW_IPS",
    "FFMPEG_BINARY_PATH",
    "MEDIA_SERVER_MIN_REFRESH_MINUTES",
}


def _media_env_defaults() -> dict[str, str]:
    """Media-integration knobs declared by Settings, as name -> shell-rendered default.

    The names come from the class body's media block and the values from
    ``Settings.model_fields``, so a knob added to Settings is covered by the
    entrypoint guard below without editing this test.
    """
    _, marker, media_block = inspect.getsource(Settings).partition(MEDIA_SECTION_MARKER)
    assert marker, f"{MEDIA_SECTION_MARKER!r} not found in the Settings source"

    names: list[str] = []
    for line in media_block.splitlines()[1:]:
        if line.strip().startswith(("@", "def ")):  # end of the field block
            break
        match = re.match(r"\s+([A-Z][A-Z0-9_]*)\s*:", line)
        if match:
            names.append(match.group(1))

    defaults: dict[str, str] = {}
    for name in names:
        field = Settings.model_fields.get(name)
        assert field is not None, f"{name} was parsed from the media block but is not a Settings field"
        assert not field.is_required(), f"{name} has no default for entrypoint.sh to mirror"
        defaults[name] = "" if field.default is None else str(field.default)
    return defaults


def test_entrypoint_defaults_match_settings_defaults() -> None:
    """entrypoint.sh must export every media knob with Settings' own default (spec 4.5)."""
    entrypoint = (Path(__file__).resolve().parents[2] / "entrypoint.sh").read_text(encoding="utf-8")
    knobs = _media_env_defaults()

    assert SPEC_MANDATED_MEDIA_ENV <= set(knobs), (
        f"media block parser found {sorted(knobs)}, expected at least {sorted(SPEC_MANDATED_MEDIA_ENV)}"
    )
    missing = [
        expected
        for name, default in knobs.items()
        if (expected := f'export {name}="${{{name}:-{default}}}"') not in entrypoint
    ]
    assert not missing, "entrypoint.sh does not mirror Settings defaults:\n" + "\n".join(missing)
