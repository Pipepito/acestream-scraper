"""The release file works in both checkout and flattened image layouts."""
import pytest

from app.config import version


@pytest.fixture(autouse=True)
def clear_version_cache():
    version.get_app_version.cache_clear()
    version.get_app_version_parsed.cache_clear()
    yield
    version.get_app_version.cache_clear()
    version.get_app_version_parsed.cache_clear()


@pytest.mark.parametrize("layout", ["checkout", "image"])
def test_version_file_layouts(tmp_path, monkeypatch, layout):
    checkout = tmp_path / "version.txt"
    image = tmp_path / "app" / "version.txt"
    chosen = checkout if layout == "checkout" else image
    chosen.parent.mkdir(parents=True, exist_ok=True)
    chosen.write_text("v2.2.0\n")
    monkeypatch.setattr(version, "_VERSION_FILES", (checkout, image))
    assert version.get_app_version() == "v2.2.0"
    assert str(version.get_app_version_parsed()) == "2.2.0"


def test_missing_version_is_not_silently_reported_as_an_old_release(tmp_path, monkeypatch):
    monkeypatch.setattr(version, "_VERSION_FILES", (tmp_path / "missing.txt",))
    with pytest.raises(FileNotFoundError, match="version.txt"):
        version.get_app_version()
