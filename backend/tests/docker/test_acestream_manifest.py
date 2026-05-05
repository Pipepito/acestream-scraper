"""Schema tests for docker/manifests/acestream.json."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "docker" / "manifests" / "acestream.json"


def load_manifest() -> dict:
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_manifest_has_version_and_platforms():
    payload = load_manifest()
    assert isinstance(payload.get("version"), str) and payload["version"]
    assert isinstance(payload.get("platforms"), dict) and payload["platforms"]


def test_each_platform_install_declares_kind():
    payload = load_manifest()
    for platform, entry in payload["platforms"].items():
        install = entry.get("install")
        assert isinstance(install, dict), f"{platform}: install must be an object"
        kind = install.get("kind")
        assert kind == "executable", (
            f"{platform}: install.kind must be 'executable', got {kind!r}"
        )
        assert isinstance(install.get("binary_path"), str) and install["binary_path"]


def test_validator_passes_on_current_manifest():
    """Running the metadata validator must succeed."""
    import subprocess

    result = subprocess.run(
        ["python3", str(REPO_ROOT / "scripts" / "ci" / "validate_docker_manifest_metadata.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_amd64_install_is_executable_for_3_2_x():
    payload = load_manifest()
    if not payload["version"].startswith("3.2."):
        pytest.skip("test only meaningful while pinned to AceStream 3.2.x")
    install = payload["platforms"]["linux/amd64"]["install"]
    assert install["kind"] == "executable"
    assert install["binary_path"] == "start-engine"
    assert install["strip_components"] == 0
