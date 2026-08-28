"""scripts/ci/cleanup_runner_docker.sh must only target this repo's transient
CI images, honour --keep, and respect the age threshold (fake docker CLI)."""
from __future__ import annotations

import os
import stat
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ci" / "cleanup_runner_docker.sh"


def _fake_docker(tmp_path: Path, images: list[tuple[str, datetime]]) -> Path:
    listing_file = tmp_path / "images.txt"
    listing_file.write_text(
        "".join(f"{ref}|{ts.strftime('%Y-%m-%d %H:%M:%S %z')} UTC\n" for ref, ts in images)
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "docker"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        f"if [ \"$1\" = images ]; then cat '{listing_file}'; exit 0; fi\n"
        "echo \"docker $*\" >> \"$DOCKER_CALLS\"\n"
        "exit 0\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    return bin_dir


def _run(tmp_path: Path, bin_dir: Path, *args: str) -> tuple[str, list[str]]:
    calls = tmp_path / "calls.log"
    calls.write_text("")
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "DOCKER_CALLS": str(calls)}
    out = subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=env, check=True).stdout
    return out, [line for line in calls.read_text().splitlines() if line]


def test_removes_only_old_transient_images_and_keeps_current(tmp_path: Path):
    now = datetime.now(timezone.utc)
    old, fresh = now - timedelta(hours=5), now - timedelta(minutes=10)
    images = [
        ("acestream-scraper:smoke-PR-113-28", old),        # leaked smoke image -> remove
        ("acestream-scraper:smoke-29", old),               # legacy per-number tag -> remove
        ("acestream-installer-test:apk-armeabi-v7a", old),  # crashed pytest leftover -> remove
        ("acestream-scraper-smoke:scraper-acexy-1a2b3c4d", fresh),  # other job, in flight -> keep (fresh)
        ("acestream-scraper:smoke-PR-113-30", old),        # current build -> keep (--keep)
        ("pipepito/acestream-scraper:latest", old),        # not transient -> never targeted here
        ("python:3.11-slim", old),
    ]
    bin_dir = _fake_docker(tmp_path, images)
    out, calls = _run(tmp_path, bin_dir, "--keep", "acestream-scraper:smoke-PR-113-30", "--transient-age-hours", "3")

    rm_calls = [c for c in calls if c.startswith("docker image rm -f")]
    assert len(rm_calls) == 1, calls
    removed = set(rm_calls[0].split()[4:])
    assert removed == {
        "acestream-scraper:smoke-PR-113-28",
        "acestream-scraper:smoke-29",
        "acestream-installer-test:apk-armeabi-v7a",
    }
    assert "docker image prune -f" in calls
    assert "docker image prune -af --filter until=24h" in calls
    assert any(c.startswith("docker buildx prune -f --max-used-space 20GB") for c in calls)


def test_dry_run_touches_nothing(tmp_path: Path):
    old = datetime.now(timezone.utc) - timedelta(hours=9)
    bin_dir = _fake_docker(tmp_path, [("acestream-scraper:smoke-7", old)])
    out, calls = _run(tmp_path, bin_dir, "--dry-run")
    assert "[dry-run] docker image rm -f acestream-scraper:smoke-7" in out
    assert not any(c.startswith("docker image rm") or "prune" in c for c in calls)
