"""Build-time tests for docker/scripts/install-acestream.sh.

These tests build the acestream-installer Dockerfile target with controlled
build-args and inspect the resulting filesystem to assert behaviour.
Skipped when docker is unavailable.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _docker_available() -> bool:
    return shutil.which("docker") is not None


pytestmark = pytest.mark.skipif(
    not _docker_available(), reason="docker not available on this runner"
)


def _build_installer(tag: str, build_args: dict[str, str]) -> None:
    cmd = [
        "docker",
        "buildx",
        "build",
        "--platform",
        "linux/amd64",
        "--load",
        "--target",
        "acestream-installer",
        "--tag",
        tag,
    ]
    for key, value in build_args.items():
        cmd.extend(["--build-arg", f"{key}={value}"])
    cmd.append(str(REPO_ROOT))
    subprocess.run(cmd, check=True)


def _read_file_in_image(tag: str, path: str) -> str:
    result = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "cat", tag, path],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _list_dir_in_image(tag: str, path: str) -> list[str]:
    result = subprocess.run(
        ["docker", "run", "--rm", "--entrypoint", "ls", tag, "-1", path],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_fixture_mode_creates_executable_symlink():
    tag = "acestream-installer-test:fixture"
    _build_installer(tag, build_args={"ACESTREAM_BINARY_PATH": "start-engine"})
    metadata = _read_file_in_image(tag, "/opt/acestream/install-metadata.txt")
    assert "kind=executable" in metadata
    listing = _list_dir_in_image(tag, "/opt/acestream/bin")
    assert "acestreamengine" in listing


def test_python_module_kind_not_yet_implemented_returns_clear_error():
    """Until Task 4 lands, requesting python_module must fail loudly."""
    tag = "acestream-installer-test:pymod-stub"
    cmd = [
        "docker",
        "buildx",
        "build",
        "--platform",
        "linux/amd64",
        "--load",
        "--target",
        "acestream-installer",
        "--tag",
        tag,
        "--build-arg",
        "ACESTREAM_INSTALL_KIND=python_module",
        str(REPO_ROOT),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert "python_module install kind not yet implemented" in (result.stderr + result.stdout)
