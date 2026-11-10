"""The WARP traffic guard against a real kernel, inside the built image.

Unit tests pin the rules as text. This proves what they do: the built image
carries an nft that accepts them, and the kernel blocks, exempts and expires
as designed. The check is offline (`--network none`); see
warp_guard_kernel_check.py.
"""
from __future__ import annotations

import platform as host_platform
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CHECK = Path(__file__).with_name("warp_guard_kernel_check.py")


def _docker_available() -> bool:
    return shutil.which("docker") is not None and subprocess.run(
        ["docker", "info"], capture_output=True
    ).returncode == 0


pytestmark = pytest.mark.skipif(
    not _docker_available(), reason="docker not available on this runner"
)


def _native_platform() -> str:
    return "linux/arm64" if host_platform.machine() in ("arm64", "aarch64") else "linux/amd64"


def test_guard_blocks_exempts_and_expires_in_the_built_image(request: pytest.FixtureRequest):
    platform = _native_platform()
    tag = f"acestream-scraper-smoke:warp-guard-{platform.replace('/', '-')}-{uuid.uuid4().hex[:8]}"
    request.addfinalizer(lambda: subprocess.run(["docker", "image", "rm", "-f", tag], capture_output=True))
    subprocess.run(
        [
            "bash", str(REPO_ROOT / "scripts" / "ci" / "build_multiarch_images.sh"),
            "--flavor", "scraper",
            "--platforms", platform,
            "--load",
            "--network", "host",
            "--tag", tag,
        ],
        check=True, cwd=REPO_ROOT,
    )

    result = subprocess.run(
        [
            "docker", "run", "--rm", "-i",
            "--platform", platform,
            "--network", "none",
            "--sysctl", "net.ipv6.conf.all.disable_ipv6=0",
            "--cap-add", "NET_ADMIN",
            "--entrypoint", "python3",
            tag, "-",
        ],
        input=CHECK.read_text(encoding="utf-8"), capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WARP guard kernel check passed" in result.stdout
