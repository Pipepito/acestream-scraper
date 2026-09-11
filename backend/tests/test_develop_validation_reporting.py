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


@pytest.mark.parametrize('writes_report', [True, False])
def test_failed_container_preserves_current_artifacts_without_archiving_stale_success(tmp_path, writes_report):
    pipeline = (ROOT / 'jenkins/develop.Jenkinsfile').read_text()
    stage = pipeline.split("stage('Full application validation')", 1)[1]
    shell = stage.split("sh '''", 1)[1].split("'''", 1)[0]
    (tmp_path / 'phase3-gate-report-full.json').write_text('{"passed":true,"stale":true}')
    (tmp_path / 'phase3-phase1-full.json').write_text('{"stale":true}')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    docker = bin_dir / 'docker'
    docker.write_text('#!/bin/sh\n' + (
        'printf \'{"passed":false,"current":true}\\n\' > "$WORKSPACE/.ci-develop-artifacts/phase3-gate-report-full.json"\n'
        if writes_report else '') + 'exit 7\n')
    docker.chmod(0o755)
    result = subprocess.run(['bash', '-c', shell], cwd=tmp_path, env={**os.environ,
        'WORKSPACE': str(tmp_path), 'PR_RUNNER_IMAGE': 'unused', 'PATH': f'{bin_dir}:{os.environ["PATH"]}'},
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 7
    assert 'Application validation failed (exit 7)' in result.stdout
    assert not (tmp_path / 'phase3-phase1-full.json').exists()
    current = tmp_path / 'phase3-gate-report-full.json'
    if writes_report:
        assert json.loads(current.read_text()) == {'passed': False, 'current': True}
    else:
        assert not current.exists()
    assert "artifacts: '.ci-develop-artifacts/**," in stage
