"""Failed gates must remain diagnosable without a Jenkins workspace or rerun."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("phase", [1, 3])
def test_gate_retains_failure_output(tmp_path, phase):
    config = tmp_path / 'gates.json'
    config.write_text(json.dumps({'version': 'test', 'profiles': {'quick': {'commands': [
        {'id': 'broken', 'command': "printf 'actual failure\\n'; printf 'warning\\n' >&2; exit 7", 'blocking': True, 'gate_critical': True},
    ]}}}))
    logs = tmp_path / 'logs'
    result = subprocess.run([sys.executable, str(ROOT / f'scripts/phase_gates/phase{phase}_gate_runner.py'),
        '--config', str(config), '--json-output', *(['--log-dir', str(logs)] if phase == 3 else [])], capture_output=True, text=True, timeout=10)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report['blocking_failures'] == ['broken']
    assert report['results'][0]['stdout_tail'] == 'actual failure'
    assert report['results'][0]['stderr_tail'] == 'warning'
    if phase == 1:
        human = subprocess.run([sys.executable, str(ROOT / 'scripts/phase_gates/phase1_gate_runner.py'),
            '--config', str(config)], capture_output=True, text=True, timeout=10)
        assert 'actual failure' in human.stdout
        assert 'warning' in human.stdout
        return
    assert '[phase3] Running broken' in result.stderr
    assert '[phase3] broken: exit 7' in result.stderr
    assert 'actual failure' in (logs / 'broken.log').read_text()
    assert 'warning' in (logs / 'broken.log').read_text()
