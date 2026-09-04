"""Contract tests for docker/scripts/install-zeronet.sh.

The offline tests run the script directly: the per-platform gate (amd64-only
payload), the ARM no-op, and the unsupported-platform failure need no network
and no docker. The real amd64 install (git clone + pip) is exercised by the
image builds in CI (the Jenkins runtime-smoke stage builds the full amd64
image, zeronet-installer stage included) and by the docker-gated smoke below.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "docker" / "scripts" / "install-zeronet.sh"
REQUIREMENTS = REPO_ROOT / "docker" / "zeronet" / "requirements.txt"


def _run(tmp_path: Path, platform: str | None) -> subprocess.CompletedProcess:
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "ZERONET_INSTALL_DIR": str(tmp_path / "opt-zeronet"),
        "ZERONET_REQUIREMENTS": str(REQUIREMENTS),
    }
    if platform is not None:
        env["TARGETPLATFORM"] = platform
    return subprocess.run(
        ["bash", str(SCRIPT)], env=env, capture_output=True, text=True
    )


def test_arm_platforms_install_nothing_but_succeed(tmp_path):
    for platform in ("linux/arm64", "linux/arm/v7"):
        result = _run(tmp_path / platform.replace("/", "-"), platform)

        assert result.returncode == 0, result.stderr
        assert "bundled for linux/amd64 only" in result.stdout
        metadata = (
            tmp_path / platform.replace("/", "-") / "opt-zeronet" / "install-metadata.txt"
        ).read_text()
        assert "zeronet_version=none" in metadata


def test_unsupported_platform_fails(tmp_path):
    result = _run(tmp_path, "linux/riscv64")

    assert result.returncode != 0
    assert "unsupported TARGETPLATFORM" in result.stderr


def test_missing_target_platform_fails(tmp_path):
    result = _run(tmp_path, None)

    assert result.returncode != 0
    assert "TARGETPLATFORM is not set" in result.stderr


def test_source_pin_and_gevent_pin_are_in_place():
    """The source is pinned by commit and gevent by exact version.

    zeronet-conservancy v0.7.10 deadlocks at startup under gevent >= 24.10
    (import-time ThreadPool + LoopExit), so the gevent pin is load-bearing —
    a range would silently resolve to a broken node.
    """
    script = SCRIPT.read_text()
    assert re.search(r'ZERONET_COMMIT:-[0-9a-f]{40}', script)
    requirements = REQUIREMENTS.read_text()
    assert re.search(r'^gevent==23\.9\.\d+$', requirements, flags=re.M)


def _docker_available() -> bool:
    return shutil.which("docker") is not None and subprocess.run(
        ["docker", "info"], capture_output=True
    ).returncode == 0


@pytest.mark.skipif(not _docker_available(), reason="docker not available on this runner")
def test_zeronet_installer_stage_produces_working_launcher():
    """Build the zeronet-installer stage for amd64 and prove the relocated
    interpreter + launcher actually start ZeroNet far enough to print its
    argparse help (which exercises Config/plugins import, not just bash)."""
    tag = f"acestream-zeronet-installer-test:{uuid.uuid4().hex[:8]}"
    subprocess.run(
        [
            "docker", "buildx", "build",
            "--platform", "linux/amd64",
            "--network", "host",
            "--load",
            "--target", "zeronet-installer",
            "--tag", tag,
            str(REPO_ROOT),
        ],
        check=True,
    )
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", tag, "/opt/zeronet/bin/zeronet", "--help"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, result.stderr
        assert "--ui_port" in result.stdout
    finally:
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)
