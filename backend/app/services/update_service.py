"""Bounded, unauthenticated stable-release discovery, cached per process.

Called from a sync endpoint (worker thread), never from application startup.
An unavailable GitHub API leaves the offline application fully usable.
"""
import json
from pathlib import Path
import re
import threading
import time

import httpx

from app.config.version import get_app_version
from app.schemas.updates import UpdateStatus

API_URL = 'https://api.github.com/repos/Pipepito/acestream-scraper/releases/latest'
RELEASE_URL = 'https://github.com/Pipepito/acestream-scraper/releases/tag/'
SUCCESS_TTL = 6 * 60 * 60
FAILURE_TTL = 15 * 60
MAX_BYTES = 256 * 1024
_lock = threading.Lock()
_cached: UpdateStatus | None = None
_expires = 0.0


def stable_version(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, str) or not re.fullmatch(r'v?(0|[1-9]\d{0,8})\.(0|[1-9]\d{0,8})(?:\.(0|[1-9]\d{0,8}))?', value):
        return None
    # Historical GitHub releases use tags such as v2.1; an omitted patch is zero.
    parts = [int(part) for part in value.lstrip('v').split('.')]
    return tuple((parts + [0])[:3])


def fetch_latest() -> dict:
    # Fixed public endpoint, no application token, redirects or environment proxies.
    deadline = time.monotonic() + 8
    with httpx.Client(timeout=3, follow_redirects=False, trust_env=False) as client:
        with client.stream('GET', API_URL, headers={
            'Accept': 'application/vnd.github+json',
            'Accept-Encoding': 'identity',
            'User-Agent': 'acestream-scraper-update-check',
        }) as response:
            response.raise_for_status()
            if response.headers.get('content-encoding', 'identity') != 'identity':
                raise ValueError('Unexpected compressed release response')
            data = bytearray()
            for chunk in response.iter_bytes(chunk_size=16384):
                if len(data) + len(chunk) > MAX_BYTES or time.monotonic() > deadline:
                    raise ValueError('Release response limit exceeded')
                data.extend(chunk)
    payload = json.loads(data)
    if not isinstance(payload, dict):
        raise ValueError('Invalid release response')
    return payload


def check_updates() -> UpdateStatus:
    global _cached, _expires
    current = get_app_version()
    deployment = 'docker' if Path('/.dockerenv').exists() or Path('/run/.containerenv').exists() else 'native'
    fallback = UpdateStatus(current_version=current, deployment=deployment, status='unavailable')
    # Other clients never pile up waiting for a slow external request.
    if not _lock.acquire(blocking=False):
        return _cached if _cached and _cached.current_version == current else fallback
    try:
        if _cached and _cached.current_version == current and time.monotonic() < _expires:
            return _cached
        result = fallback
        try:
            payload = fetch_latest()
            tag = payload.get('tag_name')
            latest = stable_version(tag)
            installed = stable_version(current)
            if (latest is None or installed is None or payload.get('draft') is not False
                    or payload.get('prerelease') is not False or not payload.get('published_at')):
                raise ValueError('Not a published stable release')
            result = UpdateStatus(current_version=current, latest_version=tag,
                                  update_available=latest > installed,
                                  release_url=RELEASE_URL + tag,
                                  deployment=deployment, status='checked')
        except (httpx.HTTPError, ValueError, UnicodeError, RecursionError):
            pass
        _cached = result
        _expires = time.monotonic() + (SUCCESS_TTL if result.status == 'checked' else FAILURE_TTL)
        return result
    finally:
        _lock.release()
