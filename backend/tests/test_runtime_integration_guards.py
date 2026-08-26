import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def test_backend_requirements_include_apscheduler():
    requirements = (REPO_ROOT / "backend" / "requirements.txt").read_text()

    assert "apscheduler" in requirements.lower()


def test_build_backend_script_uses_node_copy_script():
    package_json = json.loads((REPO_ROOT / "frontend" / "package.json").read_text())

    assert package_json["scripts"]["build"] == "vite build"
    assert package_json["scripts"]["build:backend"] == "vite build && node scripts/copy-build.js"


def test_frontend_container_builds_from_vite_dist_directory():
    frontend_dockerfile = (REPO_ROOT / "frontend" / "Dockerfile").read_text()
    root_dockerfile = (REPO_ROOT / "Dockerfile").read_text()

    assert "COPY --from=build /app/dist /usr/share/nginx/html" in frontend_dockerfile
    assert "COPY --from=frontend-builder /build/frontend/dist/ /app/frontend_build/" in root_dockerfile


def test_copy_build_script_copies_artifacts_with_overrides(tmp_path):
    source_dir = tmp_path / "build"
    static_dir = source_dir / "static"
    destination_dir = tmp_path / "frontend_build"

    static_dir.mkdir(parents=True)
    (source_dir / "index.html").write_text("<html>ok</html>")
    (static_dir / "app.js").write_text("console.log('ok')")

    env = os.environ.copy()
    env["COPY_BUILD_SOURCE"] = str(source_dir)
    env["COPY_BUILD_DESTINATION"] = str(destination_dir)

    subprocess.run(
        ["node", str(REPO_ROOT / "frontend" / "scripts" / "copy-build.js")],
        check=True,
        cwd=REPO_ROOT / "frontend",
        env=env,
    )

    assert (destination_dir / "index.html").read_text() == "<html>ok</html>"
    assert (destination_dir / "static" / "app.js").read_text() == "console.log('ok')"


def test_copy_build_script_removes_stale_artifacts_from_destination(tmp_path):
    source_dir = tmp_path / "build"
    assets_dir = source_dir / "assets"
    destination_dir = tmp_path / "frontend_build"
    stale_assets_dir = destination_dir / "assets"

    assets_dir.mkdir(parents=True)
    stale_assets_dir.mkdir(parents=True)
    (source_dir / "index.html").write_text("<html>fresh</html>")
    (assets_dir / "index-new.js").write_text("fresh bundle")
    (stale_assets_dir / "index-old.js").write_text("stale bundle")

    env = os.environ.copy()
    env["COPY_BUILD_SOURCE"] = str(source_dir)
    env["COPY_BUILD_DESTINATION"] = str(destination_dir)

    subprocess.run(
        ["node", str(REPO_ROOT / "frontend" / "scripts" / "copy-build.js")],
        check=True,
        cwd=REPO_ROOT / "frontend",
        env=env,
    )

    assert (destination_dir / "index.html").read_text() == "<html>fresh</html>"
    assert (destination_dir / "assets" / "index-new.js").read_text() == "fresh bundle"
    assert not (destination_dir / "assets" / "index-old.js").exists()


def test_docker_compose_uses_root_dockerfile_for_app_image():
    compose_file = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "dockerfile: Dockerfile" in compose_file
    assert "dockerfile: backend/Dockerfile" not in compose_file


def test_docker_compose_pins_zeronet_platform_for_arm_hosts():
    compose_file = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "image: nofish/zeronet:latest" in compose_file
    assert "platform: linux/amd64" in compose_file


