"""Tests for scripts/ci/derive_acestream_build_args.py (CI wrapper over the resolver)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER = REPO_ROOT / "scripts" / "ci" / "derive_acestream_build_args.py"
MANIFEST = REPO_ROOT / "docker" / "manifests" / "acestream.json"


def _run(manifest_path: Path, flavor: str, platform: str = "") -> tuple[int, str, str]:
    cmd = ["python3", str(HELPER), str(manifest_path), flavor]
    if platform:
        cmd.append(platform)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def _pairs(out: str) -> dict[str, str]:
    return dict(line.split("=", 1) for line in out.strip().splitlines())


def test_non_acestream_flavor_emits_nothing(tmp_path: Path):
    manifest = tmp_path / "ace.json"
    manifest.write_text(json.dumps({"version": "x", "platforms": {}}))
    rc, out, _ = _run(manifest, "scraper")
    assert rc == 0 and out == ""


def test_executable_flavor_emits_expected_keys():
    rc, out, err = _run(MANIFEST, "scraper-acestream-acexy", "linux/amd64")
    assert rc == 0, err
    pairs = _pairs(out)
    expected = json.loads(MANIFEST.read_text())["platforms"]["linux/amd64"]
    assert pairs["ACESTREAM_INSTALL_KIND"] == "executable"
    assert pairs["ACESTREAM_BINARY_PATH"] == "start-engine"
    assert pairs["ACESTREAM_DOWNLOAD_URL"] == expected["url"]
    assert pairs["ACESTREAM_DOWNLOAD_SHA256"] == expected["sha256"]
    assert pairs["ACESTREAM_VENDORED_FILE"] == expected["vendored_file"]
    assert pairs["ACESTREAM_MIRROR_URLS"] == " ".join(expected["mirror_urls"])
    assert "ACESTREAM_PYTHON_MODULE" not in pairs
    # The x86_64 engine links a specific libpython; the manifest pins it and
    # the installer stage pip-installs the engine deps with that interpreter.
    assert pairs["ACESTREAM_PYTHON_VERSION"] == expected["install"]["python_version"]
    assert "ACESTREAM_ANDROID_ABI" not in pairs


def test_android_apk_platforms_emit_bionic_keys():
    expected = json.loads(MANIFEST.read_text())["platforms"]
    for platform in ("linux/arm64", "linux/arm/v7"):
        rc, out, err = _run(MANIFEST, "scraper-acestream", platform)
        assert rc == 0, err
        pairs = _pairs(out)
        entry = expected[platform]
        assert pairs["ACESTREAM_INSTALL_KIND"] == "android-apk"
        assert pairs["ACESTREAM_ARCHIVE_TYPE"] == "apk"
        assert pairs["ACESTREAM_ANDROID_ABI"] == entry["install"]["abi"]
        assert pairs["ACESTREAM_DOWNLOAD_URL"] == entry["url"]
        assert pairs["ACESTREAM_BIONIC_URL"] == entry["install"]["bionic"]["url"]
        assert pairs["ACESTREAM_BIONIC_SHA256"] == entry["install"]["bionic"]["sha256"]
        assert pairs["ACESTREAM_BIONIC_LIBDIR"] == entry["install"]["bionic"]["libdir"]
        assert pairs["ACESTREAM_BIONIC_LINKER"] == entry["install"]["bionic"]["linker"]
        assert pairs["ACESTREAM_PLATFORM_SUPPORT"] == entry["support"]
        assert "ACESTREAM_BINARY_PATH" not in pairs


def test_default_platform_is_first_declared():
    rc, out, err = _run(MANIFEST, "scraper-acestream")
    assert rc == 0, err
    first = next(iter(json.loads(MANIFEST.read_text())["platforms"]))
    assert _pairs(out)["ACESTREAM_PLATFORM"] == first


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


def test_unknown_install_kind_errors(tmp_path: Path):
    manifest = tmp_path / "ace.json"
    manifest.write_text(
        json.dumps({"version": "1", "platforms": {"linux/amd64": {"url": "https://x/y", "install": {"kind": "chroot"}}}})
    )
    rc, _, err = _run(manifest, "scraper-acestream", "linux/amd64")
    assert rc != 0 and "chroot" in err
