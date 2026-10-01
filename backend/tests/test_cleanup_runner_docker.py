"""Exercise runner retention, pressure escalation, and Docker failure handling."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('docker_lifecycle', ROOT / 'scripts/ci/docker_lifecycle.py')
lifecycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lifecycle)
NOW = 2_000_000_000


def image(name, *, key=None, legacy=False, created=NOW - 3600):
    from datetime import datetime, timezone
    labels = {}
    if key:
        labels = {lifecycle.PREFIX + 'kind': 'dependency-runner', lifecycle.PREFIX + 'inputs': key}
    if legacy:
        labels[lifecycle.PREFIX + 'keep'] = 'true'
    return {'Id': 'sha256:' + name, 'RepoTags': [name], 'RepoDigests': [],
            'Created': datetime.fromtimestamp(created, timezone.utc).isoformat(),
            'Os': 'linux', 'Architecture': 'amd64', 'Config': {'Labels': labels}}


def cached(char, **kwargs):
    key = char * 64
    return image(lifecycle.RUNNER_REPO + ':deps-' + key, key=key, **kwargs)


class Docker:
    def __init__(self, images=(), in_use=()):
        self.images = copy.deepcopy(list(images))
        self.in_use = list(in_use)
        self.calls = []
        self.modern = True
        self.prune_error = False
        self.platform = 'linux/amd64'

    def __call__(self, *args, capture=True):
        self.calls.append(args)
        if args[:3] == ('image', 'ls', '-aq'):
            return '\n'.join(im['Id'] for im in self.images)
        if args[:2] == ('image', 'inspect'):
            return json.dumps([im for im in self.images if im['Id'] in args[2:]
                               or set(im['RepoTags']) & set(args[2:])])
        if args[:3] == ('container', 'ls', '-aq'):
            return '\n'.join(str(n) for n in range(len(self.in_use)))
        if args[:2] == ('container', 'inspect'):
            return json.dumps([{'Image': im} for im in self.in_use])
        if args[:2] == ('buildx', 'ls'):
            return 'default\nacestream-builder\n'
        if args[:3] == ('buildx', 'prune', '--help'):
            return '--max-used-space --min-free-space --reserved-space' if self.modern else '--keep-storage'
        if args[:2] == ('buildx', 'prune'):
            if self.prune_error:
                raise RuntimeError('fixture prune failure')
            return ''
        if args[:2] == ('buildx', 'du'):
            return 'Total: 1GB\n'
        if args[0] == 'info':
            return '/'
        if args[0] == 'version':
            return self.platform
        if args[:2] == ('image', 'rm'):
            assert '--force' not in args and '-f' not in args
            self.images = [im for im in self.images if im['Id'] not in args[2:]
                           and not set(im['RepoTags']) & set(args[2:])]
            return ''
        if args[:2] == ('buildx', 'build'):
            ref = args[args.index('--tag') + 1]
            key = args[args.index('--label') + 1].split('=', 1)[1]
            built = image(ref, key=key)
            built['Os'], built['Architecture'] = self.platform.split('/')
            self.images.append(built)
            return ''
        if args[:2] == ('system', 'df'):
            return 'retained inventory'
        raise AssertionError(args)


def options(**kwargs):
    return argparse.Namespace(**dict({'keep': [], 'builder_keep': '8GB', 'min_free_gb': 8,
        'runner_keep_count': 2, 'runner_max_age_hours': 168, 'transient_age_hours': 0,
        'dry_run': False}, **kwargs))


@pytest.fixture
def host(monkeypatch, tmp_path):
    docker = Docker()
    monkeypatch.setattr(lifecycle, 'docker', docker)
    monkeypatch.setattr(lifecycle.time, 'time', lambda: NOW)
    monkeypatch.setenv('CI_DOCKER_STATE_DIR', str(tmp_path / 'state'))
    monkeypatch.setattr(lifecycle.os, 'statvfs', lambda path: SimpleNamespace(f_bavail=12, f_frsize=1024**3))
    return docker


def test_normal_retention_uses_last_usage_and_expires_old_runners():
    first, second, third = cached('a'), cached('b'), cached('c')
    expired = cached('d', created=NOW - 8 * 86400)
    old = image('acestream-scraper-pr-ci:develop', legacy=True)
    dangling = image('old-dangling', legacy=True)
    dangling['RepoTags'] = []
    unrelated = image('personal:latest')
    chosen = lifecycle.select([first, second, third, expired, old, dangling, unrelated], set(), [],
                              {first['Id']: NOW, second['Id']: NOW-1, third['Id']: NOW-2}, NOW)
    assert {im['Id'] for im in chosen} == {third['Id'], expired['Id'], old['Id'], dangling['Id']}


def test_keeps_protect_whole_image_and_container_references_even_under_pressure():
    selected, in_container, unused = cached('a'), cached('b'), cached('c')
    selected['RepoTags'].append('acestream-scraper-pr-ci:alias')
    chosen = lifecycle.select([selected, in_container, unused], {in_container['Id']},
                              ['acestream-scraper-pr-ci:alias'], {}, NOW, pressure=True)
    assert chosen == [unused]


def test_transient_age_and_unrelated_images_are_preserved():
    old = image('acestream-scraper:smoke-old', created=NOW - 4*3600)
    fresh = image('acestream-scraper:smoke-fresh')
    app, base = image('pipepito/acestream-scraper:latest'), image('python:3.12')
    assert lifecycle.select([old, fresh, app, base], set(), [], {}, NOW, transient_age=3) == [old]


def test_normal_cleanup_preserves_warm_layers_and_recent_runner(host):
    host.images = [cached('a'), image('acestream-scraper-pr-ci:release', legacy=True), image('unrelated:latest')]
    lifecycle.cleanup(options())
    assert len(host.images) == 2
    prunes = [c for c in host.calls if c[:2] == ('buildx', 'prune') and '--help' not in c]
    assert len(prunes) == 2
    assert all('until=24h' in c and '8GB' in c for c in prunes)
    assert not any(c[:2] == ('image', 'prune') for c in host.calls)


def test_pressure_reclaims_unused_runner_but_preserves_selected_alias(host, monkeypatch):
    selected, unused = cached('a'), cached('b')
    selected['RepoTags'].append('selected:alias')
    host.images = [selected, unused, image('unrelated:latest')]
    checks = iter([False, False, False, True])
    monkeypatch.setattr(lifecycle, 'free_space', lambda *args: next(checks))
    lifecycle.cleanup(options(keep=['selected:alias']))
    assert {im['Id'] for im in host.images} == {selected['Id'], 'sha256:unrelated:latest'}
    prunes = [c for c in host.calls if c[:2] == ('buildx', 'prune') and '--help' not in c]
    assert sum('--min-free-space' in c and '--filter' not in c for c in prunes) == 2


def test_insufficient_space_reports_failure_without_deleting_unrelated_data(host, monkeypatch, capsys):
    host.images = [image('unrelated:latest')]
    monkeypatch.setattr(lifecycle, 'free_space', lambda *args: False)
    with pytest.raises(RuntimeError, match='cannot meet'):
        lifecycle.cleanup(options())
    assert len(host.images) == 1
    assert 'retained inventory' in capsys.readouterr().out


def test_dry_run_performs_no_mutations(host):
    host.images = [image('acestream-scraper-pr-ci:develop', legacy=True)]
    lifecycle.cleanup(options(dry_run=True))
    assert not any(c[:2] == ('image', 'rm') for c in host.calls)
    assert not any(c[:2] == ('buildx', 'prune') and '--help' not in c for c in host.calls)


def test_prune_errors_are_not_silenced_or_retried_with_different_policy(host):
    host.prune_error = True
    with pytest.raises(RuntimeError, match='fixture prune failure'):
        lifecycle.cleanup(options())
    assert len([c for c in host.calls if c[:2] == ('buildx', 'prune') and '--help' not in c]) == 1


def test_old_buildx_option_is_selected_from_capabilities(host):
    host.modern = False
    lifecycle.prune('default', '8GB')
    assert ('buildx', 'prune', '--builder', 'default', '-af', '--keep-storage', '8GB') in host.calls


def test_inventory_failure_stops_before_deletion(host, monkeypatch):
    monkeypatch.setattr(lifecycle, 'inventory', lambda: (_ for _ in ()).throw(RuntimeError('inspection failed')))
    with pytest.raises(RuntimeError, match='inspection failed'):
        lifecycle.cleanup(options())
    assert host.calls == []


@pytest.fixture
def context(tmp_path):
    for name in lifecycle.INPUTS:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
    return argparse.Namespace(context=str(tmp_path), image_file=str(tmp_path / 'runner-ref'))


def test_same_inputs_reuse_runner_and_refresh_usage(host, context):
    lifecycle.ensure_runner(context)
    first = Path(context.image_file).read_text()
    # Arbitrary source changes cannot invalidate dependencies.
    (Path(context.context) / 'application.py').write_text('changed')
    lifecycle.ensure_runner(context)
    assert Path(context.image_file).read_text() == first
    assert sum(c[:2] == ('buildx', 'build') for c in host.calls) == 1
    assert lifecycle.read_usage()[host.images[0]['Id']] == NOW


@pytest.mark.parametrize('name', lifecycle.INPUTS)
def test_each_dependency_input_invalidates_runner(host, context, name):
    lifecycle.ensure_runner(context)
    first = Path(context.image_file).read_text()
    (Path(context.context) / name).write_text('new dependency input')
    lifecycle.ensure_runner(context)
    assert Path(context.image_file).read_text() != first
    assert sum(c[:2] == ('buildx', 'build') for c in host.calls) == 2


def test_platform_change_never_reuses_other_architecture(host, context):
    lifecycle.ensure_runner(context)
    first = Path(context.image_file).read_text()
    host.platform = 'linux/arm64'
    lifecycle.ensure_runner(context)
    assert Path(context.image_file).read_text() != first
    assert sum(c[:2] == ('buildx', 'build') for c in host.calls) == 2


def test_identity_mismatch_fails_before_cleanup_or_build(host, context):
    lifecycle.ensure_runner(context)
    host.images[0]['Config']['Labels'][lifecycle.PREFIX + 'inputs'] = 'wrong'
    host.calls.clear()
    with pytest.raises(RuntimeError, match='mismatched identity'):
        lifecycle.ensure_runner(context)
    assert not any(c[:2] == ('buildx', 'build') or c[:2] in [('image', 'rm'), ('buildx', 'prune')] for c in host.calls)


def test_symlink_input_is_rejected(host, context):
    path = Path(context.context) / lifecycle.INPUTS[0]
    path.unlink()
    path.symlink_to(Path(context.context) / lifecycle.INPUTS[1])
    with pytest.raises(RuntimeError, match='regular file'):
        lifecycle.ensure_runner(context)


def test_selected_runner_counts_toward_retention_limit():
    first, second, third = cached('a'), cached('b'), cached('c')
    chosen = lifecycle.select([first, second, third], set(), first['RepoTags'],
                              {second['Id']: NOW, third['Id']: NOW-1}, NOW)
    assert chosen == [third]


def test_container_created_after_planning_protects_image(host, monkeypatch):
    old = image('acestream-scraper-pr-ci:develop', legacy=True)
    host.images = [old]
    original = lifecycle.inventory
    invocations = 0

    def inventory():
        nonlocal invocations
        invocations += 1
        if invocations > 1:
            host.in_use = [old['Id']]
        return original()

    monkeypatch.setattr(lifecycle, 'inventory', inventory)
    lifecycle.cleanup(options())
    assert host.images == [old]
    assert not any(c[:2] == ('image', 'rm') for c in host.calls)


def test_runner_builder_exports_only_committed_trusted_inputs(tmp_path):
    """The working tree and selected application code cannot enter a networked build."""
    import os
    import subprocess

    repo = tmp_path / 'repo'
    repo.mkdir()
    def git(*args):
        return subprocess.run(['git', '-C', str(repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()
    git('init', '-q')
    for name in lifecycle.INPUTS:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('trusted')
    policy = repo / 'scripts/ci/docker_lifecycle.py'
    policy.parent.mkdir(parents=True)
    policy.write_text('''from pathlib import Path
import sys
root = Path(__file__).resolve().parents[2]
assert (root / 'backend/requirements.txt').read_text() == 'trusted'
assert not (root / 'application.py').exists()
assert not (root / 'secrets.txt').exists()
Path(sys.argv[sys.argv.index('--image-file') + 1]).write_text('trusted-runner')
''')
    git('add', '.')
    git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'trusted inputs')
    trusted = git('rev-parse', 'HEAD')
    (repo / 'backend/requirements.txt').write_text('untrusted')
    policy.write_text("raise RuntimeError('fork policy executed')")
    (repo / 'application.py').write_text('unrelated source')
    (repo / 'secrets.txt').write_text('must not enter build context')
    git('add', '.')
    git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', 'fork changes')
    output = tmp_path / 'runner'
    result = subprocess.run(['bash', str(ROOT / 'scripts/ci/build_pr_runner.sh'),
        '--source', str(repo), '--ref', trusted, '--image-file', str(output)],
        capture_output=True, text=True, env=os.environ, timeout=10)
    assert result.returncode == 0, result.stderr
    assert output.read_text() == 'trusted-runner'


def test_build_failure_does_not_publish_runner_reference(host, context, monkeypatch):
    original = host.__call__
    def failed_build(*args, **kwargs):
        if args[:2] == ('buildx', 'build'):
            raise RuntimeError('dependency install failed')
        return original(*args, **kwargs)
    monkeypatch.setattr(lifecycle, 'docker', failed_build)
    with pytest.raises(RuntimeError, match='dependency install failed'):
        lifecycle.ensure_runner(context)
    assert not Path(context.image_file).exists()


def test_build_reserves_a_retention_slot_and_loads_into_local_daemon(host, context):
    host.images = [cached('a'), cached('b')]
    lifecycle.ensure_runner(context)
    assert len(host.images) == 2
    build = next(c for c in host.calls if c[:2] == ('buildx', 'build'))
    assert build[build.index('--builder') + 1] == 'default'
    assert '--load' in build


def test_failed_identity_does_not_leave_previous_output_reference(host, context):
    lifecycle.ensure_runner(context)
    host.images[0]['Architecture'] = 'arm64'
    with pytest.raises(RuntimeError, match='mismatched identity'):
        lifecycle.ensure_runner(context)
    assert not Path(context.image_file).exists()


def test_pressure_can_be_resolved_without_evicting_any_runner(host, monkeypatch):
    host.images = [cached('a'), cached('b')]
    checks = iter([False, True])
    monkeypatch.setattr(lifecycle, 'free_space', lambda *args: next(checks))
    lifecycle.cleanup(options())
    assert len(host.images) == 2
    pressure = [c for c in host.calls if '--min-free-space' in c]
    assert len(pressure) == 1
    assert pressure[0][pressure[0].index('--min-free-space')+1] == str(8 * 1024**3)


def test_pressure_stops_after_oldest_runner_frees_enough_space(host, monkeypatch):
    older, newer = cached('a'), cached('b')
    host.images = [older, newer]
    monkeypatch.setattr(lifecycle, 'read_usage', lambda: {older['Id']: NOW-10, newer['Id']: NOW})
    checks = iter([False, False, False, True])
    monkeypatch.setattr(lifecycle, 'free_space', lambda *args: next(checks))
    lifecycle.cleanup(options())
    assert host.images == [newer]
