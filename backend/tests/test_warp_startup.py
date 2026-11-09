"""Auto-connect must wait for the tunnel, not merely a responsive daemon."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "warp-setup.sh"


def run_setup(tmp_path, states, auto_connect=True, force_ipv4="true", dns_only=False):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    (tmp_path / "states.json").write_text(json.dumps(states))
    cli = bin_dir / "warp-cli"
    cli.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\nfrom pathlib import Path\n"
        "root = Path(os.environ['WARP_TEST_DIR'])\n"
        "(root / 'force_ipv4').write_text(os.environ.get('WARP_FORCE_IPV4', ''))\n"
        "with (root / 'calls').open('a') as f: f.write(' '.join(sys.argv[1:]) + '\\n')\n"
        "if '--json' in sys.argv:\n"
        "    counter = root / 'polls'\n"
        "    n = int(counter.read_text()) if counter.exists() else 0\n"
        "    states = json.loads((root / 'states.json').read_text())\n"
        "    state = states[min(n, len(states)-1)]\n"
        "    counter.write_text(str(n+1))\n"
        "    print('not JSON' if state == 'malformed' else json.dumps({'status':state}))\n"
        "elif 'status' in sys.argv: print('Status update: Disconnected')\n"
    )
    cli.chmod(0o755)
    for name, script in {
        "sudo": '#!/bin/sh\nexec "$@"\n',
        "nft": f'#!{sys.executable}\n'
        'import os, sys, json\nfrom pathlib import Path\n'
        'root = Path(os.environ["WARP_TEST_DIR"])\n'
        'with (root / "calls").open("a") as f: f.write("nft\\n")\n'
        'rule = {"rule": {"expr": [{"match": {"op": "==", "left": {"meta": {"key": "oifname"}}, "right": "CloudflareWARP"}}, {"masquerade": None}]}}\n'
        'if "-j" in sys.argv: print(json.dumps({"nftables": [rule] if (root / "nat-rule").exists() else []}))\n'
        'if "rule" in sys.argv:\n'
        '    with (root / "nat-rule").open("a") as f: f.write("added\\n")\n',
    }.items():
        path = bin_dir / name
        path.write_text(script)
        path.chmod(0o755)
    env = {
        **os.environ, "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
        "WARP_TEST_DIR": str(tmp_path), "DATABASE_URL": f"sqlite:///{tmp_path}/test.db", "WARP_EXCLUDE_HOSTS": "", "LOG_DIR": str(tmp_path / "logs"),
        "ENABLE_WARP": "true", "WARP_ENABLE_NAT": str(auto_connect).lower(),
        "WARP_REQUIRED_COMMANDS": "warp-cli", "WARP_READY_ATTEMPTS": "4",
        "WARP_READY_INTERVAL": "0.01", "WARP_LICENSE_KEY": "",
        "WARP_FORCE_IPV4": force_ipv4,
        "WARP_DNS_ONLY": str(dns_only).lower(),
    }
    result = subprocess.run(
        ["bash", str(SCRIPT), "configure"], env=env,
        capture_output=True, text=True, timeout=10,
    )
    return result, (tmp_path / "calls").read_text().splitlines()


def test_waits_through_connecting_before_configuring_nat(tmp_path):
    result, calls = run_setup(tmp_path, ["Disconnected", "Connecting", "Connected"])
    assert result.returncode == 0, result.stderr
    assert calls.count("--accept-tos --json status") == 4
    assert calls.index("nft") > [i for i, call in enumerate(calls) if "--json" in call][2]


@pytest.mark.parametrize("state", ["Disconnected", "Connecting", "malformed"])
def test_unconnected_or_invalid_status_blocks_startup(tmp_path, state):
    result, calls = run_setup(tmp_path, [state])
    assert result.returncode != 0
    assert "WARP NAT connect did not become ready" in result.stderr
    assert calls.count("--accept-tos --json status") == 4
    assert "nft" not in calls


def test_manual_connect_mode_only_requires_daemon(tmp_path):
    result, calls = run_setup(tmp_path, ["Disconnected"], auto_connect=False)
    assert result.returncode == 0, result.stderr
    assert not any("--json" in call or call == "nft" for call in calls)
    assert "--accept-tos connect" not in calls


def test_setup_preserves_disabled_ipv4_preference(tmp_path):
    result, _ = run_setup(tmp_path, ["Disconnected"], auto_connect=False, force_ipv4="false")
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "force_ipv4").read_text() == "false"


def test_dns_only_connects_without_enabling_tunnel_or_nat(tmp_path):
    result, calls = run_setup(tmp_path, ["Connecting", "Connected"], dns_only=True)
    assert result.returncode == 0, result.stderr
    assert "--accept-tos mode doh" in calls
    assert "--accept-tos connect" in calls
    assert calls.count("--accept-tos --json status") == 3
    assert "--accept-tos mode warp+doh" not in calls
    assert "nft" not in calls


def test_dns_only_manual_mode_is_set_without_connecting(tmp_path):
    result, calls = run_setup(tmp_path, ["Disconnected"], auto_connect=False, dns_only=True)
    assert result.returncode == 0, result.stderr
    assert "--accept-tos mode doh" in calls
    assert "--accept-tos connect" not in calls
    assert "nft" not in calls


def test_repeated_configuration_does_not_duplicate_nat_rule(tmp_path):
    for _ in range(2):
        result, _ = run_setup(tmp_path, ["Connected"])
        assert result.returncode == 0, result.stderr
    assert (tmp_path / 'nat-rule').read_text() == 'added\n'
