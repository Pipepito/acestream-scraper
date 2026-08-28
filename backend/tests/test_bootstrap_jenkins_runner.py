import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_SCRIPT = REPO_ROOT / "scripts" / "ci" / "bootstrap_jenkins_runner.sh"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def _write_common_tools(fake_bin: Path) -> None:
    _write_executable(
        fake_bin / "uname",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "if [ \"${1:-}\" = \"-s\" ]; then\n"
        "  printf 'Linux\\n'\n"
        "else\n"
        "  /usr/bin/uname \"$@\"\n"
        "fi\n",
    )
    _write_executable(
        fake_bin / "git",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf 'git version 2.43.0\\n'\n",
    )
    _write_executable(
        fake_bin / "python3",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "if [ \"${1:-}\" = \"-m\" ] && [ \"${2:-}\" = \"pip\" ] && [ \"${3:-}\" = \"--version\" ]; then\n"
        "  printf 'pip 24.0 from /tmp/fake/site-packages/pip (python 3.12)\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"${1:-}\" = \"-m\" ] && [ \"${2:-}\" = \"venv\" ] && [ \"${3:-}\" = \"--help\" ]; then\n"
        "  exit 0\n"
        "fi\n"
        "printf 'Python 3.12.3\\n'\n",
    )
    _write_executable(
        fake_bin / "node",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"${BOOTSTRAP_TEST_NODE_VERSION:-v20.11.1}\"\n",
    )
    _write_executable(
        fake_bin / "npm",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '10.2.4\\n'\n",
    )
    _write_executable(
        fake_bin / "rg",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf 'ripgrep 14.1.1\\n'\n",
    )


def _write_docker_stub(fake_bin: Path, *, mode: str) -> None:
    _write_executable(
        fake_bin / "docker",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$*\" >> \"${DOCKER_LOG:?}\"\n"
        "state_dir=\"${BOOTSTRAP_TEST_STATE_DIR:?}\"\n"
        "mode=\"${BOOTSTRAP_DOCKER_MODE:?}\"\n"
        "builder_file=\"${state_dir}/builder-created\"\n"
        "binfmt_file=\"${state_dir}/binfmt-installed\"\n"
        "service_started_file=\"${state_dir}/docker-service-started\"\n"
        "bootstrap=0\n"
        "for arg in \"$@\"; do\n"
        "  if [ \"$arg\" = \"--bootstrap\" ]; then\n"
        "    bootstrap=1\n"
        "  fi\n"
        "done\n"
        "if [ \"${1:-}\" = \"info\" ]; then\n"
        "  if [ \"$mode\" = \"stopped\" ] && [ ! -f \"$service_started_file\" ]; then\n"
        "    printf 'Cannot connect to the Docker daemon\\n' >&2\n"
        "    exit 1\n"
        "  fi\n"
        "  if [ \"$mode\" = \"no-access\" ]; then\n"
        "    printf 'permission denied while trying to connect to Docker\\n' >&2\n"
        "    exit 1\n"
        "  fi\n"
        "  printf 'Docker info ok\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"${1:-}\" = \"version\" ]; then\n"
        "  printf 'Client: Docker Engine - Community\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"${1:-}\" = \"compose\" ] && [ \"${2:-}\" = \"version\" ]; then\n"
        "  printf 'Docker Compose version v2.27.0\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"${1:-}\" = \"run\" ] && [ \"${4:-}\" = \"tonistiigi/binfmt\" ]; then\n"
        "  : > \"$binfmt_file\"\n"
        "  printf 'installed binfmt\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"${1:-}\" = \"buildx\" ] && [ \"${2:-}\" = \"version\" ]; then\n"
        "  printf 'github.com/docker/buildx v0.13.1\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"${1:-}\" = \"buildx\" ] && [ \"${2:-}\" = \"create\" ]; then\n"
        "  : > \"$builder_file\"\n"
        "  printf 'acestream-builder\\n'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"${1:-}\" = \"buildx\" ] && [ \"${2:-}\" = \"inspect\" ]; then\n"
        "  if [ ! -f \"$builder_file\" ]; then\n"
        "    printf 'missing builder\\n' >&2\n"
        "    exit 1\n"
        "  fi\n"
        "  platforms='linux/amd64'\n"
        "  if [ -f \"$binfmt_file\" ]; then\n"
        "    platforms='linux/amd64, linux/arm64, linux/arm/v7'\n"
        "  fi\n"
        "  printf 'Name: acestream-builder\\n'\n"
        "  printf 'Driver: docker-container\\n'\n"
        "  if [ \"$bootstrap\" -eq 1 ]; then\n"
        "    printf 'Status: running\\n'\n"
        "  fi\n"
        "  printf 'Platforms: %s\\n' \"$platforms\"\n"
        "  exit 0\n"
        "fi\n"
        "printf 'unexpected docker call: %s\\n' \"$*\" >&2\n"
        "exit 98\n",
    )


