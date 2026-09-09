"""Contract tests for docker/scripts/install-zeronet.sh.

The offline tests run the script directly: the per-platform gate (amd64 and
arm64 build the payload, 32-bit ARM does not), the wrong-host guard, and the
unsupported-platform failure need no network and no docker. The real install
(git fetch + pip) is exercised by the image builds in CI and by the
docker-gated smoke below.
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


def test_32bit_arm_installs_nothing_but_succeeds(tmp_path):
    """gevent publishes no armv7l wheels, so 32-bit ARM stays a no-op.

    Checked on PyPI for both the old 23.9.1 pin and the current one: aarch64
    has manylinux wheels, armv7l has none. Building gevent, greenlet and
    coincurve from source inside the image is not worth it for a node that is
    opt-in and has an external alternative through ZERONET_URL.
    """
    for platform in ("linux/arm/v7", "linux/arm/v6"):
        result = _run(tmp_path / platform.replace("/", "-"), platform)

        assert result.returncode == 0, result.stderr
        assert "no armv7l wheels for gevent" in result.stdout
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

    Both pins still matter, for a different reason than before: the node is
    fetched BY COMMIT (not by tag or branch) so the pin cannot drift when a
    branch moves, and gevent is pinned exactly so a build cannot resolve to
    an untested release.
    """
    script = SCRIPT.read_text()
    assert re.search(r'ZERONET_COMMIT:-[0-9a-f]{40}', script)
    requirements = REQUIREMENTS.read_text()
    assert re.search(r'^gevent==\d+\.\d+\.\d+$', requirements, flags=re.M)


def test_arm64_builds_the_payload_and_is_not_a_no_op(tmp_path):
    """arm64 must NOT take the no-op path.

    Without a git/pip toolchain the script cannot finish here, so the proof
    is that it gets past the platform gate and fails on the host-arch guard
    (or later) instead of reporting "installing nothing".
    """
    result = _run(tmp_path, "linux/arm64")
    assert "installing nothing" not in result.stdout, result.stdout
    metadata = tmp_path / "opt-zeronet" / "install-metadata.txt"
    assert not metadata.exists() or "zeronet_version=none" not in metadata.read_text()


def test_the_payload_must_be_built_on_the_target_arch(tmp_path):
    """Cross-building would embed wrong-arch wheels and a wrong-arch
    interpreter, and it would only show at runtime. The stage is expected to
    run under binfmt as the target platform."""
    import platform as _p

    other = "linux/arm64" if _p.machine() == "x86_64" else "linux/amd64"
    result = _run(tmp_path, other)
    assert result.returncode != 0
    assert "must be built on" in result.stderr, result.stderr


def _native_platform() -> str:
    import platform as _p

    return "linux/arm64" if _p.machine() in ("aarch64", "arm64") else "linux/amd64"


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
            "--platform", _native_platform(),
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
