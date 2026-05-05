#!/usr/bin/env python3
"""Phase 5 multi-arch gate runner with quick/full profiles and JSON reporting."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_CONFIG = Path("scripts/phase_gates/phase5_gate_config.yaml")


def load_config(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        shell=True,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def build_summary(profile: str, config_version: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    blocking_failures = [item["id"] for item in results if item["blocking"] and item["status"] == "failed"]
    non_blocking_failures = [item["id"] for item in results if not item["blocking"] and item["status"] == "failed"]
    return {
        "profile": profile,
        "config_version": config_version,
        "passed": len(blocking_failures) == 0,
        "blocking_failures": blocking_failures,
        "non_blocking_failures": non_blocking_failures,
        "results": results,
    }


def print_human_report(summary: Dict[str, Any]) -> None:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f" PHASE5 MULTI-ARCH GATES ► PROFILE {summary['profile'].upper()}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Config version: {summary['config_version']}")
    print()

    for result in summary["results"]:
        blocking_label = "BLOCKING" if result["blocking"] else "NON-BLOCKING"
        status_label = result["status"].upper()
        print(f"[{status_label}] {result['id']} ({blocking_label})")
        print(f"  command: {result['command']}")
        print(f"  duration_ms: {result['duration_ms']}")
        print(f"  exit: {result['exit_code']}")
        if result["status"] == "failed":
            if result["stderr_tail"]:
                print(f"  stderr: {result['stderr_tail']}")
            elif result["stdout_tail"]:
                print(f"  stdout: {result['stdout_tail']}")
        print()

    print("Summary:")
    print(f"  passed: {summary['passed']}")
    print(f"  blocking_failures: {summary['blocking_failures']}")
    print(f"  non_blocking_failures: {summary['non_blocking_failures']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 5 multi-arch gates.")
    parser.add_argument("--profile", default="quick", help="Gate profile to run (quick|full).")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to gate config file.")
    parser.add_argument("--json-output", action="store_true", help="Print machine-readable JSON summary.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = repo_root / config_path

    config = load_config(config_path)
    profiles = config.get("profiles", {})
    if args.profile not in profiles:
        print(f"Unknown profile '{args.profile}'. Available: {', '.join(sorted(profiles.keys()))}", file=sys.stderr)
        return 2

    profile = profiles[args.profile]
    commands = profile.get("commands", [])
    results: List[Dict[str, Any]] = []

    for command in commands:
        rendered_command = command["command"]
        started = time.time()
        completed = run_command(rendered_command, repo_root)
        duration_ms = int((time.time() - started) * 1000)

        stdout_lines = completed.stdout.strip().splitlines()
        stderr_lines = completed.stderr.strip().splitlines()

        results.append(
            {
                "id": command["id"],
                "description": command.get("description", ""),
                "command": rendered_command,
                "blocking": bool(command.get("blocking", True)),
                "status": "passed" if completed.returncode == 0 else "failed",
                "exit_code": completed.returncode,
                "duration_ms": duration_ms,
                "stdout_tail": stdout_lines[-1] if stdout_lines else "",
                "stderr_tail": stderr_lines[-1] if stderr_lines else "",
            }
        )

    summary = build_summary(args.profile, config.get("version", "unknown"), results)

    if args.json_output:
        print(json.dumps(summary, indent=2))
    else:
        print_human_report(summary)

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

