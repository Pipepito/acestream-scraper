#!/usr/bin/env python3
"""Bind canonical notes to a release commit and a promoted OCI index."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

REVISION = 'org.opencontainers.image.revision'
VERSION = 'org.opencontainers.image.version'
NOTES_HASH = 'io.acestream-scraper.release-notes-sha256'
ARTIFACTS = Path('.ci-release-artifacts')
METADATA = Path('phase5-build-result-release-metadata.json')


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def notes_for(version, sha):
    if not re.fullmatch(r'v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version):
        raise ValueError('Invalid release version')
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Invalid release commit')
    if run('git', 'show', f'{sha}:version.txt') != version:
        raise ValueError('Release commit has a different version')
    body = subprocess.check_output(['git', 'show', f'{sha}:frontend/changelog/{version}.md'])
    if not body.startswith(f'# {version}\n'.encode()) or len(body) > 100_000:
        raise ValueError('Invalid release notes')
    return body, hashlib.sha256(body).hexdigest()


def save_notes(version, sha):
    body, digest = notes_for(version, sha)
    ARTIFACTS.mkdir(exist_ok=True)
    (ARTIFACTS / 'release-notes.md').write_bytes(body)
    (ARTIFACTS / 'release-notes.json').write_text(json.dumps({
        'version': version, 'git_sha': sha, 'notes_sha256': digest,
    }, indent=2) + '\n')
    return digest


def inspect_digest(ref):
    manifest = json.loads(run('docker', 'buildx', 'imagetools', 'inspect', ref,
                              '--format', '{{json .Manifest}}'))
    digest = manifest.get('digest', '')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', digest):
        raise ValueError('Registry returned an invalid index digest')
    return digest


def promote(version, repo, flavor):
    # Remove stale success evidence before any failure is possible.
    METADATA.unlink(missing_ok=True)
    source = f'{repo}:{version}'
    digest = inspect_digest(source)
    pinned = f'{repo}@{digest}'
    manifest = json.loads(run('docker', 'buildx', 'imagetools', 'inspect', pinned, '--raw'))
    annotations = manifest.get('annotations', {})
    sha = annotations.get(REVISION, '')
    if annotations.get(VERSION) != version:
        raise ValueError('Published image has no matching release version annotation')
    notes_hash = save_notes(version, sha)
    if annotations.get(NOTES_HASH) != notes_hash:
        raise ValueError('Published image and committed notes differ')
    # A release may have been built from an older main commit, never an unrelated ref.
    subprocess.run(['git', 'merge-base', '--is-ancestor', sha, 'HEAD'], check=True)
    subprocess.run(['docker', 'buildx', 'imagetools', 'create', '-t', f'{repo}:latest', pinned], check=True)
    subprocess.run(['bash', 'scripts/ci/verify_multiarch_manifest.sh', '--image', f'{repo}:latest', '--flavor', flavor], check=True)
    if inspect_digest(f'{repo}:latest') != digest:
        raise ValueError('Promoted latest digest does not match the validated source')
    METADATA.write_text(json.dumps({
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'mode': 'promote-latest', 'version': version, 'git_sha': sha,
        'source': source, 'source_digest': digest, 'notes_sha256': notes_hash,
        'tags': [f'{repo}:latest'],
    }, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'promote'])
    parser.add_argument('--version', required=True)
    parser.add_argument('--sha')
    parser.add_argument('--repo', default='pipepito/acestream-scraper')
    parser.add_argument('--flavor', default='scraper-acestream-acexy')
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--',
                            'frontend/changelog', 'frontend/src/data/changelog.ts', 'version.txt'], check=True)
            print(save_notes(args.version, args.sha or run('git', 'rev-parse', 'HEAD')))
        else:
            promote(args.version, args.repo, args.flavor)
    except (ValueError, subprocess.CalledProcessError, OSError) as exc:
        parser.exit(1, f'Release notes: {exc}\n')
