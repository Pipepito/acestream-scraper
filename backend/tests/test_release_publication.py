"""Exercise release publication with a fake Docker CLI; never contact a registry."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
VERSION_TAGS = ['v2.0.0'] + ['v2.0.0-' + f for f in (
    'scraper', 'scraper-acestream', 'scraper-acexy', 'scraper-acestream-acexy')]


@pytest.fixture
def release(tmp_path):
    ci = tmp_path / 'scripts/ci'
    ci.mkdir(parents=True)
    for name in ('run_jenkins_release.sh', 'assert_release_tags_available.py',
                 'flavor_platforms.py', 'promote_latest.sh'):
        shutil.copy(ROOT / 'scripts/ci' / name, ci)
    shutil.copytree(ROOT / 'docker/manifests', tmp_path / 'docker/manifests')
    (tmp_path / 'version.txt').write_text('v2.0.0\n')
    for name in ('run_cutover_required_checks.sh', 'verify_multiarch_manifest.sh',
                 'cleanup_runner_docker.sh'):
        (ci / name).write_text('echo ' + name + ' >> "$CALL_LOG"\n')
    (ci / 'build_multiarch_images.sh').write_text('''
while [[ $# -gt 0 ]]; do
  if [[ "$1" == --digest-file ]]; then echo repo@sha256:fixture > "$2"; shift; fi
  shift
done
''')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    docker = bin_dir / 'docker'
    docker.write_text(f'#!{sys.executable}\n' + '''
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ['CALL_LOG'], 'a') as f: f.write(json.dumps(args) + '\\n')
if args[:3] == ['buildx', 'imagetools', 'inspect']:
    tag = args[3]
    countfile = Path(os.environ['CALL_LOG'] + '.count')
    count = int(countfile.read_text()) + 1 if countfile.exists() else 1
    countfile.write_text(str(count))
    mode = os.environ.get('REGISTRY_MODE', 'absent')
    if mode == 'error':
        print('ERROR: failed to authorize: 401 Unauthorized', file=sys.stderr)
        sys.exit(1)
    if mode == 'existing' or (mode == 'partial' and tag.endswith('-scraper-acexy')) or (mode == 'late' and count > 10):
        sys.exit(0)
    print('ERROR: docker.io/' + tag + ': not found', file=sys.stderr)
    sys.exit(1)
''')
    docker.chmod(0o755)
    pytest_bin = tmp_path / 'backend/venv/bin/pytest'
    pytest_bin.parent.mkdir(parents=True)
    pytest_bin.write_text('#!/bin/sh\nexit 0\n')
    pytest_bin.chmod(0o755)
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', '-C', str(tmp_path), '-c', 'user.name=Test', '-c',
                    'user.email=test@example.invalid', 'commit', '--allow-empty', '-qm', 'fixture'], check=True)
    env = {**os.environ, 'PATH': str(bin_dir) + os.pathsep + os.environ['PATH'],
           'CALL_LOG': str(tmp_path / 'calls'), 'DOCKERHUB_USERNAME': 'fixture',
           'DOCKERHUB_TOKEN': 'fixture', 'PUBLISH_LATEST': '0',
           'FORCE_VERSION_OVERWRITE': '0', 'REGISTRY_MODE': 'absent'}
    for key in ('RELEASE_IMAGE_REPO', 'RELEASE_LOGIN_SERVER'):
        env.pop(key, None)
    return tmp_path, env


def run(release, *args, **overrides):
    root, env = release
    result = subprocess.run(['bash', 'scripts/ci/run_jenkins_release.sh', *args],
                            cwd=root, env={**env, **overrides}, capture_output=True,
                            text=True, timeout=30)
    log = root / 'calls'
    return result, log.read_text() if log.exists() else ''


@pytest.mark.parametrize('mode', ['existing', 'partial', 'error'])
def test_collision_or_registry_failure_blocks_before_tests_and_push(release, mode):
    result, calls = run(release, REGISTRY_MODE=mode)
    assert result.returncode != 0
    assert 'run_cutover' not in calls
    assert 'login' not in calls
    assert 'create' not in calls


def test_fresh_version_dry_run_checks_all_tags_without_publishing(release):
    result, calls = run(release, '--dry-run')
    assert result.returncode == 0, result.stderr
    for tag in VERSION_TAGS:
        assert 'pipepito/acestream-scraper:' + tag in calls
    assert 'login' not in calls
    assert 'create' not in calls


def test_force_allows_existing_version_and_keeps_latest_untouched(release):
    result, calls = run(release, REGISTRY_MODE='existing', FORCE_VERSION_OVERWRITE='1')
    assert result.returncode == 0, result.stderr
    assert 'FORCE_VERSION_OVERWRITE enabled' in result.stdout
    assert 'create' in calls
    assert ':latest' not in calls


def test_force_does_not_hide_auth_failure(release):
    result, calls = run(release, REGISTRY_MODE='error', FORCE_VERSION_OVERWRITE='1')
    assert result.returncode != 0
    assert 'create' not in calls


def test_collision_appearing_during_build_blocks_all_tag_assignment(release):
    result, calls = run(release, REGISTRY_MODE='late')
    assert result.returncode != 0
    assert 'login' in calls
    assert 'create' not in calls


def test_promotion_reuses_existing_version_and_records_real_references(release):
    result, calls = run(release, REGISTRY_MODE='existing', PUBLISH_LATEST='1')
    assert result.returncode == 0, result.stderr
    assert 'run_cutover' not in calls
    metadata = json.loads((release[0] / 'phase5-build-result-release-metadata.json').read_text())
    assert metadata['source'] == 'pipepito/acestream-scraper:v2.0.0'
    assert metadata['tags'] == ['pipepito/acestream-scraper:latest']


def test_promotion_dry_run_does_not_inspect_or_publish(release):
    result, calls = run(release, '--dry-run', PUBLISH_LATEST='1')
    assert result.returncode == 0, result.stderr
    assert 'Dry-run promotion plan completed' in result.stdout
    assert 'imagetools' not in calls
    assert 'login' not in calls


def test_channel_dry_run_ignores_release_collisions(release):
    result, calls = run(release, '--dry-run', '--channel', 'develop', REGISTRY_MODE='existing')
    assert result.returncode == 0, result.stderr
    assert 'imagetools' not in calls
