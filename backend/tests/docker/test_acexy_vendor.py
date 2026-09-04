"""The Acexy source archive is vendored (docker/vendor/acexy) so image builds
never depend on cloning GitHub: the manifest, the SHA256SUMS file and the
archive itself must agree, and the build script must hand the archive to the
Dockerfile as build args."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = REPO_ROOT / "docker" / "manifests" / "acexy.json"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "ci" / "build_multiarch_images.sh"


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_vendored_archive_matches_manifest_and_sums():
    manifest = _manifest()
    vendor_dir = REPO_ROOT / manifest["vendor_dir"]
    archive = vendor_dir / manifest["vendored_file"]
    assert archive.is_file(), f"vendored archive missing: {archive}"

    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert digest == manifest["sha256"], "acexy.json sha256 does not match the vendored archive"

    sums = {}
    for line in (vendor_dir / "SHA256SUMS").read_text().splitlines():
        if line.strip():
            checksum, name = line.split(maxsplit=1)
            sums[name.strip().lstrip("*")] = checksum
    assert sums.get(manifest["vendored_file"]) == manifest["sha256"], "SHA256SUMS disagrees with acexy.json"
    assert manifest["version"] in manifest["vendored_file"], "archive name should carry the pinned version"


def test_build_script_passes_vendored_archive_for_acexy_flavors():
    manifest = _manifest()
    for flavor in ("scraper-acexy", "scraper-acestream-acexy"):
        proc = subprocess.run(
            ["bash", str(BUILD_SCRIPT), "--flavor", flavor, "--platforms", "linux/amd64", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert f"ACEXY_VENDORED_FILE={manifest['vendored_file']}" in proc.stdout, flavor
        assert f"ACEXY_SHA256={manifest['sha256']}" in proc.stdout, flavor

    proc = subprocess.run(
        ["bash", str(BUILD_SCRIPT), "--flavor", "scraper", "--platforms", "linux/amd64", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "ACEXY_VENDORED_FILE" not in proc.stdout, "non-Acexy flavors must not receive Acexy build args"


def test_dockerfile_prefers_the_vendored_archive_over_git():
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    builder = dockerfile.split("AS acexy-builder", 1)[1].split("\nFROM ", 1)[0]
    assert "ACEXY_VENDORED_FILE" in builder
    assert builder.index("ACEXY_VENDORED_FILE}\" ]; then") < builder.index("git clone --depth 1"), "vendored archive must be tried before git clone"
    assert "sha256sum -c" in builder
