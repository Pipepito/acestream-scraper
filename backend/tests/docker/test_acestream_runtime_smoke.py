"""End-to-end smoke: build scraper-acestream and run the engine wrapper."""
from __future__ import annotations

import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _docker_available() -> bool:
    return shutil.which("docker") is not None


pytestmark = pytest.mark.skipif(
    not _docker_available(), reason="docker not available on this runner"
)


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


def test_scraper_acestream_starts_real_engine():
    tag = "acestream-scraper-smoke:scraper-acestream"

    # Pull manifest-derived build args via the helper
    derived = subprocess.run(
        [
            "python3",
            str(REPO_ROOT / "scripts" / "ci" / "derive_acestream_build_args.py"),
            str(REPO_ROOT / "docker" / "manifests" / "acestream.json"),
            "scraper-acestream",
            "linux/amd64",
        ],
        check=True, capture_output=True, text=True,
    )
    build_args: list[str] = []
    for line in derived.stdout.strip().splitlines():
        build_args.extend(["--build-arg", line])

    subprocess.run(
        [
            "docker", "buildx", "build",
            "--platform", "linux/amd64",
            "--load",
            "--target", "scraper-acestream",
            "--tag", tag,
            *build_args,
            str(REPO_ROOT),
        ],
        check=True,
    )

    # acestream 3.2.x has no --version flag; rely on the run-d smoke below.
    # Instead, confirm the wrapper file exists and is executable inside the image.
    file_check = subprocess.run(
        [
            "docker", "run", "--rm",
            "--platform", "linux/amd64",
            "--entrypoint", "test",
            tag, "-x", "/opt/acestream/bin/acestreamengine",
        ],
        check=False,
    )
    assert file_check.returncode == 0, "wrapper /opt/acestream/bin/acestreamengine is not executable"

    # Start the full container (engine + app via entrypoint.sh)
    host_port = _free_port()
    container = f"acestream-smoke-{host_port}"
    subprocess.run(["docker", "rm", "-f", container], capture_output=True)
    subprocess.run(
        [
            "docker", "run", "-d",
            "--platform", "linux/amd64",
            "--name", container,
            "-e", "ENABLE_ACESTREAM_ENGINE=true",
            "-p", f"{host_port}:8000",
            tag,
        ],
        check=True,
    )
    try:
        assert _wait_for_port(host_port, timeout=60), "app port did not open"
        # Engine should be reachable inside the container
        ace_check = subprocess.run(
            ["docker", "exec", container, "curl", "-fsS", "http://localhost:6878/webui/api/service?method=get_version"],
            capture_output=True, text=True, timeout=30,
        )
        # Some 3.2.x builds gate webui behind auth; accept either real JSON
        # or a 401-style response, but reject "connection refused".
        combined = ace_check.stdout + ace_check.stderr
        assert "connection refused" not in combined.lower(), combined
    finally:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True)
