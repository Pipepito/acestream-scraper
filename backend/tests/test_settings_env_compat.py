"""Legacy aliases stay retired regardless of the release version."""
import ast
from pathlib import Path
import pytest
from app.config.settings import Settings

RETIRED = {
    "SCRAPER_DB_URL": "DATABASE_URL", "LEGACY_DB_URL": "LEGACY_DATABASE_URL",
    "ZERONET_BASE_URL": "ZERONET_URL", "CORS_ALLOW_ORIGINS": "CORS_ORIGINS",
    "FRONTEND_STATIC_DIR": "FRONTEND_BUILD_PATH", "ACESTREAM_ENGINE_URL": "ACE_ENGINE_URL",
}

@pytest.mark.parametrize("legacy,canonical", RETIRED.items())
def test_retired_names_cannot_override_defaults_or_canonical_settings(monkeypatch, legacy, canonical):
    monkeypatch.delenv(canonical, raising=False)
    monkeypatch.setenv(legacy, "http://retired.invalid")
    settings = Settings(_env_file=None)
    assert getattr(settings, canonical) == Settings.model_fields[canonical].default
    monkeypatch.setenv(canonical, 'https://canonical.example' if canonical != 'CORS_ORIGINS' else '["https://canonical.example"]')
    assert 'canonical.example' in str(getattr(Settings(_env_file=None), canonical))


def test_alias_shim_and_runtime_consumers_stay_absent():
    root = Path(__file__).resolve().parents[1]
    banned = set(RETIRED) | {"ENABLE_LEGACY_ENV_ALIASES", "LEGACY_ENV_ALIAS_MAP", "apply_legacy_env_aliases", "get_env_compat_events"}
    for path in [root / 'main.py', *sorted((root / 'app').rglob('*.py'))]:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert node.value not in banned, str(path)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                assert node.name not in banned, str(path)


def test_engine_url_default_follows_env(monkeypatch):
    """A services-off container must reach the engine named by ACE_ENGINE_URL before anyone opens Settings."""
    import importlib
    from app.repositories import settings_repository

    monkeypatch.setenv("ACE_ENGINE_URL", "http://engine:6878")
    reloaded = importlib.reload(settings_repository)
    try:
        assert reloaded.SettingsRepository.DEFAULT_ACE_ENGINE_URL == "http://engine:6878"
    finally:
        monkeypatch.delenv("ACE_ENGINE_URL", raising=False)
        importlib.reload(settings_repository)