def test_legacy_path_guard_accepts_current_runtime_contract():
    result = subprocess.run(
        ["bash", "scripts/ci/assert_no_legacy_paths.sh", "--strict"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_legacy_path_guard_covers_jenkins_entrypoints():
    guard_script = (REPO_ROOT / "scripts" / "ci" / "assert_no_legacy_paths.sh").read_text()

    assert '"Jenkinsfile"' in guard_script
    assert '"jenkins/release.Jenkinsfile"' in guard_script
    assert '"scripts/ci/run_jenkins_validation.sh"' in guard_script
    assert '"scripts/ci/run_jenkins_release.sh"' in guard_script


def test_jenkins_validation_wrapper_fails_fast_when_builder_is_missing(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_bash_log = tmp_path / "fake-bash.log"

    _write_executable(
        fake_bin / "bash",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$*\" >> \"${FAKE_BASH_LOG:?}\"\n"
        "printf 'unexpected downstream bash call: %s\\n' \"$*\" >&2\n"
        "exit 99\n",
    )
    _write_executable(
        fake_bin / "docker",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "if [ \"${1:-}\" = \"buildx\" ] && [ \"${2:-}\" = \"inspect\" ]; then\n"
        "  printf 'missing builder: %s\\n' \"${3:-}\" >&2\n"
        "  exit 1\n"
        "fi\n"
        "printf 'unexpected docker call: %s\\n' \"$*\" >&2\n"
        "exit 98\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["FAKE_BASH_LOG"] = str(fake_bash_log)
    env["JENKINS_BUILDER"] = "missing-builder"

    result = subprocess.run(
        ["/bin/bash", str(REPO_ROOT / "scripts/ci/run_jenkins_validation.sh")],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "missing-builder" in (result.stdout + result.stderr)
    assert not fake_bash_log.exists() or fake_bash_log.read_text() == ""


def test_jenkins_release_wrapper_fails_fast_when_builder_is_missing(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_bash_log = tmp_path / "fake-bash.log"

    _write_executable(
        fake_bin / "bash",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$*\" >> \"${FAKE_BASH_LOG:?}\"\n"
        "printf 'unexpected downstream bash call: %s\\n' \"$*\" >&2\n"
        "exit 99\n",
    )
    _write_executable(
        fake_bin / "docker",
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "if [ \"${1:-}\" = \"buildx\" ] && [ \"${2:-}\" = \"inspect\" ]; then\n"
        "  printf 'missing builder: %s\\n' \"${3:-}\" >&2\n"
        "  exit 1\n"
        "fi\n"
        "printf 'unexpected docker call: %s\\n' \"$*\" >&2\n"
        "exit 98\n",
    )

    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["FAKE_BASH_LOG"] = str(fake_bash_log)
    env["JENKINS_BUILDER"] = "missing-builder"

    result = subprocess.run(
        ["/bin/bash", str(REPO_ROOT / "scripts/ci/run_jenkins_release.sh"), "--dry-run"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "missing-builder" in (result.stdout + result.stderr)
    assert not fake_bash_log.exists() or fake_bash_log.read_text() == ""


def test_jenkins_release_pipeline_verifies_checkout_matches_origin_main():
    pipeline = (REPO_ROOT / "jenkins" / "release.Jenkinsfile").read_text()

    assert "git fetch --no-tags origin main" in pipeline
    assert 'head_sha="$(git rev-parse HEAD)"' in pipeline
    assert 'origin_main_sha="$(git rev-parse origin/main)"' in pipeline
    assert 'if [[ "$head_sha" != "$origin_main_sha" ]]; then' in pipeline
    assert "Release pipeline requires the checked-out commit to match origin/main." in pipeline


def test_jenkins_release_pipeline_exposes_publish_latest_parameter():
    pipeline = (REPO_ROOT / "jenkins" / "release.Jenkinsfile").read_text()

    assert "name: 'PUBLISH_LATEST'" in pipeline
    assert "defaultValue: false" in pipeline
    assert "PUBLISH_LATEST=${params.PUBLISH_LATEST ? '1' : '0'}" in pipeline
    assert "run_jenkins_release.sh --print-publish-plan" in pipeline


def test_run_jenkins_release_print_publish_plan_default_excludes_latest():
    # Without PUBLISH_LATEST set, the publish plan must not include the
    # floating :latest tag. This protects the canary flow: the first publish
    # of a new version pushes only the versioned + flavor-channel tags so
    # users on :latest are unaffected until an opt-in promotion run.
    env = os.environ.copy()
    env.pop("PUBLISH_LATEST", None)

    result = subprocess.run(
        [
            "/bin/bash",
            str(REPO_ROOT / "scripts/ci/run_jenkins_release.sh"),
            "--print-publish-plan",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "pipepito/acestream-scraper:latest" not in result.stdout, result.stdout
    assert "pipepito/acestream-scraper:scraper-acestream-acexy" in result.stdout
    assert "pipepito/acestream-scraper:scraper" in result.stdout


def test_run_jenkins_release_print_publish_plan_with_publish_latest_includes_latest():
    env = os.environ.copy()
    env["PUBLISH_LATEST"] = "1"

    result = subprocess.run(
        [
            "/bin/bash",
            str(REPO_ROOT / "scripts/ci/run_jenkins_release.sh"),
            "--print-publish-plan",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "pipepito/acestream-scraper:latest" in result.stdout, result.stdout


def test_run_jenkins_release_publish_latest_only_promotes_full_payload_flavor():
    # Even when PUBLISH_LATEST=1, only the scraper-acestream-acexy flavor
    # (the canonical :latest payload) should receive the floating :latest tag.
    # The partial flavors must continue to be addressable only via channel +
    # versioned tags so an operator can never accidentally promote a partial
    # build to :latest.
    env = os.environ.copy()
    env["PUBLISH_LATEST"] = "1"

    result = subprocess.run(
        [
            "/bin/bash",
            str(REPO_ROOT / "scripts/ci/run_jenkins_release.sh"),
            "--print-publish-plan",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count(":latest") == 1, result.stdout
