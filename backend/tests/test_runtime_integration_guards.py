import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


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
