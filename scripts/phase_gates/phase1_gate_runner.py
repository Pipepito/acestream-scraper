#!/usr/bin/env python3
"""
Phase 1 migration safety gate runner.

Runs quick/full parity profiles, separates blocking and non-blocking failures,
and exits non-zero only when blocking checks fail.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_CONFIG = Path("scripts/phase_gates/phase1_gate_config.yaml")


def load_config(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_blocking(command: Dict[str, Any], class_policy: Dict[str, Any]) -> bool:
    if "gate_critical" in command:
        return bool(command["gate_critical"])
    source_class = command.get("source_class", "legacy")
    class_data = class_policy.get(source_class, {})
    return bool(class_data.get("blocking_default", False))


def run_command(command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        shell=True,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def print_human_report(summary: Dict[str, Any]) -> None:
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f" GATE ► PROFILE {summary['profile'].upper()}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Config version: {summary['config_version']}")
    print(f"Dry run: {summary['dry_run']}")
    print()

    for result in summary["results"]:
        blocking_label = "BLOCKING" if result["blocking"] else "NON-BLOCKING"
        status_label = result["status"].upper()
        print(f"[{status_label}] {result['id']} ({blocking_label})")
        print(f"  class: {result['source_class']}")
        print(f"  command: {result['command']}")
        if result["exit_code"] is not None:
            print(f"  exit: {result['exit_code']}")
        if result["status"] == "failed" and result["stderr_tail"]:
            print(f"  stderr: {result['stderr_tail']}")
        print()

    print("Summary:")
    print(f"  passed: {summary['passed']}")
    print(f"  blocking_failures: {summary['blocking_failures']}")
    print(f"  non_blocking_failures: {summary['non_blocking_failures']}")


def build_summary(
    profile: str,
    config_version: str,
    dry_run: bool,
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    blocking_failures = [item["id"] for item in results if item["blocking"] and item["status"] == "failed"]
    non_blocking_failures = [item["id"] for item in results if not item["blocking"] and item["status"] == "failed"]
    return {
        "profile": profile,
        "config_version": config_version,
        "dry_run": dry_run,
        "passed": len(blocking_failures) == 0,
        "blocking_failures": blocking_failures,
        "non_blocking_failures": non_blocking_failures,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Phase 1 migration safety gates.")
    parser.add_argument("--profile", default="quick", help="Gate profile to run (quick|full).")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to gate config file.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands without executing.")
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

    class_policy = config.get("class_policy", {})
    profile = profiles[args.profile]
    commands = profile.get("commands", [])
    results: List[Dict[str, Any]] = []

    for command in commands:
        blocking = is_blocking(command, class_policy)
        result = {
            "id": command["id"],
            "description": command.get("description", ""),
            "command": command["command"],
            "source_class": command.get("source_class", "unknown"),
            "blocking": blocking,
            "status": "planned" if args.dry_run else "passed",
            "exit_code": None,
            "stderr_tail": "",
        }

        if not args.dry_run:
            completed = run_command(command["command"], repo_root)
            result["exit_code"] = completed.returncode
            result["status"] = "passed" if completed.returncode == 0 else "failed"
            if completed.returncode != 0:
                stderr_lines = completed.stderr.strip().splitlines()
                result["stderr_tail"] = stderr_lines[-1] if stderr_lines else ""

        results.append(result)

    summary = build_summary(
        profile=args.profile,
        config_version=config.get("version", "unknown"),
        dry_run=args.dry_run,
        results=results,
    )

    if args.json_output:
        print(json.dumps(summary, indent=2))
    else:
        print_human_report(summary)

    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
