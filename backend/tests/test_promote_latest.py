"""scripts/ci/promote_latest.sh must retag the published version manifest to
:latest (never rebuild) and refuse when the version was never published."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ci" / "promote_latest.sh"


def _fake_docker(tmp_path: Path, *, inspect_rc: int) -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.log"
    calls.write_text("")
    fake = bin_dir / "docker"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        'echo "docker $*" >> "$DOCKER_CALLS"\n'
        f'if [ "$1 $2 $3" = "buildx imagetools inspect" ]; then exit {inspect_rc}; fi\n'
        # verify_multiarch_manifest.sh reads the raw manifest list of :latest
        'if [ "$1 $2 $3" = "buildx imagetools inspect" ] || [ "$4" = "--raw" ]; then :; fi\n'
        "exit 0\n"
    )
    fake.chmod(0o755)
    return bin_dir, calls


def _run(bin_dir: Path, calls: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "DOCKER_CALLS": str(calls)}
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env, cwd=REPO_ROOT)


def test_dry_run_prints_plan_and_calls_nothing(tmp_path: Path):
    bin_dir, calls = _fake_docker(tmp_path, inspect_rc=0)
    result = _run(bin_dir, calls, "--version", "v9.9.9", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "pipepito/acestream-scraper:latest <- pipepito/acestream-scraper:v9.9.9" in result.stdout
    assert "imagetools create -t pipepito/acestream-scraper:latest pipepito/acestream-scraper:v9.9.9" in result.stdout
    assert calls.read_text() == ""


def test_refuses_when_version_manifest_is_missing(tmp_path: Path):
    bin_dir, calls = _fake_docker(tmp_path, inspect_rc=1)
    result = _run(bin_dir, calls, "--version", "v9.9.9")
    assert result.returncode != 0
    assert "not in the registry" in result.stderr
    assert "imagetools create" not in calls.read_text()


def test_version_is_required(tmp_path: Path):
    bin_dir, calls = _fake_docker(tmp_path, inspect_rc=0)
    result = _run(bin_dir, calls)
    assert result.returncode != 0 and "--version is required" in result.stderr
