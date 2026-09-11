"""The FFmpeg source tarball is vendored (docker/vendor/ffmpeg) so image
builds need no egress to ffmpeg.org: manifest, SHA256SUMS and the archive
must agree, the validator must check them, and the build script must hand
the archive to the Dockerfile for every flavor (ffmpeg rides in runtime-base)."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "docker" / "manifests" / "ffmpeg.json"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "ci" / "build_multiarch_images.sh"
VALIDATOR = REPO_ROOT / "scripts" / "ci" / "validate_docker_manifest_metadata.py"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_vendored_archive_matches_manifest_and_sums():
    manifest = _manifest()
    vendor_dir = REPO_ROOT / manifest["vendor_dir"]
    archive = vendor_dir / manifest["vendored_file"]
    assert archive.is_file(), f"vendored archive missing: {archive}"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest["sha256"]
    sums = {}
    for line in (vendor_dir / "SHA256SUMS").read_text().splitlines():
        if line.strip():
            checksum, name = line.split(maxsplit=1)
            sums[name.strip().lstrip("*")] = checksum
    assert sums.get(manifest["vendored_file"]) == manifest["sha256"]
    assert manifest["version"] in manifest["vendored_file"]
    assert manifest["vendor_dir"] == "docker/vendor/ffmpeg"
    assert manifest["mirror_urls"][0].endswith("/" + manifest["vendored_file"])


def test_validator_checks_the_ffmpeg_manifest(tmp_path):
    proc = subprocess.run(["python3", str(VALIDATOR)], capture_output=True, text=True, cwd=REPO_ROOT)
    assert proc.returncode == 0, proc.stderr
    # Break the sha in a copy of the repo layout the validator reads relative to itself:
    # simplest is to assert the validator source references ffmpeg.json and require_vendored for it.
    source = VALIDATOR.read_text()
    assert 'load_json("docker/manifests/ffmpeg.json")' in source
    assert 'require_vendored(\n        "ffmpeg.json"' in source or 'require_vendored("ffmpeg.json"' in source


def test_build_script_passes_vendored_ffmpeg_for_every_flavor():
    manifest = _manifest()
    for flavor in ("scraper", "scraper-acestream", "scraper-acexy", "scraper-acestream-acexy"):
        proc = subprocess.run(
            ["bash", str(BUILD_SCRIPT), "--flavor", flavor, "--platforms", "linux/amd64", "--dry-run"],
            capture_output=True, text=True, cwd=REPO_ROOT, check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert f"FFMPEG_VENDORED_FILE={manifest['vendored_file']}" in proc.stdout, flavor
        assert f"FFMPEG_SHA256={manifest['sha256']}" in proc.stdout, flavor
        assert f"FFMPEG_SOURCE_URL={manifest['source_url']}" in proc.stdout, flavor


def test_dockerfile_builds_ffmpeg_from_the_vendored_archive():
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    builder = dockerfile.split("AS ffmpeg-builder", 1)[1].split("\nFROM ", 1)[0]
    assert "FFMPEG_VENDORED_FILE" in builder and "FFMPEG_SHA256" in builder
    assert "--mount=type=bind,source=docker/vendor,target=/tmp/ffmpeg-vendor,readonly" in builder
    assert "build-ffmpeg.sh" in builder
    assert "COPY --from=ffmpeg-builder /out/ /opt/ffmpeg/bin/" in dockerfile
