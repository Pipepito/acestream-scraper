#!/usr/bin/env python3
"""Host-only Docker retention and dependency-runner reuse, under the CI FIFO lock.

Never imported or executed from a fork checkout on the host. build_pr_runner.sh
exports this file from the trusted validation ref alongside its build inputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime

PREFIX = 'org.acestream-scraper.ci.'
RUNNER_REPO = 'acestream-scraper-pr-ci'
INPUTS = ('backend/requirements.txt', 'frontend/package.json',
          'frontend/package-lock.json', 'docker/ci/pr-runner.Dockerfile')
TRANSIENT = re.compile(r'^(acestream-scraper:(smoke-|release-smoke$)|'
                       r'acestream-scraper-smoke:|acestream-installer-test:|acestream-scraper-task3:)')


def docker(*args, capture=True):
    result = subprocess.run(['docker', *args], text=True, capture_output=capture)
    if result.returncode:
        raise RuntimeError(f"docker {' '.join(args)} failed ({result.returncode}): "
                           f"{result.stderr or ''}")
    return result.stdout or ''


def records(kind, ids):
    return json.loads(docker(kind, 'inspect', *ids)) if ids else []


def inventory():
    ids = docker('image', 'ls', '-aq', '--no-trunc').split()
    images = records('image', sorted(set(ids)))
    containers = records('container', docker('container', 'ls', '-aq').split())
    return images, {item['Image'] for item in containers}


def created(image):
    # Docker uses nanosecond RFC3339 timestamps; datetime supports microseconds.
    return datetime.fromisoformat(re.sub(r'(\.\d{6})\d+', r'\1', image['Created'])
                                  .replace('Z', '+00:00')).timestamp()


def tags(image):
    return [tag for tag in image.get('RepoTags') or [] if tag != '<none>:<none>']


def labels(image):
    return image.get('Config', {}).get('Labels') or {}


def runner(image):
    return (labels(image).get(PREFIX + 'kind') == 'dependency-runner'
            or any(tag.startswith(RUNNER_REPO + ':') for tag in tags(image))
            # Includes dangling images from the retired permanently-kept runners.
            or labels(image).get(PREFIX + 'keep') == 'true')


def reusable(image):
    return (labels(image).get(PREFIX + 'kind') == 'dependency-runner'
            and any(re.fullmatch(RUNNER_REPO + r':deps-[a-f0-9]{64}', t) for t in tags(image)))


def state_file():
    return Path(os.environ.get('CI_DOCKER_STATE_DIR',
                str(Path.home() / '.cache/acestream-ci'))) / 'runner-usage.json'


def read_usage():
    path = state_file()
    try:
        values = json.loads(path.read_text())
        return {k: float(v) for k, v in values.items()}
    except FileNotFoundError:
        return {}
    except (ValueError, TypeError, AttributeError, OSError) as exc:
        print(f'WARNING: cannot read runner usage: {exc}', file=sys.stderr)
        return {}


def remember(image_id):
    usage = read_usage()
    live, _ = inventory()
    usage = {im['Id']: usage[im['Id']] for im in live if im['Id'] in usage}
    usage[image_id] = time.time()
    path = state_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(usage))
    temporary.replace(path)


def select(images, in_use, keep, usage, now, pressure=False, count=2, age=168, transient_age=0):
    protected = in_use | {im['Id'] for im in images
                          if im['Id'] in keep or set(tags(im)) & set(keep)}
    eligible = [im for im in images if im['Id'] not in protected]
    cached = sorted((im for im in eligible if reusable(im)),
                    key=lambda im: usage.get(im['Id'], created(im)), reverse=True)
    # Explicit keeps also count toward the normal runner retention limit.
    slots = max(0, count - sum(reusable(im) and im['Id'] in protected for im in images))
    retained = set() if pressure else {
        im['Id'] for im in cached[:slots]
        if now - usage.get(im['Id'], created(im)) < age * 3600
    }
    chosen = []
    for im in eligible:
        if runner(im):
            if im['Id'] not in retained:
                chosen.append(im)
        elif any(TRANSIENT.search(t) for t in tags(im)):
            if now - created(im) >= transient_age * 3600:
                chosen.append(im)
    return chosen


def prune(builder, cap, cold_hours=0, dry=False, minimum_free=0):
    common = ['buildx', 'prune', '--builder', builder, '-af']
    if cold_hours:
        common += ['--filter', f'until={cold_hours}h']
    help_text = docker('buildx', 'prune', '--help')
    option = '--max-used-space' if '--max-used-space' in help_text else '--keep-storage'
    if minimum_free and '--min-free-space' in help_text:
        command = [*common, '--min-free-space', str(minimum_free * 1024**3)]
        if '--reserved-space' in help_text:
            command += ['--reserved-space', '1GB']
    else:
        command = [*common, option, cap]
    print(('Plan: ' if dry else 'Pruning: ') + 'docker ' + ' '.join(command), flush=True)
    if not dry:
        docker(*command, capture=False)
    print(docker('buildx', 'du', '--builder', builder), end='', flush=True)


def free_space(paths, minimum):
    okay = True
    for path in paths:
        stats = os.statvfs(path)
        free = stats.f_bavail * stats.f_frsize
        print(f'Free space on {path}: {free / 1024**3:.2f} GiB (need {minimum} GiB)', flush=True)
        okay &= free >= minimum * 1024**3
    return okay


def cleanup(args):
    images, in_use = inventory()  # Fail closed before making any deletion plan.
    # A miss is expected before a runner build. Existing keep references must
    # resolve to IDs so aliases cannot bypass protection.
    keep = list(args.keep)
    for ref in args.keep:
        if any(ref == im['Id'] or ref in tags(im) or ref in (im.get('RepoDigests') or []) for im in images):
            keep.extend(im['Id'] for im in records('image', [ref]))
    usage = read_usage()
    now = time.time()
    builders = docker('buildx', 'ls', '--format', '{{.Name}}').split()
    builders = sorted(set(name.rstrip('*') for name in builders))
    if not builders:
        raise RuntimeError('No builders could be inspected; refusing incomplete cleanup')
    paths = list(dict.fromkeys([os.environ.get('JENKINS_AGENT_DIR', os.environ.get('WORKSPACE', '/')),
                               docker('info', '--format', '{{.DockerRootDir}}').strip()]))
    if any(not path for path in paths):
        raise RuntimeError('Cannot determine Docker filesystem for free-space preflight')

    def remove(chosen, reason):
        for im in chosen:
            refs = tags(im) or [im['Id']]
            print(f"{'Plan' if args.dry_run else 'Removing'} {', '.join(refs)} ({reason})", flush=True)
            if not args.dry_run:
                # Re-read container references before each removal; no --force.
                _, current_use = inventory()
                if im['Id'] in current_use:
                    print('Retaining image now referenced by a container', flush=True)
                    continue
                docker('image', 'rm', *refs, capture=False)

    remove(sorted(select(images, in_use, keep, usage, now, count=args.runner_keep_count,
                  age=args.runner_max_age_hours, transient_age=args.transient_age_hours),
                  key=created, reverse=True),
           'expired/superseded CI image')
    for builder in builders:
        prune(builder, args.builder_keep, cold_hours=24, dry=args.dry_run)
    if args.dry_run:
        print('Under disk pressure: reclaim recent build cache first, then evict unused CI '
              'runners least-recently-used first, stopping once space is sufficient. '
              'Keep explicit images and container references; never remove volumes.')
        return
    if free_space(paths, args.min_free_gb):
        return
    print('Disk pressure: reclaiming recent build cache before reusable runners', flush=True)

    def reclaim_cache():
        for builder in builders:
            # Modern Buildx targets only the required headroom. Older versions
            # fall back to a bounded 1GB cache, with the chosen policy logged.
            prune(builder, '1GB', minimum_free=args.min_free_gb)
            if free_space(paths, args.min_free_gb):
                return True
        return False

    if reclaim_cache():
        return
    images, in_use = inventory()
    candidates = select(images, in_use, keep, usage, now, pressure=True,
                        transient_age=args.transient_age_hours)
    for im in sorted(candidates, key=lambda im: usage.get(im['Id'], created(im))):
        remove([im], 'disk pressure: least recently used runner')
        if free_space(paths, args.min_free_gb) or reclaim_cache():
            return
    print(docker('system', 'df', '-v'), flush=True)
    raise RuntimeError('Cleanup cannot meet the free-space minimum without removing protected '
                       'or unrelated data. Inspect retained images and filesystem usage.')


def ensure_runner(args):
    context = Path(args.context)
    Path(args.image_file).unlink(missing_ok=True)
    platform = docker('version', '--format', '{{.Server.Os}}/{{.Server.Arch}}').strip()
    if not re.fullmatch(r'linux/(amd64|arm64)', platform):
        raise RuntimeError(f'Unsupported runner platform: {platform!r}')
    digest = hashlib.sha256(b'acestream-dependency-runner-v1\0' + platform.encode() + b'\0')
    for name in INPUTS:
        path = context / name
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f'Runner input must be a regular file: {name}')
        digest.update(name.encode() + b'\0' + path.read_bytes() + b'\0')
    key = digest.hexdigest()
    ref = f'{RUNNER_REPO}:deps-{key}'
    images, _ = inventory()
    matches = [im for im in images if ref in tags(im)]
    if matches and (labels(matches[0]).get(PREFIX + 'inputs') != key
                    or labels(matches[0]).get(PREFIX + 'kind') != 'dependency-runner'
                    or f"{matches[0]['Os']}/{matches[0]['Architecture']}" != platform):
        raise RuntimeError(f'Cached runner {ref} has mismatched identity; refusing reuse')
    # Protect the exact selected image (including all aliases) during cleanup.
    cleanup(argparse.Namespace(keep=[ref], builder_keep='8GB', min_free_gb=8,
                              runner_keep_count=2 if matches else 1, runner_max_age_hours=168,
                              transient_age_hours=0, dry_run=False))
    if matches:
        print(f'Reusing dependency runner {ref}', flush=True)
    else:
        print(f'Building dependency runner {ref} for {platform}', flush=True)
        docker('buildx', 'build', '--builder', 'default', '--load', '--platform', platform, '--file', str(context / INPUTS[-1]),
               '--label', PREFIX + 'inputs=' + key, '--tag', ref, str(context), capture=False)
    image = records('image', [ref])[0]
    if (labels(image).get(PREFIX + 'inputs') != key
            or labels(image).get(PREFIX + 'kind') != 'dependency-runner'
            or f"{image['Os']}/{image['Architecture']}" != platform):
        raise RuntimeError(f'Prepared runner {ref} has mismatched identity')
    remember(image['Id'])
    Path(args.image_file).write_text(ref + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    clean = sub.add_parser('cleanup')
    clean.add_argument('--keep', action='append', default=[])
    clean.add_argument('--transient-age-hours', type=float, default=0)
    clean.add_argument('--builder-keep', default='8GB')
    clean.add_argument('--min-free-gb', type=int, default=8)
    clean.add_argument('--runner-keep-count', type=int, default=2)
    clean.add_argument('--runner-max-age-hours', type=float, default=168)
    clean.add_argument('--dry-run', action='store_true')
    ensure = sub.add_parser('runner')
    ensure.add_argument('--context', required=True)
    ensure.add_argument('--image-file', required=True)
    cache = sub.add_parser('prune')
    cache.add_argument('--builder', required=True)
    cache.add_argument('--cap', required=True)
    cache.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'cleanup':
            if min(args.min_free_gb, args.runner_keep_count, args.runner_max_age_hours,
                   args.transient_age_hours) < 0:
                parser.error('Retention and free-space values cannot be negative')
            cleanup(args)
        elif args.command == 'runner':
            ensure_runner(args)
        else:
            prune(args.builder, args.cap, dry=args.dry_run)
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
