"""Exercise Pages publication against a disposable local Git remote."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


@pytest.fixture
def pages(tmp_path):
    repo, remote = tmp_path / "source", tmp_path / "remote.git"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.invalid")
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    git(repo, "remote", "add", "origin", str(remote))
    (repo / "scripts/ci").mkdir(parents=True)
    shutil.copy(ROOT / "scripts/ci/publish_pages.sh", repo / "scripts/ci")
    (repo / "docs/builder").mkdir(parents=True)
    (repo / "docs/index.html").write_text("initial docs")
    (repo / "docs/builder/runtime-options.json").write_text("{}")
    (repo / "version.txt").write_text("v2.0.0\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", "Fixture")
    git(repo, "push", "-q", "origin", "main")
    metadata = {
        "mode": "promote-latest", "version": "v2.0.0",
        "git_sha": git(repo, "rev-parse", "HEAD"),
        "generated_at": "2026-09-09T00:00:00+00:00",
    }
    (repo / "phase5-build-result-release-metadata.json").write_text(json.dumps(metadata))
    return repo, remote, metadata


def publish(repo, *args):
    return subprocess.run(
        ["bash", "scripts/ci/publish_pages.sh", *args], cwd=repo,
        env={**os.environ, "GITHUB_PUBLISH_USERNAME": "test",
             "GITHUB_PUBLISH_TOKEN": "local-fixture", "PAGES_BRANCH": "gh-pages",
             "PAGES_REMOTE_URL": git(repo, "remote", "get-url", "origin")},
        capture_output=True, text=True, timeout=30,
    )


def test_production_label_survives_later_develop_publish(pages):
    repo, remote, metadata = pages
    initial = publish(repo)
    assert initial.returncode == 0, initial.stderr
    assert "release-status.json" not in git(remote, "ls-tree", "--name-only", "gh-pages")
    promoted = publish(repo, "--promoted-release")
    assert promoted.returncode == 0, promoted.stderr
    status = git(remote, "show", "gh-pages:release-status.json")
    assert json.loads(status)["version"] == "v2.0.0"
    assert json.loads(status)["gitSha"] == metadata["git_sha"]
    git(repo, "checkout", "-qb", "develop")
    (repo / "docs/index.html").write_text("next development docs")
    developed = publish(repo)
    assert developed.returncode == 0, developed.stderr
    assert git(remote, "show", "gh-pages:index.html") == "next development docs"
    assert git(remote, "show", "gh-pages:release-status.json") == status


@pytest.mark.parametrize("field,value", [
    ("mode", "publish"), ("git_sha", "0" * 40), ("version", "v2.1.0-dev"),
])
def test_rejects_unpromoted_or_mismatched_release(pages, field, value):
    repo, remote, metadata = pages
    metadata[field] = value
    (repo / "phase5-build-result-release-metadata.json").write_text(json.dumps(metadata))
    result = publish(repo, "--promoted-release")
    assert result.returncode != 0
    assert "successful promotion metadata" in result.stderr
    assert not git(remote, "for-each-ref", "refs/heads/gh-pages")


def test_dry_run_never_publishes(pages):
    repo, remote, _ = pages
    result = publish(repo, "--promoted-release", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "release-status.json" in result.stdout
    assert not git(remote, "for-each-ref", "refs/heads/gh-pages")
