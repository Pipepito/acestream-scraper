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


def test_docker_compose_wires_embedded_ipfs_defaults():
    compose_file = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "- ENABLE_IPFS=false" in compose_file
    assert "- ./ipfs_data:/data/ipfs" in compose_file


def test_docker_compose_wires_embedded_zeronet_defaults():
    compose_file = (REPO_ROOT / "docker-compose.yml").read_text()

    assert "- ENABLE_ZERONET=false" in compose_file
    # External mode stays the compose default; the sidecar profile remains.
    assert "ZERONET_URL=http://host.docker.internal:43110" in compose_file


def test_entrypoint_gates_embedded_zeronet_on_installed_launcher():
    entrypoint = (REPO_ROOT / "entrypoint.sh").read_text()

    assert "ENABLE_ZERONET" in entrypoint
    assert "IMAGE_HAS_ZERONET" in entrypoint
    assert 'ZERONET_UI_PORT="${ZERONET_UI_PORT:-43110}"' in entrypoint
    assert 'ZERONET_FILESERVER_PORT="${ZERONET_FILESERVER_PORT:-26552}"' in entrypoint
    # ENABLE_ZERONET=true must repoint the baked ZERONET_URL default at the
    # embedded node's UI port.
    assert 'ZERONET_URL="http://127.0.0.1:$ZERONET_UI_PORT"' in entrypoint


def test_entrypoint_gates_ipfs_on_installed_binary_and_reserves_gateway_port():
    entrypoint = (REPO_ROOT / "entrypoint.sh").read_text()

    assert "ENABLE_IPFS" in entrypoint
    assert "IMAGE_HAS_IPFS" in entrypoint
    # Acexy owns 8080 in-container, so the embedded gateway must default to 8081.
    assert 'IPFS_GATEWAY_PORT="${IPFS_GATEWAY_PORT:-8081}"' in entrypoint
    assert 'IPFS_GATEWAY_URL="${IPFS_GATEWAY_URL:-http://127.0.0.1:$IPFS_GATEWAY_PORT}"' in entrypoint


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


