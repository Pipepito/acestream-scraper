"""The local gate picks its tier from the same selector Jenkins uses."""

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL).decode().strip()


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "scripts/ci").mkdir(parents=True)
    for name in ("local_gate.sh", "classify_changes.py"):
        shutil.copyfile(ROOT / "scripts/ci" / name, tmp_path / "scripts/ci" / name)
    (tmp_path / "README.md").write_text("project\n")
    git(tmp_path, "init", "-q", "-b", "develop")
    git(tmp_path, "config", "user.email", "ci@example.invalid")
    git(tmp_path, "config", "user.name", "CI test")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "base")
    return tmp_path


def plan(repo, *arguments):
    return subprocess.run(["bash", "scripts/ci/local_gate.sh", "--plan", *arguments], cwd=repo,
                          capture_output=True, text=True)


def change(repo, path, committed=False):
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("changed\n")
    if committed:
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "change")


@pytest.mark.parametrize("path, tier, expected, unexpected", [
    ("wiki/Home.md", "docs", ["validate_documentation.py"], ["run_v2_test_suite.sh", "validate_docker_flavor_targets.sh"]),
    (".github/rulesets/reviews.json", "docs", ["validate_repository_metadata.sh"], ["run_v2_test_suite.sh"]),
    ("backend/app/services/epg_service.py", "application", ["run_v2_test_suite.sh --profile full"],
     ["validate_docker_flavor_targets.sh", "test:mobile", "live journey"]),
    ("frontend/src/App.tsx", "application", ["run_v2_test_suite.sh --profile full", "test:mobile"],
     ["validate_docker_flavor_targets.sh", "live journey"]),
    ("backend/app/services/player_service.py", "application", ["run_v2_test_suite.sh", "live journey"],
     ["validate_docker_flavor_targets.sh"]),
    ("Dockerfile", "images", ["validate_docker_flavor_targets.sh", "backend/tests/docker", "live journey"], []),
    ("backend/requirements.txt", "images", ["validate_docker_flavor_targets.sh"], []),
    ("unrecognized.bin", "images", ["validate_docker_flavor_targets.sh"], []),
])
@pytest.mark.parametrize("committed", [False, True])
def test_tier_follows_the_change(repo, path, tier, expected, unexpected, committed):
    git(repo, "checkout", "-qb", "feature")
    change(repo, path, committed)
    result = plan(repo, "--base", "develop")
    assert result.returncode == 0, result.stderr
    assert f"needs the '{tier}' tier" in result.stdout
    assert "Cross-architecture image builds are left to Jenkins." in result.stdout
    for text in expected:
        assert text in result.stdout
    for text in unexpected:
        assert text not in result.stdout
    assert "--platform" not in result.stdout and "linux/amd64" not in result.stdout.replace("PLATFORM=linux/amd64", "")


def test_mixed_changes_take_the_highest_tier(repo):
    git(repo, "checkout", "-qb", "feature")
    change(repo, "wiki/Home.md", committed=True)
    change(repo, "frontend/src/App.tsx", committed=True)
    assert "needs the 'application' tier" in plan(repo, "--base", "develop").stdout
    change(repo, "docker/manifests/platforms.json")  # Uncommitted work counts too.
    assert "needs the 'images' tier" in plan(repo, "--base", "develop").stdout


def test_tier_can_be_raised_but_never_lowered(repo):
    git(repo, "checkout", "-qb", "feature")
    change(repo, "frontend/src/App.tsx")
    raised = plan(repo, "--base", "develop", "--tier", "images")
    assert raised.returncode == 0 and "needs the 'images' tier" in raised.stdout
    lowered = plan(repo, "--base", "develop", "--tier", "docs")
    assert lowered.returncode == 2 and "refusing to lower" in lowered.stderr
    assert plan(repo, "--base", "develop", "--tier", "everything").returncode == 2


def test_no_changes_and_unknown_targets_are_reported(repo):
    assert "nothing to validate" in plan(repo, "--base", "develop").stdout
    missing = plan(repo, "--base", "no-such-branch")
    assert missing.returncode == 2 and "--base" in missing.stderr


def test_missing_prerequisites_block_instead_of_passing(repo):
    git(repo, "checkout", "-qb", "feature")
    change(repo, "backend/app/main.py")
    result = subprocess.run(["bash", "scripts/ci/local_gate.sh", "--base", "develop"], cwd=repo,
                            capture_output=True, text=True)
    assert result.returncode == 3
    assert "backend/venv is missing" in result.stderr
    assert "passed" not in result.stdout
