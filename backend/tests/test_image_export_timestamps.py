"""Ensure every image export normalizes timestamps without enabling publication."""
import os
from pathlib import Path
import shlex
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[2]
APP = Path(os.environ.get("APP_TEST_ROOT", ROOT))


@pytest.mark.parametrize("mode,expected_exports", [
    (["--load"], ["type=docker,dest=-,rewrite-timestamp=true"]),
    (["--push"], ["type=image,push=true,rewrite-timestamp=true"]),
    (["--push-by-digest", "--repo", "example.invalid/app"],
     ["type=image,name=example.invalid/app,push=true,push-by-digest=true,name-canonical=true,rewrite-timestamp=true"]),
    ([], ["type=cacheonly"]),
])
def test_export_options_and_epoch(mode, expected_exports):
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/ci/build_multiarch_images.sh"),
         "--dry-run", "--flavor", "scraper", "--platforms", "linux/arm64",
         "--tag", "example.invalid/app:test", *mode],
        cwd=APP, env={**os.environ, "APP_ROOT": str(APP), "SOURCE_DATE_EPOCH": "1793355726"},
        text=True, capture_output=True, check=True,
    )
    commands = [shlex.split(line.removeprefix("[DRY RUN] ")) for line in result.stdout.splitlines()
                if line.startswith("[DRY RUN] docker buildx build ")]
    assert len(commands) == 1
    args = commands[0]
    assert [args[i+1] for i, v in enumerate(args) if v == "--output"] == expected_exports
    assert "SOURCE_DATE_EPOCH=946684800" in args
    assert "1793355726" not in " ".join(args)
    if "--load" in mode or not mode:
        assert "push=true" not in " ".join(args)
        assert "imagetools create" not in result.stdout


def test_each_architecture_in_multi_platform_publication_normalizes_timestamps():
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/ci/build_multiarch_images.sh"),
         "--dry-run", "--flavor", "scraper", "--push", "--tag", "example.invalid/app:test"],
        cwd=APP, env={**os.environ, "APP_ROOT": str(APP)},
        text=True, capture_output=True, check=True,
    )
    commands = [shlex.split(line.removeprefix("[DRY RUN] ")) for line in result.stdout.splitlines()
                if line.startswith("[DRY RUN] docker buildx build ")]
    assert len(commands) == 3
    for args in commands:
        assert "SOURCE_DATE_EPOCH=946684800" in args
        assert "rewrite-timestamp=true" in args[args.index("--output")+1]
        assert "push-by-digest=true" in args[args.index("--output")+1]


@pytest.mark.parametrize("build_status,load_status,expected", [(0, 0, 0), (23, 0, 23), (0, 31, 31)])
def test_load_streams_normalized_image_and_preserves_failures(tmp_path, build_status, load_status, expected):
    import sys
    fake = tmp_path / 'docker'
    fake.write_text(f'#!{sys.executable}\n' + '''
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ['DOCKER_EVENTS']).open('a') as f:
    f.write(json.dumps(args) + '\\n')
if args[:2] == ['buildx', 'build']:
    assert 'type=docker,dest=-,rewrite-timestamp=true' in args
    assert not any('push=true' in arg for arg in args)
    sys.stdout.write('normalized-image-stream')
    raise SystemExit(int(os.environ['BUILD_STATUS']))
if args == ['load']:
    assert sys.stdin.read() == 'normalized-image-stream'
    raise SystemExit(int(os.environ['LOAD_STATUS']))
raise AssertionError(args)
''')
    fake.chmod(0o755)
    events = tmp_path / 'events.jsonl'
    result = subprocess.run(
        ['bash', str(ROOT / 'scripts/ci/build_multiarch_images.sh'), '--flavor', 'scraper',
         '--platforms', 'linux/arm64', '--load', '--tag', 'example.invalid/app:test'],
        cwd=APP, env={**os.environ, 'APP_ROOT': str(APP), 'PATH': str(tmp_path)+os.pathsep+os.environ['PATH'],
                      'DOCKER_EVENTS': str(events), 'BUILD_STATUS': str(build_status), 'LOAD_STATUS': str(load_status)},
        text=True, capture_output=True,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    assert len(events.read_text().splitlines()) == 2
