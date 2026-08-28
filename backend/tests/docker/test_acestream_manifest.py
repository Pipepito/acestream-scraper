"""Schema tests for docker/manifests/acestream.json and the vendored payloads."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = REPO_ROOT / "docker" / "manifests" / "acestream.json"
PLATFORMS_PATH = REPO_ROOT / "docker" / "manifests" / "platforms.json"
RESOLVER = REPO_ROOT / "docker" / "scripts" / "acestream_manifest.py"
ANDROID_BOOTSTRAP_DIR = REPO_ROOT / "docker" / "scripts" / "acestream-android"


def load_manifest() -> dict:
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_manifest_has_version_and_platforms():
    payload = load_manifest()
    assert isinstance(payload.get("version"), str) and payload["version"]
    assert isinstance(payload.get("platforms"), dict) and payload["platforms"]
    assert payload["mirror_base_url"].startswith("https://github.com/")
    assert (REPO_ROOT / payload["vendor_dir"]).is_dir()


def test_each_platform_install_declares_a_known_kind():
    payload = load_manifest()
    for platform, entry in payload["platforms"].items():
        install = entry.get("install")
        assert isinstance(install, dict), f"{platform}: install must be an object"
        kind = install.get("kind")
        assert kind in {"executable", "android-apk"}, (
            f"{platform}: install.kind must be 'executable' or 'android-apk', got {kind!r}"
        )
        assert entry["support"] in {"stable", "experimental"}
        if kind == "executable":
            assert isinstance(install.get("binary_path"), str) and install["binary_path"]
            assert entry["archive_type"] == "tar.gz"
        else:
            assert install["abi"] in {"arm64-v8a", "armeabi-v7a"}
            assert entry["archive_type"] == "apk"
            assert isinstance(install["bionic"], dict)


def test_acestream_platforms_cover_every_baseline_platform():
    """All baseline platforms (amd64, arm/v7, arm64) now have an engine."""
    baseline = json.loads(PLATFORMS_PATH.read_text(encoding="utf-8"))["baseline_platforms"]
    assert set(baseline) == set(load_manifest()["platforms"])


def test_arm_entries_use_the_official_android_engine_on_bionic():
    payload = load_manifest()
    expected = {
        "linux/arm64": ("arm64-v8a", "armv8_64", "lib64", "linker64", "aarch64"),
        "linux/arm/v7": ("armeabi-v7a", "armv7", "lib", "linker", "arm"),
    }
    for platform, (abi, apk_arch, libdir, linker, deb_arch) in expected.items():
        entry = payload["platforms"][platform]
        assert entry["url"].startswith("https://download.acestream.media/android/")
        assert entry["url"].endswith(f"-{apk_arch}.apk")
        assert entry["engine_version"] == payload["android_version"]
        install = entry["install"]
        assert install["kind"] == "android-apk"
        assert install["abi"] == abi
        bionic = install["bionic"]
        assert bionic["libdir"] == libdir and bionic["linker"] == linker
        assert bionic["vendored_file"].endswith(f"_{deb_arch}.deb")
    assert payload["platforms"]["linux/arm/v7"]["support"] == "experimental"
    assert payload["platforms"]["linux/arm64"]["support"] == "stable"


@pytest.mark.parametrize("platform", ["linux/amd64", "linux/arm64", "linux/arm/v7"])
def test_vendored_payloads_match_pinned_sha256(platform: str):
    """The in-repo copies used by the build must be byte-identical to the pins."""
    payload = load_manifest()
    entry = payload["platforms"][platform]
    vendored = REPO_ROOT / payload["vendor_dir"] / entry["vendored_file"]
    assert vendored.is_file(), f"missing vendored engine archive {vendored}"
    assert hashlib.sha256(vendored.read_bytes()).hexdigest() == entry["sha256"]
    for url in entry["mirror_urls"]:
        assert url == f"{payload['mirror_base_url']}/{entry['vendored_file']}"
    bionic = entry["install"].get("bionic")
    if bionic:
        deb = REPO_ROOT / bionic["vendor_dir"] / bionic["vendored_file"]
        assert deb.is_file(), f"missing vendored bionic package {deb}"
        assert hashlib.sha256(deb.read_bytes()).hexdigest() == bionic["sha256"]


def test_validator_passes_on_current_manifest():
    """Running the metadata validator must succeed."""
    result = subprocess.run(
        ["python3", str(REPO_ROOT / "scripts" / "ci" / "validate_docker_manifest_metadata.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_validator_rejects_unknown_install_kind(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "ci"))
    import validate_docker_manifest_metadata as validator

    payload = load_manifest()
    payload["platforms"]["linux/arm64"]["install"]["kind"] = "chroot"
    with pytest.raises(AssertionError, match="install.kind"):
        validator.require_platform_entry(payload["platforms"]["linux/arm64"], "linux/arm64", payload)


def test_amd64_install_is_executable_for_3_2_x():
    payload = load_manifest()
    if not payload["version"].startswith("3.2."):
        pytest.skip("test only meaningful while pinned to AceStream 3.2.x")
    install = payload["platforms"]["linux/amd64"]["install"]
    assert install["kind"] == "executable"
    assert install["binary_path"] == "start-engine"
    assert install["strip_components"] == 0


def test_resolver_emits_platform_specific_variables():
    def resolve(platform: str) -> dict[str, str]:
        out = subprocess.run(
            ["python3", str(RESOLVER), str(MANIFEST_PATH), "--platform", platform],
            check=True, capture_output=True, text=True,
        ).stdout
        return dict(line.split("=", 1) for line in out.strip().splitlines())

    amd64 = resolve("linux/amd64")
    assert amd64["ACESTREAM_INSTALL_KIND"] == "executable"
    assert amd64["ACESTREAM_BINARY_PATH"] == "start-engine"
    assert "ACESTREAM_ANDROID_ABI" not in amd64

    arm64 = resolve("linux/arm64")
    assert arm64["ACESTREAM_INSTALL_KIND"] == "android-apk"
    assert arm64["ACESTREAM_ANDROID_ABI"] == "arm64-v8a"
    assert arm64["ACESTREAM_BIONIC_LIBDIR"] == "lib64"
    assert arm64["ACESTREAM_VENDOR_SUBDIR"] == "acestream"
    assert arm64["ACESTREAM_BIONIC_VENDOR_SUBDIR"] == "bionic"
    assert "ACESTREAM_BINARY_PATH" not in arm64

    unknown = subprocess.run(
        ["python3", str(RESOLVER), str(MANIFEST_PATH), "--platform", "linux/ppc64le"],
        capture_output=True, text=True,
    )
    assert unknown.returncode != 0 and "linux/ppc64le" in unknown.stderr


def test_resolver_respects_explicit_environment_overrides(monkeypatch: pytest.MonkeyPatch):
    env = {"ACESTREAM_DOWNLOAD_URL": "https://example.invalid/custom.apk"}
    out = subprocess.run(
        ["python3", str(RESOLVER), str(MANIFEST_PATH), "--platform", "linux/arm64", "--respect-env"],
        check=True, capture_output=True, text=True, env={**dict(__import__("os").environ), **env},
    ).stdout
    keys = {line.split("=", 1)[0] for line in out.strip().splitlines()}
    assert "ACESTREAM_DOWNLOAD_URL" not in keys  # explicit build-arg wins
    assert "ACESTREAM_DOWNLOAD_SHA256" in keys


def test_android_bootstrap_files_are_shipped():
    for name in ("start-engine", "main_linux.py", "app_bridge.py", "acestream.conf"):
        assert (ANDROID_BOOTSTRAP_DIR / name).is_file(), name
    launcher = (ANDROID_BOOTSTRAP_DIR / "start-engine").read_text(encoding="utf-8")
    assert "PAGESIZE" in launcher  # 16 KB-page kernels must fail loudly
    assert "main_linux.py" in launcher
    conf = (ANDROID_BOOTSTRAP_DIR / "acestream.conf").read_text(encoding="utf-8")
    assert "--log-debug" not in conf  # no Android-app debug logging in docker logs


def test_dockerfile_engine_python_default_matches_manifest():
    """The Dockerfile grafts python<ACESTREAM_ENGINE_PYTHON_VERSION> for the
    x86_64 engine; its default must equal the manifest's pinned interpreter so
    a plain `docker build` never mixes interpreter versions."""
    import re

    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    match = re.search(r"^ARG ACESTREAM_ENGINE_PYTHON_VERSION=(\S+)$", dockerfile, re.M)
    assert match, "Dockerfile must declare a global ARG ACESTREAM_ENGINE_PYTHON_VERSION default"
    pinned = load_manifest()["platforms"]["linux/amd64"]["install"]["python_version"]
    assert match.group(1) == pinned
    assert re.search(r"^ARG APP_PYTHON_VERSION=3\.\d+$", dockerfile, re.M), "app Python must be a global ARG"
    assert "FROM python:${APP_PYTHON_VERSION}-slim AS runtime-base" in dockerfile
    assert "FROM python:${ACESTREAM_ENGINE_PYTHON_VERSION}-slim AS engine-python" in dockerfile
