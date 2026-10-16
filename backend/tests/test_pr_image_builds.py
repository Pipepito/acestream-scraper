"""Execute PR image orchestration with a stateful fake Docker daemon."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def runner(tmp_path):
    ci = tmp_path / 'scripts/ci'
    ci.mkdir(parents=True)
    for name in ('validate_pr_images.sh', 'flavor_platforms.py'):
        shutil.copy(ROOT / 'scripts/ci' / name, ci)
    shutil.copytree(ROOT / 'docker/manifests', tmp_path / 'docker/manifests')
    (ci / 'cleanup_runner_docker.sh').write_text('test "$DOCKER_CONFIG" = "$EXPECTED_ORIGINAL_CONFIG"\n')
    (ci / 'build_multiarch_images.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
python3 - "$@" <<'PYTHON'
import json, os, sys
from pathlib import Path
args=sys.argv[1:]
if '--dry-run' in args:
    raise SystemExit(0)
assert '--load' in args and '--push' not in args and '--push-by-digest' not in args
assert args[args.index('--builder')+1] == os.environ.get('JENKINS_BUILDER', 'acestream-builder')
assert os.environ['BUILDX_CONFIG'] == os.environ['EXPECTED_BUILDX_CONFIG']
assert json.loads((Path(os.environ['DOCKER_CONFIG']) / 'config.json').read_text()) == {'auths': {}}
tag=args[args.index('--tag')+1]
state=Path(os.environ['IMAGE_STATE'])
images=json.loads(state.read_text())
images.append(tag)
state.write_text(json.dumps(images))
with open(os.environ['EVENT_LOG'],'a') as f: f.write(json.dumps(['build', *args])+'\\n')
if os.environ.get('FAIL_BUILD') == '1':
    raise SystemExit(23)
PYTHON
''')
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    docker = bin_dir / 'docker'
    docker.write_text(f'#!{sys.executable}\n'+'''
import json, os, sys
from pathlib import Path
args=sys.argv[1:]
state=Path(os.environ['IMAGE_STATE'])
images=json.loads(state.read_text())
with open(os.environ['EVENT_LOG'],'a') as f: f.write(json.dumps(args)+'\\n')
if args[:2] == ['image','ls']:
    tag=args[-1].split('=',1)[1]
    if tag in images: print('sha256:fixture')
elif args[:2] == ['image','inspect']:
    assert args[2] in images
    print('sha256:fixture linux/amd64')
elif args[:2] == ['image','rm']:
    assert '-f' not in args
    if os.environ.get('FAIL_REMOVE') == '1':
        print('fixture removal failure',file=sys.stderr)
        sys.exit(19)
    images.remove(args[2])
    state.write_text(json.dumps(images))
else:
    raise AssertionError(args)
''')
    docker.chmod(0o755)
    (tmp_path / 'images.json').write_text('[]')
    original = tmp_path / 'original-config'
    original.mkdir()
    (original / 'config.json').write_text('{"auths":{"private.example":{}}}')
    env = {**os.environ, 'PATH': str(bin_dir)+os.pathsep+os.environ['PATH'],
           'IMAGE_STATE': str(tmp_path / 'images.json'), 'EVENT_LOG': str(tmp_path / 'events'),
           'DOCKER_CONFIG': str(original), 'EXPECTED_ORIGINAL_CONFIG': str(original),
           'BUILDX_CONFIG': str(original / 'buildx'), 'EXPECTED_BUILDX_CONFIG': str(original / 'buildx')}
    return tmp_path, env


def run(runner, *args, **overrides):
    root, env = runner
    result = subprocess.run(['bash', 'scripts/ci/validate_pr_images.sh', '--name', 'PR-123-7', *args],
                            cwd=root, env={**env, **overrides}, capture_output=True, text=True, timeout=20)
    log = root / 'events'
    events = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    return result, events, json.loads((root / 'images.json').read_text())


def test_builds_complete_manifest_matrix_and_removes_each_image(runner):
    result, events, images = run(runner)
    assert result.returncode == 0, result.stderr
    builds = [e for e in events if e[0] == 'build']
    assert len(builds) == 12
    pairs = {(e[e.index('--flavor')+1], e[e.index('--platforms')+1]) for e in builds}
    assert len(pairs) == 12
    assert {p for _, p in pairs} == {'linux/amd64', 'linux/arm64', 'linux/arm/v7'}
    assert images == []
    for index, event in enumerate(events):
        if event[0] != 'build':
            continue
        next_build = next((n for n in range(index+1, len(events)) if events[n][0] == 'build'), len(events))
        tag = event[event.index('--tag')+1]
        assert ['image', 'rm', tag] in events[index+1:next_build]


def test_failed_build_removes_partially_exported_image_and_preserves_failure(runner):
    result, events, images = run(runner, FAIL_BUILD='1')
    assert result.returncode == 23
    assert sum(e[0] == 'build' for e in events) == 1
    assert images == []


def test_failed_removal_is_visible_and_fails_the_job(runner):
    result, _, images = run(runner, FAIL_REMOVE='1')
    assert result.returncode != 0
    assert 'fixture removal failure' in result.stderr
    assert len(images) == 1


def test_dry_run_does_not_touch_docker(runner):
    result, events, images = run(runner, '--dry-run')
    assert result.returncode == 0, result.stderr
    assert not events and not images
    assert result.stdout.count('[DRY RUN] docker image rm ') == 12


def test_preexisting_tag_is_not_overwritten_or_deleted(runner):
    original = 'acestream-scraper-pr-build:pr-123-7-linux-amd64-scraper'
    (runner[0] / 'images.json').write_text(json.dumps([original]))
    result, events, images = run(runner)
    assert result.returncode != 0
    assert 'Refusing to overwrite' in result.stderr
    assert images == [original]
    assert not any(e[0] == 'build' or e[:2] == ['image','rm'] for e in events)


def test_custom_publication_builder_and_buildx_config_are_reused(runner):
    custom = str(runner[0] / 'custom-buildx')
    result, events, images = run(runner, JENKINS_BUILDER='custom-builder',
                                BUILDX_CONFIG=custom, EXPECTED_BUILDX_CONFIG=custom)
    assert result.returncode == 0, result.stderr
    assert not images
    assert sum(e[0] == 'build' for e in events) == 12
