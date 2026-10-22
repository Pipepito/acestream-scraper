#!/usr/bin/env python3
"""Publish identical canonical notes only from verified promotion evidence.

Safe to retry after GitHub failure without building or promoting images again.
Existing tags and releases must match; this tool never edits or overwrites them.
"""
import argparse
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

from release_notes import METADATA, inspect_digest, notes_for

API = 'https://api.github.com/repos/Pipepito/acestream-scraper'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHub:
    def __init__(self):
        self.token = os.environ.get('GITHUB_PUBLISH_TOKEN')
        if not self.token:
            raise ValueError('GITHUB_PUBLISH_TOKEN is required')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def request(self, method, path, data=None):
        request = urllib.request.Request(API + path, method=method,
            data=json.dumps(data).encode() if data is not None else None,
            headers={'Authorization': f'Bearer {self.token}', 'Accept': 'application/vnd.github+json',
                     'Content-Type': 'application/json', 'User-Agent': 'acestream-scraper-release'})
        try:
            with self.opener.open(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            exc.close()
            if method == 'GET' and exc.code == 404:
                return None
            # Never include upstream body, headers or credentials in logs.
            raise ValueError(f'GitHub {method} failed with HTTP {exc.code}; retry publication after resolving access') from None
        except urllib.error.URLError:
            raise ValueError('GitHub unavailable; retry publication') from None


def verify_tag(api, version, sha):
    ref = api.request('GET', f'/git/ref/tags/{version}')
    if ref is None:
        return False
    obj = ref['object']
    for _ in range(8):
        if obj['type'] == 'commit':
            if obj['sha'] != sha:
                raise ValueError('Existing version tag points at a different commit; refusing to overwrite')
            return True
        if obj['type'] != 'tag' or not re.fullmatch(r'[0-9a-f]{40}', obj['sha']):
            break
        tag = api.request('GET', f"/git/tags/{obj['sha']}")
        obj = tag['object']
    raise ValueError('Cannot resolve existing version tag')


def publish(metadata, api):
    if metadata.get('mode') != 'promote-latest' or metadata.get('dry_run'):
        raise ValueError('Successful non-dry-run promotion metadata is required')
    version, sha = metadata['version'], metadata['git_sha']
    body, digest = notes_for(version, sha)
    if digest != metadata.get('notes_sha256'):
        raise ValueError('Release notes hash differs from promotion evidence')
    repo = 'pipepito/acestream-scraper'
    if metadata.get('source') != f'{repo}:{version}' or metadata.get('tags') != [f'{repo}:latest']:
        raise ValueError('Unexpected promoted repository')
    if inspect_digest(f'{repo}:latest') != metadata.get('source_digest'):
        raise ValueError('Latest no longer matches this promotion; refusing stale publication')
    has_tag = verify_tag(api, version, sha)
    existing = api.request('GET', f'/releases/tags/{version}')
    if existing:
        if (not has_tag or existing.get('body') != body.decode() or existing.get('draft') is not False
                or existing.get('prerelease') is not False):
            raise ValueError('Existing release differs; refusing to overwrite')
        print(f'GitHub release {version} already matches')
        return
    if not has_tag:
        api.request('POST', '/git/refs', {'ref': f'refs/tags/{version}', 'sha': sha})
    # Re-read even after creating it, before publishing anything visible to users.
    if not verify_tag(api, version, sha):
        raise ValueError('Release tag is missing')
    api.request('POST', '/releases', {'tag_name': version, 'target_commitish': sha,
        'name': version, 'body': body.decode(), 'draft': False, 'prerelease': False,
        'generate_release_notes': False, 'make_latest': 'true'})
    print(f'Published GitHub release {version}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, default=METADATA)
    args = parser.parse_args()
    try:
        publish(json.loads(args.metadata.read_text()), GitHub())
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f'GitHub release publication failed: {exc}\nImages are already promoted; retry this helper after correcting the failure.\n')
