"""Build-time tests for docker/scripts/install-acestream.sh.

These tests build the acestream-installer Dockerfile target with controlled
build-args and inspect the resulting filesystem. Skipped when docker is
unavailable. The installer resolves docker/manifests/acestream.json for the
build platform and prefers the vendored archives under docker/vendor/, so no
network access is needed.
"""
from __future__ import annotations

import platform as host_platform
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _docker_available() -> bool:
    # A daemon must answer, not just a CLI on PATH (matches test_acexy_runtime_smoke).
    return shutil.which("docker") is not None and subprocess.run(
        ["docker", "info"], capture_output=True
    ).returncode == 0


pytestmark = pytest.mark.skipif(
    not _docker_available(), reason="docker not available on this runner"
)


def _native_platform() -> str:
    return "linux/arm64" if host_platform.machine() in ("arm64", "aarch64") else "linux/amd64"


def _build_target(tag: str, target: str, build_args: dict[str, str], platform: str = "linux/amd64") -> None:
    # Builder selection is controlled by the BUILDX_BUILDER env var (honored
    # by docker buildx natively). On Jenkins we set it to the docker-driver
    # builder so RUN steps inherit the host's WARP-routed network; locally
    # the default builder is fine. Vendored archives make the network
    # optional anyway.
    cmd = [
        "docker", "buildx", "build",
        "--platform", platform,
        "--network", "host",
        "--load",
        "--target", target,
        "--tag", tag,
    ]
    for key, value in build_args.items():
        cmd.extend(["--build-arg", f"{key}={value}"])
    cmd.append(str(REPO_ROOT))
    subprocess.run(cmd, check=True)


def _build_installer(tag: str, build_args: dict[str, str], platform: str = "linux/amd64") -> None:
    _build_target(tag, "acestream-installer", build_args, platform)


