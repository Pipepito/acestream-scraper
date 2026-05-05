"""Tests for scripts/ci/derive_acestream_build_args.py."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER = REPO_ROOT / "scripts" / "ci" / "derive_acestream_build_args.py"


def _run(manifest_path: Path, flavor: str, platform: str = "") -> tuple[int, str, str]:
    cmd = ["python3", str(HELPER), str(manifest_path), flavor]
    if platform:
        cmd.append(platform)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_non_acestream_flavor_emits_nothing(tmp_path: Path):
    manifest = tmp_path / "ace.json"
    manifest.write_text(json.dumps({"version": "x", "platforms": {}}))
    rc, out, _ = _run(manifest, "scraper")
    assert rc == 0 and out == ""


def test_python_module_flavor_emits_expected_keys():
    manifest = REPO_ROOT / "docker" / "manifests" / "acestream.json"
    rc, out, err = _run(manifest, "scraper-acestream-acexy", "linux/amd64")
    assert rc == 0, err
    pairs = dict(line.split("=", 1) for line in out.strip().splitlines())
    assert pairs["ACESTREAM_INSTALL_KIND"] == "python_module"
    assert pairs["ACESTREAM_PYTHON_MODULE"] == "acestreamengine"
    assert pairs["ACESTREAM_PYTHON_VERSION"] == "3.10"
    expected = json.loads((REPO_ROOT / "docker" / "manifests" / "acestream.json").read_text())
    expected_url = expected["platforms"]["linux/amd64"]["url"]
    expected_sha = expected["platforms"]["linux/amd64"]["sha256"]
    assert pairs["ACESTREAM_DOWNLOAD_URL"] == expected_url
    assert pairs["ACESTREAM_DOWNLOAD_SHA256"] == expected_sha


def test_unknown_platform_errors(tmp_path: Path):
    manifest = tmp_path / "ace.json"
    manifest.write_text(
        json.dumps(
            {
                "version": "9.9.9",
                "platforms": {
                    "linux/amd64": {
                        "url": "https://example.invalid/x.tar.gz",
                        "sha256": "",
                        "archive_type": "tar.gz",
                        "install": {
                            "strip_components": 1,
                            "kind": "executable",
                            "binary_path": "engine",
                            "engine_http_port": 6878,
                        },
                    }
                },
            }
        )
    )
    rc, _, err = _run(manifest, "scraper-acestream", "linux/does-not-exist")
    assert rc != 0
    assert "linux/does-not-exist" in err