def test_build_script_derives_real_acexy_source_from_manifest():
    # Without ACEXY_REPO/ACEXY_REF the Dockerfile compiles the test fixture
    # (a stub that prints "fixture acexy" and exits). The canonical build
    # script must derive them from docker/manifests/acexy.json for every
    # acexy-bearing flavor so published images ship the real proxy.
    script = (REPO_ROOT / "scripts" / "ci" / "build_multiarch_images.sh").read_text()
    assert 'ACEXY_MANIFEST="$ROOT_DIR/docker/manifests/acexy.json"' in script
    assert 'ACEXY_BEARING_FLAVORS=("scraper-acexy" "scraper-acestream-acexy")' in script
    manifest = json.loads((REPO_ROOT / "docker" / "manifests" / "acexy.json").read_text())

    for flavor in ("scraper-acexy", "scraper-acestream-acexy"):
        result = subprocess.run(
            [
                "/bin/bash",
                str(REPO_ROOT / "scripts/ci/build_multiarch_images.sh"),
                "--dry-run", "--flavor", flavor,
                "--result-file", f"/tmp/acexy-dryrun-{flavor}.json",
            ],
            cwd=REPO_ROOT, check=False, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        out = result.stdout + result.stderr
        assert f"ACEXY_REPO={manifest['repo']}" in out, out
        assert f"ACEXY_REF={manifest['ref']}" in out, out

    result = subprocess.run(
        [
            "/bin/bash",
            str(REPO_ROOT / "scripts/ci/build_multiarch_images.sh"),
            "--dry-run", "--flavor", "scraper",
            "--result-file", "/tmp/acexy-dryrun-scraper.json",
        ],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ACEXY_REPO" not in result.stdout + result.stderr


def test_run_jenkins_release_channel_plan_pushes_floating_channel_tags_only():
    # The develop pre-release channel publishes floating channel tags per
    # flavor and never a version tag or :latest.
    result = subprocess.run(
        ["/bin/bash", str(REPO_ROOT / "scripts/ci/run_jenkins_release.sh"),
         "--print-publish-plan", "--channel", "develop"],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True, env=os.environ.copy(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    version = (REPO_ROOT / "version.txt").read_text().strip()
    assert "pipepito/acestream-scraper:develop " in result.stdout or "pipepito/acestream-scraper:develop\n" in result.stdout
    for flavor in ("scraper", "scraper-acestream", "scraper-acexy", "scraper-acestream-acexy"):
        assert f"pipepito/acestream-scraper:develop-{flavor}" in result.stdout, result.stdout
    assert "pipepito/acestream-scraper:latest" not in result.stdout
    assert f"pipepito/acestream-scraper:{version}" not in result.stdout


def test_run_jenkins_release_rejects_invalid_channel_names():
    result = subprocess.run(
        ["/bin/bash", str(REPO_ROOT / "scripts/ci/run_jenkins_release.sh"),
         "--print-publish-plan", "--channel", "Not Valid"],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "Invalid channel name" in result.stderr


def test_run_jenkins_release_refuses_dev_versions(tmp_path):
    # develop carries vX.Y.Z-dev; only the release PR bumps it, so a release
    # run on a -dev version must stop before doing anything.
    import shutil
    scripts_dir = tmp_path / "scripts" / "ci"
    scripts_dir.mkdir(parents=True)
    shutil.copy(REPO_ROOT / "scripts/ci/run_jenkins_release.sh", scripts_dir / "run_jenkins_release.sh")
    (tmp_path / "version.txt").write_text("v2.1.0-dev\n")
    result = subprocess.run(
        ["/bin/bash", str(scripts_dir / "run_jenkins_release.sh"), "--print-publish-plan"],
        cwd=tmp_path, check=False, capture_output=True, text=True,
    )
    assert result.returncode != 0
    assert "Refusing to release a development version" in result.stderr
    # ...while the channel publish of the same tree is fine.
    result = subprocess.run(
        ["/bin/bash", str(scripts_dir / "run_jenkins_release.sh"), "--print-publish-plan", "--channel", "develop"],
        cwd=tmp_path, check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr


def test_build_script_multi_platform_push_is_sequential_by_digest():
    # A multi-platform --push builds one platform at a time, pushes each by
    # digest and assembles every tag with imagetools; registry host:port
    # prefixes must survive the repository parsing.
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts/ci/build_multiarch_images.sh"), "--dry-run",
         "--flavor", "scraper", "--push",
         "--tag", "localhost:5055/acestream-scraper:seq", "--tag", "localhost:5055/acestream-scraper:seq-2"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    out = result.stdout
    assert out.count("push-by-digest=true") == 3, out
    assert "name=localhost:5055/acestream-scraper" in out  # (commas are %q-escaped in dry-run output)
    assert out.count("Building linux/") == 3
    assert "imagetools create --tag localhost:5055/acestream-scraper:seq --tag localhost:5055/acestream-scraper:seq-2" in out
    assert "--push " not in out  # never a single multi-platform --push build

    mixed = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts/ci/build_multiarch_images.sh"), "--dry-run",
         "--flavor", "scraper", "--push", "--tag", "a/app:1", "--tag", "b/app:1"],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True,
    )
    assert mixed.returncode != 0 and "share one repository" in mixed.stderr

    single = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts/ci/build_multiarch_images.sh"), "--dry-run",
         "--flavor", "scraper", "--platforms", "linux/amd64", "--push", "--tag", "a/app:1"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    assert "--push" in single.stdout and "imagetools" not in single.stdout


def test_build_script_push_by_digest_single_platform():
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts/ci/build_multiarch_images.sh"), "--dry-run",
         "--flavor", "scraper-acexy", "--platforms", "linux/arm/v7", "--push-by-digest",
         "--repo", "example.com/app", "--prune-builder-after", "2GB", "--builder", "acestream-builder"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    out = result.stdout
    assert "push-by-digest=true" in out and "name=example.com/app" in out
    assert "Pushed linux/arm/v7 as example.com/app@" in out
    assert "docker buildx prune --builder acestream-builder -f --max-used-space 2GB" in out
    assert "imagetools" not in out and "--tag" not in out

    bad = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts/ci/build_multiarch_images.sh"), "--dry-run",
         "--flavor", "scraper", "--push-by-digest", "--repo", "example.com/app"],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True,
    )
    assert bad.returncode != 0 and "exactly one platform" in bad.stdout + bad.stderr


def test_run_jenkins_release_channel_dry_run_is_platform_major(tmp_path):
    # Every flavor is built for one platform before the next platform, each
    # pushed by digest, the builder cache is pruned between platforms, and the
    # tags are assembled per flavor at the end.
    env = os.environ.copy()
    env.pop("PUBLISH_LATEST", None)
    # The release script deliberately verifies its configured builder even for a
    # dry run. Keep this contract test independent of the host's Docker daemon.
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(fake_bin / "docker", "#!/usr/bin/env bash\nexit 0\n")
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["JENKINS_BUILDER"] = "default"
    result = subprocess.run(
        ["/bin/bash", str(REPO_ROOT / "scripts/ci/run_jenkins_release.sh"), "--dry-run", "--channel", "develop"],
        cwd=REPO_ROOT, check=False, capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    out = result.stdout
    builds = [line for line in out.splitlines() if line.startswith("Building linux/")]
    assert len(builds) == 12, builds  # 4 flavors x 3 platforms
    # platform-major: the first four builds are all for the first platform
    assert {line.split()[1] for line in builds[:4]} == {"linux/amd64"}
    assert out.count("docker buildx prune --builder default") == 3
    assert out.count("imagetools create") == 4
    assert "--tag pipepito/acestream-scraper:develop " in out
    assert "pipepito/acestream-scraper:latest" not in out
