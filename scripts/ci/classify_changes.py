#!/usr/bin/env python3
"""Select CI work from a complete Git diff; uncertain inputs require all work."""

import argparse
from pathlib import Path, PurePosixPath
import subprocess


KEYS = ("APPLICATION", "WIKI", "PAGES", "DOCKERHUB", "METADATA")
TEXT_ROOTS = {"README.md", "AGENTS.md", "CLAUDE.md", "LICENSE", ".github/PULL_REQUEST_TEMPLATE.md"}
DOC_SUFFIXES = {".md", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
SITE_FILES = {"docs/index.html", "docs/.nojekyll", "docs/builder/app.js",
              "docs/builder/style.css", "docs/builder/runtime-options.json"}
HUB_FILES = {"docs/dockerhub/README.md", "docs/dockerhub/short-description.txt"}


def is_repository_metadata(path):
    p = PurePosixPath(path)
    # Only direct children of these data directories qualify. New workflows and
    # nested/executable files retain the full gate. The assignment workflow has
    # an exact trusted behavior contract in metadata-tools/assignment-workflow.json.
    return (p.parent == PurePosixPath(".github/ISSUE_TEMPLATE")
            and p.suffix in {".yml", ".yaml"}
            or p.parent == PurePosixPath(".github/rulesets") and p.suffix == ".json"
            or path == ".github/workflows/assign-pull-requests.yml")


def classify_paths(paths):
    result = dict.fromkeys(KEYS, False)
    for path in paths:
        p = PurePosixPath(path)
        is_doc = (path in TEXT_ROOTS or path in SITE_FILES or path in HUB_FILES
                  or (p.parts[0] in {"docs", "wiki"} and p.suffix.lower() in DOC_SUFFIXES))
        is_metadata = is_repository_metadata(path)
        result["METADATA"] |= is_metadata
        if not is_doc and not is_metadata:
            result["APPLICATION"] = True
        result["WIKI"] |= path.startswith("wiki/") or path == "scripts/ci/publish_wiki.sh"
        result["PAGES"] |= (path in SITE_FILES or path.startswith(("docs/builder/", "docs/recipes/"))
                            or path in {"scripts/ci/publish_pages.sh", "scripts/ci/prepare_pages.sh"}
                            or path.startswith(("frontend/src/recipes/", "frontend/recipe-helper/"))
                            or path in {"frontend/vite.recipes.config.ts", "frontend/package.json", "frontend/package-lock.json", "frontend/src/theme.ts"})
        result["DOCKERHUB"] |= path in HUB_FILES or path == "scripts/ci/publish_dockerhub_description.py"
        # Changes to selection/orchestration must exercise the full validation scope.
        if (path.startswith(("jenkins/", "scripts/ci/metadata-tools/"))
                or path in {"Jenkinsfile", "scripts/ci/classify_changes.py",
                            "scripts/ci/validate_repository_metadata.sh"}):
            result.update(dict.fromkeys(KEYS, True))
    return result


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL)


def classify(repo, base, head="HEAD", pull_request=False):
    try:
        if not base:
            raise ValueError("no successful baseline")
        base = git(repo, "rev-parse", "--verify", f"{base}^{{commit}}").decode().strip()
        head = git(repo, "rev-parse", "--verify", f"{head}^{{commit}}").decode().strip()
        if pull_request:
            base = git(repo, "merge-base", base, head).decode().strip()
        elif subprocess.call(["git", "-C", str(repo), "merge-base", "--is-ancestor", base, head],
                             stderr=subprocess.DEVNULL) != 0:
            raise ValueError("baseline no longer an ancestor")
        paths = git(repo, "diff", "--no-ext-diff", "--no-renames", "--name-only", "-z", base, head).decode().split("\0")
        paths = set(filter(None, paths))
        result = classify_paths(paths)
        # Symlinks, submodules and executable/mode changes never take the docs shortcut.
        for ref in (base, head):
            for entry in git(repo, "ls-tree", "-r", "-z", ref).split(b"\0"):
                if entry:
                    meta, path = entry.split(b"\t", 1)
                    if path.decode() in paths and not meta.startswith(b"100644 blob "):
                        result["APPLICATION"] = True
        return result
    except (subprocess.CalledProcessError, ValueError, UnicodeError, OSError):
        return dict.fromkeys(KEYS, True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--pull-request", action="store_true")
    args = parser.parse_args()
    for key, value in classify(args.repo, args.base, args.head, args.pull_request).items():
        print(f"CI_{key}={str(value).lower()}")


if __name__ == "__main__":
    main()
