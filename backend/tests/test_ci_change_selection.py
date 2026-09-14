"""Real Git histories exercise CI skipping without any application services."""

import importlib.util
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("change_selection", ROOT / "scripts/ci/classify_changes.py")
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL).decode().strip()


def commit(repo, path, content="text"):
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "test change")
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "ci@example.invalid")
    git(tmp_path, "config", "user.name", "CI test")
    commit(tmp_path, "README.md")
    return tmp_path


@pytest.mark.parametrize("path, expected", [
    ("README.md", set()),
    ("docs/ops/jenkins-ci.md", set()),
    ("wiki/Home.md", {"WIKI"}),
    ("wiki/phone screenshot.png", {"WIKI"}),
    ("docs/builder/app.js", {"PAGES"}),
    ("docs/builder/runtime-options.json", {"PAGES"}),
    ("docs/builder/example.png", {"PAGES"}),
    ("docs/builder/new-script.js", {"APPLICATION", "PAGES"}),
    ("docs/.nojekyll", {"PAGES"}),
    ("docs/dockerhub/README.md", {"DOCKERHUB"}),
    ("docs/dockerhub/short-description.txt", {"DOCKERHUB"}),
    ("backend/app/main.py", {"APPLICATION"}),
    ("backend/requirements.txt", {"APPLICATION"}),
    ("frontend/package-lock.json", {"APPLICATION"}),
    ("Dockerfile", {"APPLICATION"}),
    (".dockerignore", {"APPLICATION"}),
    ("version.txt", {"APPLICATION"}),
    ("unexpected.txt", {"APPLICATION"}),
    ("docs/new-executable.py", {"APPLICATION"}),
    ("scripts/ci/publish_pages.sh", {"APPLICATION", "PAGES"}),
    ("jenkins/develop.Jenkinsfile", set(selection.KEYS)),
    ("scripts/ci/classify_changes.py", set(selection.KEYS)),
])
def test_scope_by_path(repo, path, expected):
    base = git(repo, "rev-parse", "HEAD")
    commit(repo, path, "changed")
    result = selection.classify(repo, base)
    assert {key for key, value in result.items() if value} == expected


def test_docs_after_failed_application_build_still_validate_application(repo):
    successful = git(repo, "rev-parse", "HEAD")
    commit(repo, "backend/app/main.py", "application changed but build failed")
    commit(repo, "README.md", "docs follow-up")
    assert selection.classify(repo, successful)["APPLICATION"]


def test_pr_compares_entire_branch_from_merge_base(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-qb", "feature")
    commit(repo, "backend/app/main.py")
    head = commit(repo, "README.md", "docs follow-up")
    git(repo, "checkout", "--detach", base)
    target = commit(repo, "docs/new-guide.md")
    assert selection.classify(repo, target, head, pull_request=True)["APPLICATION"]
    assert all(selection.classify(repo, target, head).values())  # rewritten develop history


def test_target_changes_are_not_counted_as_pr_changes(repo):
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "checkout", "-qb", "feature")
    head = commit(repo, "wiki/Home.md")
    git(repo, "checkout", "--detach", base)
    target = commit(repo, "backend/app/main.py")
    assert not selection.classify(repo, target, head, pull_request=True)["APPLICATION"]


@pytest.mark.parametrize("base", ["", "missing-ref", "0" * 40])
def test_missing_baseline_requires_all_work(repo, base):
    assert all(selection.classify(repo, base).values())


def test_rename_of_application_file_into_docs_is_not_hidden(repo):
    base = commit(repo, "backend/app/main.py")
    (repo / "wiki").mkdir()
    git(repo, "mv", "backend/app/main.py", "wiki/example.md")
    git(repo, "commit", "-qm", "rename")
    assert selection.classify(repo, base)["APPLICATION"]


def test_deleted_wiki_page_still_needs_publication(repo):
    base = commit(repo, "wiki/Removed.md")
    git(repo, "rm", "wiki/Removed.md")
    git(repo, "commit", "-qm", "delete")
    assert selection.classify(repo, base) == dict(APPLICATION=False, WIKI=True, PAGES=False, DOCKERHUB=False)


@pytest.mark.parametrize("kind", ["symlink", "executable"])
def test_non_regular_docs_never_run_on_host(repo, kind):
    base = git(repo, "rev-parse", "HEAD")
    target = repo / "README.md"
    if kind == "symlink":
        target.unlink()
        target.symlink_to("/etc/passwd")
    else:
        target.chmod(0o755)
        git(repo, "config", "core.filemode", "true")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "mode change")
    assert selection.classify(repo, base)["APPLICATION"]


def test_unchanged_successful_revision_has_no_publication(repo):
    assert not any(selection.classify(repo, "HEAD").values())
