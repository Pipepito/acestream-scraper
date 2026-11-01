"""Persistent WARP host exclusions, shared by the API and sidecar startup.

Stdlib only; fixed CLI argv, bounded input, no shell execution. Only hosts
managed here are removed; unrelated WARP exclusions are preserved.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time

from runtime_config import ConfigConflict, ConfigError, config_path, locked, write_config

MAX_HOSTS = 64


def normalize_hosts(hosts: list[str]) -> list[str]:
    if not isinstance(hosts, list) or len(hosts) > MAX_HOSTS:
        raise ConfigError('Use at most 64 hostnames.')
    result = []
    for raw in hosts:
        if not isinstance(raw, str):
            raise ConfigError('Enter hostnames only, without URLs, ports or wildcards.')
        host = raw.strip().lower().rstrip('.')
        if (len(host) > 253 or '.' not in host or any(
                not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label)
                for label in host.split('.'))):
            raise ConfigError('Enter hostnames only, without URLs, ports or wildcards.')
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ConfigError('Enter hostnames, not IP addresses.')
        if host not in result:
            result.append(host)
    return sorted(result)


def exclusions_path(database_url: str | None = None) -> Path:
    return config_path(database_url).with_name('warp-exclusions.json')


def read_state(path: Path) -> dict:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        hosts = normalize_hosts(re.split(r'[,\s]+', os.environ.get('WARP_EXCLUDE_HOSTS', '').strip())) if os.environ.get('WARP_EXCLUDE_HOSTS', '').strip() else []
        return {'version': 1, 'hosts': hosts, 'managed_hosts': hosts}
    except OSError:
        raise ConfigError('Cannot read WARP exclusions; check file permissions and type.') from None
    try:
        with os.fdopen(fd) as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 65536:
                raise ValueError
            data = json.load(stream)
        if (not isinstance(data, dict) or set(data) != {'version', 'hosts', 'managed_hosts'}
                or type(data['version']) is not int or data['version'] != 1):
            raise ValueError
        # A failed apply can retain one previous list for safe removal on retry.
        managed = data['managed_hosts']
        if not isinstance(managed, list) or len(managed) > MAX_HOSTS * 2:
            raise ValueError
        data['hosts'] = normalize_hosts(data['hosts'])
        data['managed_hosts'] = sorted(set(normalize_hosts(managed[:MAX_HOSTS]) + normalize_hosts(managed[MAX_HOSTS:])))
        return data
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise ConfigError('Invalid WARP exclusions file; restore it before saving.') from None


def revision(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class WarpExclusions:
    def __init__(self, path: Path):
        self.path = path

    def command(self, args: list[str], deadline: float) -> str:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise ConfigError('WARP took too long to apply exclusions. Retry when it is available.')
        try:
            result = subprocess.run(['warp-cli', '--accept-tos', *args], capture_output=True,
                                    text=True, timeout=min(5, remaining), check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise ConfigError('WARP is unavailable or did not answer. Start WARP and retry.') from None
        if result.returncode:
            raise ConfigError('WARP rejected the exclusions command. Check that a consumer WARP client is running.')
        return result.stdout

    def active(self, deadline: float) -> list[str]:
        try:
            data = json.loads(self.command(['--json', 'tunnel', 'host', 'list'], deadline))
            if data.get('mode') != 'exclude':
                raise ConfigError('WARP is not using exclusion mode. Its managed policy must be changed outside the app.')
            entries = data['hosts']
            if not isinstance(entries, list) or len(entries) > 1024:
                raise ValueError
            hosts = [item['value'] if isinstance(item, dict) else item for item in entries]
            if any(not isinstance(host, str) or len(host) > 253 for host in hosts):
                raise ValueError
            return sorted(set(host.lower().rstrip('.') for host in hosts))
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            if isinstance(exc, ConfigError):
                raise
            raise ConfigError('WARP returned an unsupported exclusion list.') from None

    def view(self, data: dict, deadline: float) -> dict:
        try:
            active = self.active(deadline)
            error = None
        except ConfigError as exc:
            active, error = None, str(exc)
        desired = set(data['hosts'])
        removed = set(data['managed_hosts']) - desired
        return {'hosts': data['hosts'], 'revision': revision(data), 'active_hosts': active,
                'applied': active is not None and desired <= set(active) and not removed.intersection(active),
                'error': error}

    def state(self) -> dict:
        with locked(self.path):
            return self.view(read_state(self.path), time.monotonic() + 10)

    def reconcile(self, data: dict, deadline: float) -> None:
        active = set(self.active(deadline))
        desired = set(data['hosts'])
        # Add first to avoid routing a replacement host through the tunnel.
        for host in sorted(desired - active):
            self.command(['tunnel', 'host', 'add', host], deadline)
        for host in sorted((set(data['managed_hosts']) - desired) & active):
            self.command(['tunnel', 'host', 'remove', host], deadline)
        result = self.view(data, deadline)
        if not result['applied']:
            raise ConfigError(result['error'] or 'WARP has not applied the saved exclusions. Retry applying them.')

    def save(self, hosts: list[str], expected_revision: str) -> dict:
        hosts = normalize_hosts(hosts)
        with locked(self.path):
            current = read_state(self.path)
            if revision(current) != expected_revision:
                raise ConfigConflict('Exclusions changed in another session. Reload before saving.')
            managed = sorted(set(current['managed_hosts']) | set(hosts))
            if len(managed) > MAX_HOSTS * 2:
                raise ConfigError('Apply the previous changes before adding more exclusions.')
            data = {'version': 1, 'hosts': hosts, 'managed_hosts': managed}
            write_config(self.path, data)
            return self.apply_locked(data)

    def apply_locked(self, data: dict) -> dict:
        deadline = time.monotonic() + 45
        try:
            self.reconcile(data, deadline)
        except ConfigError as exc:
            # Desired state and removal history stay durable for an explicit retry.
            return {'hosts': data['hosts'], 'revision': revision(data), 'active_hosts': None,
                    'applied': False, 'error': str(exc)}
        data = {**data, 'managed_hosts': data['hosts']}
        write_config(self.path, data)
        return self.view(data, deadline)

    def startup(self) -> None:
        # No configured exclusions need no writes, including on read-only roots.
        # Keep broken symlinks visible to read_state's no-follow validation.
        if (not self.path.exists() and not self.path.is_symlink()
                and not os.environ.get('WARP_EXCLUDE_HOSTS', '').strip()):
            return
        with locked(self.path):
            data = read_state(self.path)
            if not self.path.exists() and not data['hosts']:
                return
            result = self.apply_locked(data)
            if not result['applied']:
                raise ConfigError(result['error'])


if __name__ == '__main__':
    try:
        WarpExclusions(exclusions_path()).startup()
    except (ConfigError, OSError) as exc:
        print(str(exc) if isinstance(exc, ConfigError) else 'Cannot persist WARP exclusions.', file=sys.stderr)
        sys.exit(1)
