"""Contract tests for docker/scripts/install-zeronet.sh.

The offline tests run the script directly: the per-platform gate (amd64 and
arm64 build the payload, 32-bit ARM does not), the wrong-host guard, and the
unsupported-platform failure need no network and no docker. The real install
(git fetch + pip) is exercised by the image builds in CI and by the
docker-gated smoke below.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "docker" / "scripts" / "install-zeronet.sh"
REQUIREMENTS = REPO_ROOT / "docker" / "zeronet" / "requirements.txt"


def _run(
    tmp_path: Path, platform: str | None, *, machine: str | None = None
) -> subprocess.CompletedProcess:
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "ZERONET_INSTALL_DIR": str(tmp_path / "opt-zeronet"),
        "ZERONET_REQUIREMENTS": str(REQUIREMENTS),
    }
    if machine is not None:
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir(parents=True)
        uname = fake_bin / "uname"
        uname.write_text(f"#!/bin/sh\nprintf '%s\\n' '{machine}'\n")
        uname.chmod(0o755)
        env["PATH"] = f"{fake_bin}:{env['PATH']}"
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

    Force a mismatched host so this offline test never invokes git or pip,
    including when the test runner itself is ARM64.
    """
    result = _run(tmp_path, "linux/arm64", machine="x86_64")
    assert result.returncode != 0
    assert "must be built on aarch64" in result.stderr
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
def test_zeronet_installer_stage_produces_working_launcher(tmp_path):
    """Build the zeronet-installer stage for the native platform and prove the relocated
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
            ["docker", "run", "--rm", "--network", "none", tag, "/opt/zeronet/bin/zeronet", "--no-bootstrap", "--help"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, result.stderr
        assert "--ui-port" in result.stdout

        verification = subprocess.run(
            [
                "docker", "run", "--rm", "--network", "none",
                "-v", f"{REPO_ROOT}:/review:ro",
                "-e", "LD_LIBRARY_PATH=/opt/zeronet/python/lib",
                tag, "/opt/zeronet/python/bin/python3.11",
                "/review/backend/tests/docker/zeronet_manifest_smoke.py",
            ], capture_output=True, text=True, timeout=60,
        )
        assert verification.returncode == 0, verification.stdout + verification.stderr

        # Run the real entrypoint and node twice against the same mounted volume.
        # A successful HTTP response proves startup got past state initialization.
        state = tmp_path / "state"
        state.mkdir()
        (state / "sites.json").write_text("{}")
        identity = {"master_seed": "a" * 64}
        (state / "users.json").write_text(json.dumps({"review-identity": identity}))
        wait_for_node = """
import time
import urllib.request
for attempt in range(100):
    try:
        request = urllib.request.Request('http://127.0.0.1:43110/', headers={'Accept': 'text/html'})
        urllib.request.urlopen(request, timeout=1)
        break
    except Exception:
        time.sleep(0.1)
else:
    raise SystemExit('ZeroNet UI did not start')
"""
        for run in range(2):
            boot = subprocess.run(
                [
                    "docker", "run", "--rm", "--network", "none",
                    "-v", f"{state}:/data/zeronet",
                    "-v", f"{REPO_ROOT}:/review:ro",
                    "-e", "ENABLE_ZERONET=true",
                    "-e", "LOG_DIR=/tmp/logs",
                    "-e", "ZERONET_EXTRA_ARGS=--no-bootstrap --offline",
                    tag, "bash", "/review/entrypoint.sh",
                    "python3", "-c", wait_for_node,
                ], capture_output=True, text=True, timeout=30,
            )
            assert boot.returncode == 0, boot.stdout + boot.stderr
            private = state / ".node" / "private"
            assert (private / "sites.json").is_file()
            users = json.loads((private / "users.json").read_text())
            assert users["review-identity"]["master_seed"] == identity["master_seed"]
            assert "stale" not in users
            assert (state / "sites.json").read_text() == "{}"
            if run == 0:
                # Stale legacy data must never replace already migrated state.
                (state / "users.json").write_text('{"stale": true}')
                (private / "review-sentinel").write_text("preserved")
            else:
                assert (private / "review-sentinel").read_text() == "preserved"
                assert (state / "users.json").read_text() == '{"stale": true}'
    finally:
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True)
