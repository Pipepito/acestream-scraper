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


# version.txt sits two levels above this file: backend/app/config/version.py
# -> repo_root/version.txt
_VERSION_FILE = Path(__file__).resolve().parents[3] / "version.txt"


@lru_cache(maxsize=1)
def get_app_version() -> str:
    """Return the raw version string from ``version.txt``."""
    return _VERSION_FILE.read_text(encoding="utf-8").strip()


@lru_cache(maxsize=1)
def get_app_version_parsed() -> Version:
    """Return the parsed ``packaging.version.Version`` for the current release.

    Strips a leading ``v`` so values like ``v2.0.0`` parse cleanly.
    """
    raw = get_app_version().lstrip("v")
    return parse(raw)