def _write_service_stub(fake_bin: Path) -> None:
    _write_executable(
        fake_bin / "systemctl",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$*\" >> \"${SERVICE_LOG:?}\"\n"
        "if [ \"${1:-}\" = \"enable\" ] && [ \"${2:-}\" = \"--now\" ] && [ \"${3:-}\" = \"docker\" ]; then\n"
        "  : > \"${BOOTSTRAP_TEST_STATE_DIR:?}/docker-service-started\"\n"
        "  exit 0\n"
        "fi\n"
        "printf 'unexpected systemctl call: %s\\n' \"$*\" >&2\n"
        "exit 97\n",
    )


def _write_failing_systemctl_stub(fake_bin: Path) -> None:
    _write_executable(
        fake_bin / "systemctl",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$*\" >> \"${SERVICE_LOG:?}\"\n"
        "printf 'systemctl unavailable\\n' >&2\n"
        "exit 1\n",
    )


def _write_service_start_stub(fake_bin: Path) -> None:
    _write_executable(
        fake_bin / "service",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$*\" >> \"${SERVICE_LOG:?}\"\n"
        "if [ \"${1:-}\" = \"docker\" ] && [ \"${2:-}\" = \"start\" ]; then\n"
        "  : > \"${BOOTSTRAP_TEST_STATE_DIR:?}/docker-service-started\"\n"
        "  exit 0\n"
        "fi\n"
        "printf 'unexpected service call: %s\\n' \"$*\" >&2\n"
        "exit 95\n",
    )


def _write_sudo_stub(fake_bin: Path, *, allow: bool) -> None:
    _write_executable(
        fake_bin / "sudo",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "if [ \"${1:-}\" = \"-n\" ] && [ \"${2:-}\" = \"true\" ]; then\n"
        + ("  exit 0\n" if allow else "  exit 1\n")
        + "fi\n"
        "if [ \"${1:-}\" = \"-n\" ]; then\n"
        "  shift\n"
        "fi\n"
        "exec \"$@\"\n",
    )


def _write_install_path_stubs(fake_bin: Path) -> None:
    _write_executable(
        fake_bin / "dpkg-query",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "package=\"${4:-}\"\n"
        "case \"$package\" in\n"
        "  ca-certificates|curl|gnupg)\n"
        "    printf 'install ok installed'\n"
        "    exit 0\n"
        "    ;;\n"
        "  *)\n"
        "    exit 1\n"
        "    ;;\n"
        "esac\n",
    )
    _write_executable(
        fake_bin / "apt-get",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$*\" >> \"${APT_LOG:?}\"\n"
        "exit 0\n",
    )
    _write_executable(
        fake_bin / "curl",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "if [ \"${1:-}\" = \"-fsSL\" ] && [ \"${3:-}\" = \"-o\" ]; then\n"
        "  printf 'fake-key-data\\n' > \"${4:?}\"\n"
        "  exit 0\n"
        "fi\n"
        "printf 'fake-key-data\\n'\n",
    )
    _write_executable(
        fake_bin / "gpg",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "if [ \"${1:-}\" = \"--show-keys\" ]; then\n"
        "  key_file=\"${2:?}\"\n"
        "  if grep -q 'VALID-KEY' \"$key_file\"; then\n"
        "    exit 0\n"
        "  fi\n"
        "  printf 'invalid keyring\\n' >&2\n"
        "  exit 1\n"
        "fi\n"
        "output=\"\"\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  if [ \"${1:-}\" = \"-o\" ]; then\n"
        "    output=\"${2:?}\"\n"
        "    shift 2\n"
        "    continue\n"
        "  fi\n"
        "  shift\n"
        "done\n"
        "cat >/dev/null\n"
        "printf 'VALID-KEY\\n' > \"$output\"\n",
    )
    _write_executable(
        fake_bin / "tee",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "tmp=\"$(mktemp)\"\n"
        "cat > \"$tmp\"\n"
        "cp \"$tmp\" \"${1:?}\"\n"
        "cat \"$tmp\"\n"
        "rm -f \"$tmp\"\n",
    )