def _read_file_in_image(tag: str, path: str, platform: str = "linux/amd64") -> str:
    result = subprocess.run(
        ["docker", "run", "--rm", "--platform", platform, "--entrypoint", "cat", tag, path],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _list_dir_in_image(tag: str, path: str, platform: str = "linux/amd64") -> list[str]:
    result = subprocess.run(
        ["docker", "run", "--rm", "--platform", platform, "--entrypoint", "ls", tag, "-1", path],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _path_test_in_image(tag: str, flag: str, path: str, platform: str = "linux/amd64") -> bool:
    return subprocess.run(
        ["docker", "run", "--rm", "--platform", platform, "--entrypoint", "test", tag, flag, path],
        check=False,
    ).returncode == 0


def _unique_tag(base: str) -> str:
    """Unique per run: the PR job and the branch job can build the same commit
    concurrently on one runner, and the containerd image store refuses a
    duplicate name mid-export ("already exists")."""
    return f"{base}-{uuid.uuid4().hex[:8]}"


def _register_image_cleanup(request: pytest.FixtureRequest, tag: str) -> None:
    """Schedule `docker image rm -f <tag>` as a pytest finalizer."""
    request.addfinalizer(
        lambda: subprocess.run(
            ["docker", "image", "rm", "-f", tag],
            capture_output=True,
        )
    )


def test_fixture_mode_creates_executable_symlink(request: pytest.FixtureRequest):
    tag = _unique_tag("acestream-installer-test:fixture")
    _register_image_cleanup(request, tag)
    _build_installer(tag, build_args={"ACESTREAM_SOURCE": "fixture"})
    metadata = _read_file_in_image(tag, "/opt/acestream/install-metadata.txt")
    assert "kind=executable" in metadata
    assert "engine_source=fixture" in metadata
    listing = _list_dir_in_image(tag, "/opt/acestream/bin")
    assert "acestreamengine" in listing


def test_executable_install_from_manifest_uses_vendored_tarball(request: pytest.FixtureRequest):
    """Default (auto) mode on linux/amd64 installs the pinned 3.2.x tarball from
    docker/vendor without network access; start-engine is the symlink target
    and python deps are installed."""
    tag = _unique_tag("acestream-installer-test:exec-real")
    _register_image_cleanup(request, tag)
    _build_installer(tag, build_args={})

    metadata = _read_file_in_image(tag, "/opt/acestream/install-metadata.txt")
    assert "platform=linux/amd64" in metadata
    assert "kind=executable" in metadata
    assert "engine_source=vendored:acestream/" in metadata
    assert "resolved_binary=/opt/acestream/start-engine" in metadata

    # start-engine wrapper from the upstream tarball must be present + executable
    assert _path_test_in_image(tag, "-x", "/opt/acestream/start-engine")

    # bin/acestreamengine should symlink to start-engine
    listing = _list_dir_in_image(tag, "/opt/acestream/bin")
    assert "acestreamengine" in listing

    # Python deps installed into /opt/acestream/python-deps
    listing = _list_dir_in_image(tag, "/opt/acestream/python-deps")
    assert "apsw" in listing or any("apsw" in entry for entry in listing)

    # No bionic runtime for the native x86_64 engine
    assert _list_dir_in_image(tag, "/opt/acestream-system") == []


def test_explicit_download_url_overrides_manifest(request: pytest.FixtureRequest):
    """Explicit ACESTREAM_* build-args still win over the manifest (used by
    operators testing a new upstream build before pinning it)."""
    tag = _unique_tag("acestream-installer-test:explicit-override")
    _register_image_cleanup(request, tag)
    _build_installer(
        tag,
        build_args={
            # Point the "download" at the vendored file so the test stays offline;
            # a bogus vendored_file name forces the URL/mirror path to be exercised.
            "ACESTREAM_DOWNLOAD_URL": "file:///tmp/acestream-vendor/acestream/acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz",
            "ACESTREAM_DOWNLOAD_SHA256": "9b6bbd76a55e5a434641afae3b9cf8e6154ce1cf392152ec3aed5ac265432b2e",
            "ACESTREAM_VENDORED_FILE": "does-not-exist.tar.gz",
            "ACESTREAM_INSTALL_KIND": "executable",
            "ACESTREAM_BINARY_PATH": "start-engine",
            "ACESTREAM_STRIP_COMPONENTS": "0",
        },
    )
    metadata = _read_file_in_image(tag, "/opt/acestream/install-metadata.txt")
    assert "kind=executable" in metadata
    assert "engine_source=file:///tmp/acestream-vendor/" in metadata


def test_mirror_fallback_when_vendored_copy_and_upstream_are_unavailable(request: pytest.FixtureRequest):
    """Resolution order is vendored -> upstream url -> mirrors. With no vendored
    copy and an unreachable upstream host, the first working mirror wins and
    the pinned sha256 is still enforced (a file:// mirror keeps the test
    offline)."""
    tag = _unique_tag("acestream-installer-test:mirror-fallback")
    _register_image_cleanup(request, tag)
    _build_installer(
        tag,
        build_args={
            "ACESTREAM_SOURCE": "explicit",
            "ACESTREAM_DOWNLOAD_URL": "https://unreachable.invalid/acestream.tar.gz",
            "ACESTREAM_DOWNLOAD_SHA256": "9b6bbd76a55e5a434641afae3b9cf8e6154ce1cf392152ec3aed5ac265432b2e",
            "ACESTREAM_MIRROR_URLS": (
                "https://also-unreachable.invalid/acestream.tar.gz "
                "file:///tmp/acestream-vendor/acestream/acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz"
            ),
            "ACESTREAM_INSTALL_KIND": "executable",
            "ACESTREAM_BINARY_PATH": "start-engine",
            "ACESTREAM_STRIP_COMPONENTS": "0",
        },
    )
    metadata = _read_file_in_image(tag, "/opt/acestream/install-metadata.txt")
    assert "kind=executable" in metadata
    assert "engine_source=file:///tmp/acestream-vendor/acestream/" in metadata


def test_checksum_mismatch_fails_the_build():
    """A wrong pinned sha256 must fail the installer stage, never install."""
    cmd = [
        "docker", "buildx", "build", "--platform", "linux/amd64", "--network", "host",
        "--target", "acestream-installer", "--output", "type=cacheonly",
        "--build-arg", "ACESTREAM_SOURCE=explicit",
        "--build-arg", "ACESTREAM_DOWNLOAD_URL=file:///tmp/acestream-vendor/acestream/acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz",
        "--build-arg", "ACESTREAM_DOWNLOAD_SHA256=" + "0" * 64,
        "--build-arg", "ACESTREAM_INSTALL_KIND=executable",
        "--build-arg", "ACESTREAM_BINARY_PATH=start-engine",
        "--build-arg", "ACESTREAM_STRIP_COMPONENTS=0",
        str(REPO_ROOT),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert "could not obtain the AceStream engine archive" in (result.stdout + result.stderr)


@pytest.mark.parametrize(
    ("platform", "linker"),
    [("linux/arm64", "linker64"), ("linux/arm/v7", "linker")],
)
def test_arm_oci_image_install_layout(
    request: pytest.FixtureRequest, platform: str, linker: str
):
    """Each ARM target copies its matching digest-pinned jopsis distribution,
    replacing only the bootstrap with the project's persistent Linux launcher."""
    tag = _unique_tag(f"acestream-installer-test:oci-{platform.rsplit('/', 1)[-1]}")
    _register_image_cleanup(request, tag)
    _build_installer(tag, build_args={}, platform=platform)

    metadata = _read_file_in_image(tag, "/opt/acestream/install-metadata.txt", platform)
    assert f"platform={platform}" in metadata
    assert "kind=oci-image" in metadata
    assert "engine_version=3.2.17" in metadata
    assert "distribution=jopsis/acestream v3.2.17-fix" in metadata
    assert "engine_source=oci:jopsis/acestream:v3.2.17-fix@sha256:" in metadata

    ace = set(_list_dir_in_image(tag, "/opt/acestream", platform))
    assert {"main.py.oci-orig", "main_linux.py", "app_bridge.py", "app_bridge.py.oci-orig",
            "engine_version.json", "modules.zip", "python", "lib", "start-engine"} <= ace
    assert "install_id" not in ace
    assert "engine_runtime.json" not in ace
    assert _path_test_in_image(tag, "-x", "/opt/acestream/start-engine", platform)
    assert _path_test_in_image(tag, "-x", "/opt/acestream/python/bin/python", platform)
    assert _path_test_in_image(tag, "-x", f"/opt/acestream-system/bin/{linker}", platform)


def test_scraper_acestream_runtime_has_python310(request: pytest.FixtureRequest):
    """The scraper-acestream image must ship a working python3.10 binary (the
    x86_64 3.2.x engine links libpython3.10) and expose the launcher."""
    tag = _unique_tag("acestream-scraper-task3:scraper-acestream")
    _register_image_cleanup(request, tag)
    # Fixture mode keeps this fast and self-contained.
    _build_target(tag, "scraper-acestream", {"ACESTREAM_SOURCE": "fixture"})
    result = subprocess.run(
        ["docker", "run", "--rm", "--platform", "linux/amd64", "--entrypoint", "python3.10", tag, "--version"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("Python 3.10."), result.stdout

    # Verify the engine binary is reachable end-to-end from the scraper-acestream image
    engine_check = subprocess.run(
        ["docker", "run", "--rm", "--platform", "linux/amd64", "--entrypoint", "/opt/acestream/bin/acestreamengine", tag],
        capture_output=True, text=True, timeout=60,
    )
    # In fixture mode the binary is a 1-line bash script that prints "fixture acestream engine".
    assert engine_check.returncode == 0, engine_check.stderr
    assert "fixture acestream engine" in engine_check.stdout, engine_check.stdout


def test_scraper_acestream_arm64_ships_bionic_at_system(request: pytest.FixtureRequest):
    """The ARM runtime image must expose the bionic runtime at exactly /system
    (the payload's ELF interpreter path is hard-coded)."""
    tag = _unique_tag("acestream-scraper-task3:scraper-acestream-arm64")
    _register_image_cleanup(request, tag)
    _build_target(tag, "scraper-acestream", {}, platform="linux/arm64")
    assert _path_test_in_image(tag, "-x", "/system/bin/linker64", "linux/arm64")
    assert _path_test_in_image(tag, "-f", "/system/lib64/libc.so", "linux/arm64")
    assert _path_test_in_image(tag, "-d", "/var/lib/acestream", "linux/arm64")
    env = subprocess.run(
        ["docker", "image", "inspect", tag, "--format", "{{json .Config.Env}}"],
        check=True, capture_output=True, text=True,
    ).stdout
    assert "ACESTREAM_HOME=/var/lib/acestream" in env
    assert "IMAGE_HAS_ACESTREAM=true" in env
