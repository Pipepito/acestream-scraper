"""
Runtime smoke for the Acexy proxy: the scraper-acexy flavor must ship the
real upstream Acexy (pinned in docker/manifests/acexy.json), not the build
fixture. Requires a local docker daemon; skipped when docker is missing.
"""
from __future__ import annotations

import platform
import socket
import subprocess
import time
import urllib.request
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]

pytestmark = pytest.mark.skipif(
    subprocess.run(["docker", "info"], capture_output=True).returncode != 0,
    reason="docker daemon not available",
)


def _native_platform() -> str:
    return "linux/arm64" if platform.machine() in ("arm64", "aarch64") else "linux/amd64"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _register_image_cleanup(request: pytest.FixtureRequest, tag: str) -> None:
    request.addfinalizer(
        lambda: subprocess.run(["docker", "image", "rm", "-f", tag], capture_output=True)
    )


def test_scraper_acexy_ships_real_acexy_and_serves_status(request: pytest.FixtureRequest):
    # Unique per run: the PR job and the branch job can build the same
    # commit concurrently on one runner, and the containerd image store
    # refuses a duplicate name mid-export ("already exists").
    tag = f"acestream-scraper-smoke:scraper-acexy-{uuid.uuid4().hex[:8]}"
    _register_image_cleanup(request, tag)
    plat = _native_platform()

    # Build through the canonical script so the manifest-derived
    # ACEXY_REPO/ACEXY_REF args are exercised exactly as in CI/release.
    subprocess.run(
        [
            "bash", str(REPO_ROOT / "scripts" / "ci" / "build_multiarch_images.sh"),
            "--flavor", "scraper-acexy",
            "--platforms", plat,
            "--load",
            "--tag", tag,
        ],
        check=True, cwd=REPO_ROOT,
    )

    # The fixture stub prints "fixture acexy" and exits; the real proxy
    # prints its flag usage.
    probe = subprocess.run(
        ["docker", "run", "--rm", "--platform", plat,
         "--entrypoint", "/opt/acexy/bin/acexy", tag, "--help"],
        capture_output=True, text=True, check=False,
    )
    combined = probe.stdout + probe.stderr
    assert "fixture acexy" not in combined, "image ships the acexy build fixture, not the real proxy"
    assert combined.strip(), "acexy --help produced no output"

    host_port = _free_port()
    container = f"acexy-smoke-{host_port}"
    subprocess.run(["docker", "rm", "-f", container], capture_output=True)
    subprocess.run(
        [
            "docker", "run", "-d", "--platform", plat, "--name", container,
            "-e", "ENABLE_ACEXY=true",
            # Point at an external engine so the entrypoint's
            # localhost-engine guard does not apply to this flavor.
            "-e", "ACEXY_HOST=host.docker.internal",
            "-p", f"{host_port}:8080",
            tag,
        ],
        check=True,
    )
    try:
        deadline = time.time() + 60
        last_error = "not attempted"
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{host_port}/ace/status", timeout=3
                ) as response:
                    assert response.status == 200
                    break
            except Exception as exc:  # noqa: BLE001 - retry until deadline
                last_error = str(exc)
                time.sleep(2)
        else:
            logs = subprocess.run(
                ["docker", "logs", container], capture_output=True, text=True
            )
            pytest.fail(
                f"acexy never served /ace/status within 60s (last error: {last_error})\n"
                f"{logs.stdout[-2000:]}{logs.stderr[-2000:]}"
            )
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)