def _bootstrap_env(tmp_path: Path, *, distro: str = "ubuntu", docker_mode: str = "ready") -> tuple[dict[str, str], Path, Path]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    docker_log = tmp_path / "docker.log"
    service_log = tmp_path / "service.log"
    os_release = tmp_path / "os-release"
    os_release.write_text(f"ID={distro}\nVERSION_CODENAME=jammy\n")

    _write_common_tools(fake_bin)
    _write_docker_stub(fake_bin, mode=docker_mode)

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["BOOTSTRAP_OS_RELEASE_FILE"] = str(os_release)
    env["BOOTSTRAP_TEST_STATE_DIR"] = str(state_dir)
    env["BOOTSTRAP_DOCKER_MODE"] = docker_mode
    env["DOCKER_LOG"] = str(docker_log)
    env["SERVICE_LOG"] = str(service_log)

    return env, docker_log, service_log


def test_bootstrap_jenkins_runner_bootstraps_default_builder_after_binfmt(tmp_path):
    env, docker_log, _ = _bootstrap_env(tmp_path)

    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    docker_calls = docker_log.read_text().splitlines()
    creates = [c for c in docker_calls if c.startswith("buildx create --name acestream-builder --driver docker-container")]
    assert creates, docker_calls
    # The builder is created with BuildKit GC limits (the runner's disk is small).
    assert "--buildkitd-config" in creates[0]
    buildkitd = Path(env["BOOTSTRAP_TEST_STATE_DIR"]) / "buildkitd.toml"
    assert buildkitd.is_file()
    assert "gc = true" in buildkitd.read_text() and "max-parallelism" in buildkitd.read_text()
    assert "buildx inspect --bootstrap acestream-builder" in docker_calls
    assert docker_calls.index("run --privileged --rm tonistiigi/binfmt --install all") < docker_calls.index(
        "buildx inspect --bootstrap acestream-builder"
    )
    assert "Builder ready: acestream-builder" in result.stdout
    assert "git version 2.43.0" in result.stdout
    assert "Docker Compose version v2.27.0" in result.stdout


def test_bootstrap_jenkins_runner_rejects_unsupported_distros(tmp_path):
    env, _, _ = _bootstrap_env(tmp_path, distro="fedora")

    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "Unsupported Linux distribution 'fedora'" in result.stderr


def test_bootstrap_jenkins_runner_starts_preinstalled_docker_service_when_daemon_is_stopped(tmp_path):
    env, docker_log, service_log = _bootstrap_env(tmp_path, docker_mode="stopped")
    fake_bin = tmp_path / "bin"
    _write_service_stub(fake_bin)
    _write_sudo_stub(fake_bin, allow=True)

    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "enable --now docker" in service_log.read_text()
    assert "info" in docker_log.read_text()
    assert "Builder ready: acestream-builder" in result.stdout


def test_bootstrap_jenkins_runner_falls_back_to_service_when_systemctl_is_unusable(tmp_path):
    env, _, service_log = _bootstrap_env(tmp_path, docker_mode="stopped")
    fake_bin = tmp_path / "bin"
    _write_failing_systemctl_stub(fake_bin)
    _write_service_start_stub(fake_bin)
    _write_sudo_stub(fake_bin, allow=True)

    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    service_calls = service_log.read_text().splitlines()
    assert "enable --now docker" in service_calls[0]
    assert "docker start" in service_calls[1]


