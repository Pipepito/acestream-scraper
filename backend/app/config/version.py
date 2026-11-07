"""Application version helpers.

The canonical version lives in ``version.txt`` at the repository root so it
stays in sync with release tooling that operates outside the Python runtime
(Docker tagging, Jenkins release, GitHub release notes). This helper exposes
the value as a string and as a ``packaging.version.Version`` for comparison
gates such as the ``LEGACY_ENV_ALIAS_WINDOW`` expiry test.
"""
from functools import lru_cache
from pathlib import Path

from packaging.version import Version, parse


# The checkout keeps backend/; the runtime image flattens it into /app.
_VERSION_FILES = (
    Path(__file__).resolve().parents[3] / "version.txt",
    Path(__file__).resolve().parents[2] / "version.txt",
)


@lru_cache(maxsize=1)
def get_app_version() -> str:
    """Return the raw version string from ``version.txt``."""
    for path in _VERSION_FILES:
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    raise FileNotFoundError("Application version.txt is missing")


@lru_cache(maxsize=1)
def get_app_version_parsed() -> Version:
    """Return the parsed ``packaging.version.Version`` for the current release.

    Strips a leading ``v`` so values like ``v2.0.0`` parse cleanly.
    """
    raw = get_app_version().lstrip("v")
    return parse(raw)
