"""WARP_EXCLUDE_HOSTS keeps chosen hosts out of the WARP tunnel."""
import os
from pathlib import Path
import subprocess

SCRIPT = Path(__file__).resolve().parents[2] / "warp-setup.sh"


def run_configure(tmp_path, **extra_env):
    calls = tmp_path / "calls"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cli = bin_dir / "warp-cli"
    cli.write_text(f"#!/bin/sh\necho \"$*\" >> {calls}\necho 'Status update: Connected'\n")
    cli.chmod(0o755)
    env = {
        **os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
        "LOG_DIR": str(tmp_path / "logs"), "ENABLE_WARP": "true", "WARP_ENABLE_NAT": "false",
        "WARP_REQUIRED_COMMANDS": "warp-cli", "WARP_READY_ATTEMPTS": "2",
        "WARP_READY_INTERVAL": "0.01", "WARP_LICENSE_KEY": "",
    }
    env.pop("WARP_EXCLUDE_HOSTS", None)
    env.update(extra_env)
    result = subprocess.run(["bash", str(SCRIPT), "configure"], env=env,
                            capture_output=True, text=True, timeout=10)
    return result, calls.read_text().splitlines()


def test_each_listed_host_is_excluded(tmp_path):
    result, calls = run_configure(
        tmp_path, WARP_EXCLUDE_HOSTS="edge.api.brightcove.com, api.example.org example.net")
    assert result.returncode == 0, result.stderr
    added = [c for c in calls if "tunnel host add" in c]
    assert added == [
        "--accept-tos tunnel host add edge.api.brightcove.com",
        "--accept-tos tunnel host add api.example.org",
        "--accept-tos tunnel host add example.net",
    ]


def test_nothing_is_excluded_when_unset(tmp_path):
    """Unset must not trip `set -u` either."""
    result, calls = run_configure(tmp_path)
    assert result.returncode == 0, result.stderr
    assert not any("tunnel host add" in c for c in calls)
