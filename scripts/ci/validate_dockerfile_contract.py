#!/usr/bin/env python3
"""Static guard for the multi-flavor Docker runtime contract.

Fork PRs may not execute a contributor-controlled Dockerfile on the Jenkins
daemon. This parser catches target, entrypoint, command, and healthcheck drift
without resolving images or running Dockerfile instructions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "Dockerfile"
PLATFORMS = ROOT / "docker/manifests/platforms.json"


def logical_instructions(text: str) -> list[str]:
    instructions: list[str] = []
    current = ""
    for raw in text.splitlines():
        stripped = raw.strip()
        if not current and (not stripped or stripped.startswith("#")):
            continue
        current = f"{current} {stripped}".strip()
        if current.endswith("\\"):
            current = current[:-1].rstrip()
            continue
        instructions.append(re.sub(r"\s+", " ", current))
        current = ""
    if current:
        instructions.append(re.sub(r"\s+", " ", current))
    return instructions


def runtime_command_errors(runtime: list[str]) -> list[str]:
    """Validate the required Uvicorn command while allowing extra safe flags."""
    commands = [instruction for instruction in runtime if instruction.startswith("CMD ")]
    if len(commands) != 1:
        return [f"runtime-base must define exactly one CMD instruction; found {len(commands)}"]

    command = commands[0]
    try:
        argv = json.loads(command.removeprefix("CMD "))
    except json.JSONDecodeError:
        return ["runtime-base CMD must use valid JSON array syntax"]

    if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
        return ["runtime-base CMD must be a JSON array of strings"]
    if argv[:2] != ["uvicorn", "main:app"]:
        return ["runtime-base CMD must launch uvicorn main:app"]

    errors: list[str] = []
    for option, expected in (("--host", "0.0.0.0"), ("--port", "8000")):
        positions = [index for index, arg in enumerate(argv) if arg == option]
        if len(positions) != 1:
            errors.append(f"runtime-base CMD must define {option} exactly once")
            continue
        position = positions[0]
        actual = argv[position + 1] if position + 1 < len(argv) else None
        if actual != expected:
            errors.append(f"runtime-base CMD must set {option} to {expected}")
    return errors


def main() -> int:
    instructions = logical_instructions(DOCKERFILE.read_text(encoding="utf-8"))
    stages: dict[str, list[str]] = {}
    current_stage: str | None = None
    parent_by_stage: dict[str, str] = {}

    for instruction in instructions:
        match = re.match(r"FROM(?: --platform=\S+)? (\S+) AS ([A-Za-z0-9_.-]+)$", instruction, re.I)
        if match:
            parent, current_stage = match.groups()
            current_stage = current_stage.lower()
            stages[current_stage] = []
            parent_by_stage[current_stage] = parent.lower()
        elif current_stage:
            stages[current_stage].append(instruction)

    expected_parents = {
        "scraper": "runtime-base",
        "scraper-acestream": "scraper",
        "scraper-acexy": "scraper",
        "scraper-acestream-acexy": "scraper-acestream",
    }
    errors = [
        f"{stage} must inherit from {parent}"
        for stage, parent in expected_parents.items()
        if parent_by_stage.get(stage) != parent
    ]

    runtime = stages.get("runtime-base", [])
    required_runtime = {
        "COPY entrypoint.sh /usr/local/bin/entrypoint.sh",
        "COPY warp-setup.sh /usr/local/bin/warp-setup.sh",
        "COPY healthcheck.sh /usr/local/bin/healthcheck.sh",
        'ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]',
        'HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD ["/usr/local/bin/healthcheck.sh"]',
    }
    for required in sorted(required_runtime):
        if required not in runtime:
            errors.append(f"runtime-base is missing exact contract instruction: {required}")
    errors.extend(runtime_command_errors(runtime))

    platform_data = json.loads(PLATFORMS.read_text(encoding="utf-8"))
    expected_platforms = {"linux/amd64", "linux/arm64", "linux/arm/v7"}
    actual_platforms = set(platform_data.get("baseline_platforms", []))
    if actual_platforms != expected_platforms:
        errors.append(
            "baseline platform matrix must be linux/amd64, linux/arm64, linux/arm/v7; "
            f"got {sorted(actual_platforms)}"
        )

    if errors:
        for error in errors:
            print(f"Docker contract error: {error}")
        return 1

    print("Dockerfile targets, entrypoint, command, healthcheck, and platform matrix are consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
