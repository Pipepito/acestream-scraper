"""Contract tests for docker/scripts/install-ipfs.sh.

Unlike the acestream installer tests these run the script directly (no image
build): the paths that matter — the platform selection, the 32-bit ARM
no-op, and the unsupported-platform failure — need no network and no docker.
The amd64/arm64 download paths are exercised by the real image builds in CI.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "docker" / "scripts" / "install-ipfs.sh"


def _run(tmp_path: Path, platform: str | None) -> subprocess.CompletedProcess:
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "IPFS_INSTALL_DIR": str(tmp_path / "opt-ipfs"),
        "IPFS_INSTALL_SRC_DIR": str(tmp_path / "src"),
    }
    if platform is not None:
        env["TARGETPLATFORM"] = platform
    return subprocess.run(
        ["bash", str(SCRIPT)], env=env, capture_output=True, text=True
    )


def test_armv7_installs_nothing_but_succeeds(tmp_path):
    result = _run(tmp_path, "linux/arm/v7")

    assert result.returncode == 0, result.stderr
    assert "no 32-bit ARM build" in result.stdout
    metadata = (tmp_path / "opt-ipfs" / "install-metadata.txt").read_text()
    assert "kubo_version=none" in metadata
    assert not (tmp_path / "opt-ipfs" / "bin" / "ipfs").exists()


def test_unsupported_platform_fails(tmp_path):
    result = _run(tmp_path, "linux/riscv64")

    assert result.returncode != 0
    assert "unsupported TARGETPLATFORM" in result.stderr


def test_missing_target_platform_fails(tmp_path):
    result = _run(tmp_path, None)

    assert result.returncode != 0
    assert "TARGETPLATFORM is not set" in result.stderr


def test_pinned_platforms_cover_the_image_matrix():
    """amd64 and arm64 build pinned source; arm/v7 is the explicit no-op.

    docker/manifests/platforms.json defines the platforms images are built
    for — every one of them must be handled by the installer's case table.
    """
    script = SCRIPT.read_text()
    assert 'linux/amd64)' in script
    assert 'linux/arm64|linux/arm64/v8)' in script
    assert 'linux/arm/v7|linux/arm/v6)' in script
    # One pinned upstream source shared by both cross-compiled platforms.
    import re

    assert re.search(r"^KUBO_SOURCE_SHA256=[0-9a-f]{64}$", script, re.M)
    assert re.search(r"^KUBO_COMMIT=[0-9a-f]{40}$", script, re.M)
    assert "-mod=readonly" in script
    assert "GOTOOLCHAIN=local" in script
