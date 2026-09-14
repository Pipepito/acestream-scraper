#!/usr/bin/env python3
"""Read-only checks for user guides and Docker Hub text; never execute page content."""

import argparse
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def validate(root):
    errors = []
    required = ("README.md", "wiki/Home.md", "wiki/_Sidebar.md", "wiki/Installation.md",
                "wiki/Docker.md", "wiki/Configuration.md", "wiki/Development.md",
                "docs/dockerhub/README.md", "docs/dockerhub/short-description.txt")
    for name in required:
        if not (root / name).is_file():
            errors.append(f"Missing {name}")
    seen = set()
    for path in sorted((root / "wiki").rglob("*")):
        if path.is_file():
            if path.name in seen:
                errors.append(f"Duplicate wiki filename: {path.name}")
            seen.add(path.name)
    pages = [root / "README.md", *sorted((root / "wiki").rglob("*.md")),
             root / "docs/dockerhub/README.md"]
    for path in pages:
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        # Ignore examples in fenced code; check files, not generated heading slugs.
        content = re.sub(r"```.*?```", "", content, flags=re.S)
        for target in re.findall(r"\]\(([^\s)]+)\)", content):
            link = urlsplit(target)
            if link.scheme or link.netloc or not link.path:
                continue
            dest = (path.parent / unquote(link.path)).resolve()
            if not dest.is_relative_to(root) or not dest.exists():
                errors.append(f"{path.relative_to(root)}: missing local link {target}")
            if path.parent == root / "docs/dockerhub":
                errors.append(f"Docker Hub requires absolute links: {target}")
    for name, limit in (("short-description.txt", 100), ("README.md", 25000)):
        path = root / "docs/dockerhub" / name
        if path.is_file():
            value = path.read_text(encoding="utf-8")
            if name == "short-description.txt":
                value = value.strip()
            if not value.strip() or len(value) > limit:
                errors.append(f"Docker Hub {name} must contain 1–{limit} characters")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    for error in errors:
        print(f"FAIL: {error}")
    if not errors:
        print("PASS: user-guide links, wiki filenames, and Docker Hub description")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
