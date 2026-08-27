"""End-to-end smoke: build scraper-acestream and run the real engine.

Parametrized over the manifest's platforms that this host can execute:
linux/amd64 always (natively or under QEMU) and linux/arm64 when the host is
arm64 (the Android engine's bionic runtime cannot be exercised under
qemu-user). linux/arm/v7 needs real 32-bit ARM hardware and is build-tested
only (see test_install_acestream.py).
"""
from __future__ import annotations

import json
import platform as host_platform
import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = json.loads((REPO_ROOT / "docker" / "manifests" / "acestream.json").read_text(encoding="utf-8"))


def _docker_available() -> bool:
    return shutil.which("docker") is not None


pytestmark = pytest.mark.skipif(
    not _docker_available(), reason="docker not available on this runner"
)


def _runnable_platforms() -> list[str]:
    platforms = ["linux/amd64"]
    if host_platform.machine() in ("arm64", "aarch64"):
        platforms.append("linux/arm64")
    return [p for p in platforms if p in MANIFEST["platforms"]]


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_port(port: int, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            try:
                sock.connect(("127.0.0.1", port))
                return True
            except OSError:
                time.sleep(0.5)
    return False


def _register_image_cleanup(request: pytest.FixtureRequest, tag: str) -> None:
    """Schedule `docker image rm -f <tag>` as a pytest finalizer."""
    request.addfinalizer(
        lambda: subprocess.run(
            ["docker", "image", "rm", "-f", tag],
            capture_output=True,
        )
    )


@pytest.mark.parametrize("platform", _runnable_platforms())
def test_scraper_acestream_starts_real_engine(request: pytest.FixtureRequest, platform: str):
    tag = f"acestream-scraper-smoke:scraper-acestream-{platform.replace('/', '-')}"
    _register_image_cleanup(request, tag)

    # Build through the canonical script so the manifest-driven, per-platform
    # engine selection is exercised exactly as in CI/release. BUILDX_BUILDER
    # (env) controls the buildx instance; on Jenkins it is the docker driver
    # so RUN steps inherit the host's WARP-routed network (only needed when
    # the vendored archives are missing).
    subprocess.run(
        [
            "bash", str(REPO_ROOT / "scripts" / "ci" / "build_multiarch_images.sh"),
            "--flavor", "scraper-acestream",
            "--platforms", platform,
            "--load",
            "--network", "host",
            "--tag", tag,
        ],
        check=True, cwd=REPO_ROOT,
    )

    # Confirm the launcher exists and is executable inside the image.
    file_check = subprocess.run(
        [
            "docker", "run", "--rm",
            "--platform", platform,
            "--entrypoint", "test",
            tag, "-x", "/opt/acestream/bin/acestreamengine",
        ],
        check=False,
    )
    assert file_check.returncode == 0, "wrapper /opt/acestream/bin/acestreamengine is not executable"

    expected_version = MANIFEST["platforms"][platform]["engine_version"]

    # Start the full container (engine + app via entrypoint.sh)
    host_port = _free_port()
    container = f"acestream-smoke-{host_port}"
    subprocess.run(["docker", "rm", "-f", container], capture_output=True)
    subprocess.run(
        [
            "docker", "run", "-d",
            "--platform", platform,
            "--name", container,
            "-e", "ENABLE_ACESTREAM_ENGINE=true",
            "-p", f"{host_port}:8000",
            tag,
        ],
        check=True,
    )
    try:
        assert _wait_for_port(host_port, timeout=120), "app port did not open"
        # The engine and the app are independent processes spawned by
        # entrypoint.sh; engine startup is heavier than uvicorn (much heavier
        # under QEMU), so retry the webui probe until it answers.
        ace_check = None
        engine_deadline = time.time() + 240
        while time.time() < engine_deadline:
            ace_check = subprocess.run(
                [
                    "docker", "exec", container, "curl", "-fsS",
                    "http://localhost:6878/webui/api/service?method=get_version",
                ],
                capture_output=True, text=True, timeout=15,
            )
            if ace_check.returncode == 0 and ace_check.stdout.strip():
                break
            time.sleep(3)
        assert ace_check is not None, "engine curl never executed"
        if ace_check.returncode != 0:
            logs = subprocess.run(["docker", "logs", container], capture_output=True, text=True)
            pytest.fail(
                f"engine never answered on :6878 for {platform}: rc={ace_check.returncode} "
                f"stderr={ace_check.stderr!r}\n{logs.stdout[-3000:]}{logs.stderr[-3000:]}"
            )
        payload = json.loads(ace_check.stdout)
        assert payload.get("error") is None, payload
        reported = str(payload["result"]["version"])
        assert expected_version.startswith(reported), (
            f"{platform}: engine reports {reported}, manifest pins {expected_version}"
        )

        # The backend's engine status probe must succeed against this engine.
        status = subprocess.run(
            ["docker", "exec", container, "curl", "-fsS",
             "http://localhost:6878/server/api?api_version=3&method=get_status"],
            capture_output=True, text=True, timeout=15,
        )
        assert status.returncode == 0, status.stderr
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)