def test_bootstrap_jenkins_runner_repairs_nodesource_keyring_and_enforces_node_20(tmp_path):
    env, _, _ = _bootstrap_env(tmp_path)
    fake_bin = tmp_path / "bin"
    apt_root = tmp_path / "apt-root"
    keyring_dir = apt_root / "keyrings"
    sources_dir = apt_root / "sources.list.d"
    prefs_dir = apt_root / "preferences.d"
    keyring_dir.mkdir(parents=True)
    sources_dir.mkdir(parents=True)
    prefs_dir.mkdir(parents=True)
    (keyring_dir / "nodesource.gpg").write_text("")
    apt_log = tmp_path / "apt.log"

    _write_install_path_stubs(fake_bin)
    _write_sudo_stub(fake_bin, allow=True)

    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={
            **env,
            "BOOTSTRAP_TEST_NODE_VERSION": "v18.19.0",
            "BOOTSTRAP_KEYRING_DIR": str(keyring_dir),
            "BOOTSTRAP_SOURCES_LIST_DIR": str(sources_dir),
            "BOOTSTRAP_PREFERENCES_DIR": str(prefs_dir),
            "APT_LOG": str(apt_log),
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "install -y --allow-downgrades nodejs" in apt_log.read_text()
    assert (keyring_dir / "nodesource.gpg").read_text() == "VALID-KEY\n"
    assert "node_20.x" in (sources_dir / "nodesource.list").read_text()
    prefs = (prefs_dir / "nodesource").read_text()
    assert "Pin: origin deb.nodesource.com" in prefs
    assert "Pin-Priority: 1001" in prefs


def test_bootstrap_jenkins_runner_installs_npm_when_distro_nodejs_shadows(tmp_path):
    """A distro nodejs (e.g. Ubuntu's node 24) without npm must not satisfy
    the bootstrap: the NodeSource pin is written and nodejs is (re)installed,
    after which npm exists."""
    env, _, _ = _bootstrap_env(tmp_path)
    fake_bin = tmp_path / "bin"
    apt_root = tmp_path / "apt-root"
    keyring_dir = apt_root / "keyrings"
    sources_dir = apt_root / "sources.list.d"
    prefs_dir = apt_root / "preferences.d"
    keyring_dir.mkdir(parents=True)
    sources_dir.mkdir(parents=True)
    prefs_dir.mkdir(parents=True)
    apt_log = tmp_path / "apt.log"

    _write_install_path_stubs(fake_bin)
    _write_sudo_stub(fake_bin, allow=True)

    # The runner image ships a distro nodejs without npm.
    (fake_bin / "npm").unlink()
    # Installing nodejs (now pinned to NodeSource) brings npm with it.
    _write_executable(
        fake_bin / "apt-get",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$*\" >> \"${APT_LOG:?}\"\n"
        "if [[ \"$*\" == *install* && \"$*\" == *nodejs* ]]; then\n"
        f"  printf '#!/bin/bash\\nprintf 10.8.2\\\\n\\n' > \"{fake_bin}/npm\"\n"
        f"  chmod +x \"{fake_bin}/npm\"\n"
        "fi\n"
        "exit 0\n",
    )

    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={
            **env,
            "BOOTSTRAP_TEST_NODE_VERSION": "v24.4.0",
            "BOOTSTRAP_KEYRING_DIR": str(keyring_dir),
            "BOOTSTRAP_SOURCES_LIST_DIR": str(sources_dir),
            "BOOTSTRAP_PREFERENCES_DIR": str(prefs_dir),
            "APT_LOG": str(apt_log),
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "install -y --allow-downgrades nodejs" in apt_log.read_text()
    prefs = (prefs_dir / "nodesource").read_text()
    assert "Package: nodejs" in prefs
    assert "Pin: origin deb.nodesource.com" in prefs
    assert "Pin-Priority: 1001" in prefs
    assert (fake_bin / "npm").exists()


def test_bootstrap_jenkins_runner_repairs_invalid_nodesource_keyring(tmp_path):
    env, _, _ = _bootstrap_env(tmp_path)
    fake_bin = tmp_path / "bin"
    apt_root = tmp_path / "apt-root"
    keyring_dir = apt_root / "keyrings"
    sources_dir = apt_root / "sources.list.d"
    prefs_dir = apt_root / "preferences.d"
    keyring_dir.mkdir(parents=True)
    sources_dir.mkdir(parents=True)
    prefs_dir.mkdir(parents=True)
    (keyring_dir / "nodesource.gpg").write_text("truncated-but-nonempty\n")
    apt_log = tmp_path / "apt.log"

    _write_install_path_stubs(fake_bin)
    _write_sudo_stub(fake_bin, allow=True)

    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={
            **env,
            "BOOTSTRAP_TEST_NODE_VERSION": "v18.19.0",
            "BOOTSTRAP_KEYRING_DIR": str(keyring_dir),
            "BOOTSTRAP_SOURCES_LIST_DIR": str(sources_dir),
            "BOOTSTRAP_PREFERENCES_DIR": str(prefs_dir),
            "APT_LOG": str(apt_log),
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Configuring NodeSource apt key" in result.stdout
    assert (keyring_dir / "nodesource.gpg").read_text() == "VALID-KEY\n"
    assert "install -y --allow-downgrades nodejs" in apt_log.read_text()


def test_bootstrap_jenkins_runner_is_idempotent_on_second_run(tmp_path):
    env, docker_log, _ = _bootstrap_env(tmp_path)

    first = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert first.returncode == 0, first.stdout + first.stderr

    docker_log.write_text("")

    second = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert second.returncode == 0, second.stdout + second.stderr
    docker_calls = docker_log.read_text().splitlines()
    assert not any(c.startswith("buildx create --name acestream-builder") for c in docker_calls), docker_calls
    assert "run --privileged --rm tonistiigi/binfmt --install all" not in docker_calls


def test_bootstrap_jenkins_runner_fails_cleanly_when_install_requires_passwordless_sudo(tmp_path):
    env, _, _ = _bootstrap_env(tmp_path)
    fake_bin = tmp_path / "bin"
    (fake_bin / "node").unlink()
    (fake_bin / "npm").unlink()
    _write_executable(
        fake_bin / "id",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "if [ \"${1:-}\" = \"-un\" ]; then\n"
        "  printf 'unknown-user\\n'\n"
        "  exit 0\n"
        "fi\n"
        "printf 'unexpected id call: %s\\n' \"$*\" >&2\n"
        "exit 96\n",
    )
    _write_sudo_stub(fake_bin, allow=False)

    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**{k: v for k, v in env.items() if k != "USER"}, "PATH": str(fake_bin)},
    )

    assert result.returncode != 0
    assert "passwordless sudo is unavailable" in result.stderr
    assert "user 'unknown-user'" in result.stderr


def test_bootstrap_jenkins_runner_skips_warp_unless_enabled(tmp_path):
    """WARP setup is opt-in: the engine archives are vendored, and the setup
    needs passwordless sudo that developer machines and this harness lack."""
    env, _, _ = _bootstrap_env(tmp_path)
    env.pop("JENKINS_ENABLE_WARP", None)
    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "WARP setup skipped" in result.stdout
    assert "setup_jenkins_warp" not in result.stdout


def test_bootstrap_jenkins_runner_warp_failure_is_a_warning(tmp_path):
    """With JENKINS_ENABLE_WARP=1 the hook runs, but a failing WARP setup must
    not fail the bootstrap (only non-vendored downloads need WARP)."""
    env, _, _ = _bootstrap_env(tmp_path)
    warp_stub = tmp_path / "warp-stub.sh"
    warp_stub.write_text("#!/usr/bin/env bash\necho 'stub warp setup ran'\nexit 1\n")
    warp_stub.chmod(0o755)
    env["JENKINS_ENABLE_WARP"] = "1"
    env["BOOTSTRAP_WARP_SCRIPT"] = str(warp_stub)
    result = subprocess.run(
        ["/bin/bash", str(BOOTSTRAP_SCRIPT)],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "stub warp setup ran" in result.stdout
    assert "WARP setup failed; continuing" in result.stderr
