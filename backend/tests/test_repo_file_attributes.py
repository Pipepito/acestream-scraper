"""Vendored payloads must stay byte-exact, but the README/SHA256SUMS beside
them have to keep rendering as text in diffs. The ``binary`` macro unsets
``diff`` as well as ``text``, so every rule that re-enables ``text`` for those
two names must restore ``diff`` too, otherwise git prints "Binary files
differ" for a checksum list.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VENDOR_PREFIXES = ("docker/vendor/", "backend/tests/docker/fixtures/")
TEXT_NAMES = ("README.md", "SHA256SUMS")

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None or not (REPO_ROOT / ".git").exists(),
    reason="not a git checkout",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True, timeout=60
    ).stdout


def _tracked(text_files: bool) -> List[str]:
    paths = [path for path in _git("ls-files", *VENDOR_PREFIXES).splitlines() if path]
    return [path for path in paths if (Path(path).name in TEXT_NAMES) is text_files]


def _attributes(paths: List[str]) -> Dict[str, Dict[str, str]]:
    attributes: Dict[str, Dict[str, str]] = {}
    for line in _git("check-attr", "text", "diff", "--", *paths).splitlines():
        path, attribute, value = line.rsplit(": ", 2)
        attributes.setdefault(path, {})[attribute] = value
    return attributes


def test_vendored_checksums_and_readmes_render_as_text_in_diffs():
    paths = _tracked(text_files=True)
    assert paths, "no vendored README/SHA256SUMS is tracked any more"
    attributes = _attributes(paths)
    for path in paths:
        assert attributes[path]["text"] == "set", f"{path} is not marked text"
        assert attributes[path]["diff"] == "set", f"{path} would diff as 'Binary files differ'"


def test_vendored_payloads_stay_binary():
    paths = _tracked(text_files=False)
    assert paths, "no vendored payload is tracked any more"
    attributes = _attributes(paths)
    for path in paths:
        assert attributes[path]["text"] == "unset", f"{path} must never be text-normalized"
        assert attributes[path]["diff"] == "unset", f"{path} must never be diffed as text"
