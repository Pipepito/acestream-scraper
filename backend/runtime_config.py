"""Versioned runtime configuration. Stdlib-only so Docker can load it before services.

Only the reviewed data options in runtime-options.json can enter this file. In
particular it cannot select commands, executables, credentials or mount paths.
"""
from __future__ import annotations

import fcntl
import hashlib
import ipaddress
import json
import math
import os
import re
from pathlib import Path
import stat
import sys
import tempfile
from contextlib import contextmanager
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

OPTIONS = json.loads((Path(__file__).parent / 'app/config/runtime-options.json').read_text())
OPTION_MAP = {option['name']: option for option in OPTIONS}
ALIASES = {'ACESTREAM_ENGINE_URL': 'ACE_ENGINE_URL', 'ZERONET_BASE_URL': 'ZERONET_URL',
           'CORS_ALLOW_ORIGINS': 'CORS_ORIGINS'}
MAX_BYTES = 128 * 1024
_APPLIED: dict[str, dict] = {}


class ConfigError(ValueError):
    """A value-free error safe to show in setup or startup logs."""


class ConfigConflict(ConfigError):
    pass


def config_path(database_url: str | None = None) -> Path:
    url = database_url or os.environ.get('DATABASE_URL') or os.environ.get('SCRAPER_DB_URL') or 'sqlite:///./config/scraper.db'
    # SQLite paths follow the existing application contract; no URI query modes.
    if not url.startswith('sqlite:///') or url == 'sqlite:///:memory:' or '?' in url:
        raise ConfigError('Runtime configuration requires a file-backed SQLite database.')
    return Path(url[len('sqlite:///'):]).absolute().parent / 'runtime-config.json'


def validate_values(values: dict, *, bootstrap: bool = False) -> dict:
    if not isinstance(values, dict) or set(values) - OPTION_MAP.keys():
        raise ConfigError('Unknown runtime option. Commands, secrets and deployment paths belong in the environment.')
    result = {}
    for name, value in values.items():
        option = OPTION_MAP[name]
        kind = option['kind']
        try:
            if name == 'CORS_ORIGINS':
                if bootstrap and isinstance(value, list): value = ','.join(value)
                if isinstance(value, str) and value.lstrip().startswith('['): value = ','.join(json.loads(value))
            if bootstrap and isinstance(value, str):
                if kind == 'boolean':
                    if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
                        raise ValueError
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif kind == 'integer': value = int(value)
                elif kind == 'number': value = float(value)
            if kind == 'boolean':
                if type(value) is not bool: raise ValueError
            elif kind in ('integer', 'number'):
                if type(value) not in (int, float) or not math.isfinite(value): raise ValueError
                if kind == 'integer' and type(value) is not int: raise ValueError
                if 'minimum' in option and value < option['minimum']: raise ValueError
                if 'maximum' in option and value > option['maximum']: raise ValueError
            else:
                if not isinstance(value, str) or len(value) > 4096 or any(ord(c) < 32 for c in value): raise ValueError
                if kind == 'url' and value:
                    parsed = urlsplit(value)
                    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.fragment: raise ValueError
                    _ = parsed.port
                if kind == 'networks':
                    if not value.strip(): raise ValueError
                    for item in value.split(','):
                        if item.strip() != '*':
                            if name == 'FORWARDED_ALLOW_IPS' and re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_.-]*', item.strip()): continue
                            ipaddress.ip_network(item.strip(), strict=False)
                if name == 'CORS_ORIGINS':
                    for origin in filter(None, map(str.strip, value.split(','))):
                        if origin != '*' and (urlsplit(origin).scheme not in ('http', 'https') or not urlsplit(origin).hostname): raise ValueError
                if kind == 'host' and not valid_host(value): raise ValueError
                if kind == 'hosts' and any(not valid_host(host, port=True) for host in value.split()): raise ValueError
                if kind == 'ipv4': ipaddress.IPv4Address(value)
                if kind == 'listen':
                    host, port = value.rsplit(':', 1)
                    if (host and not valid_host(host)) or not port.isdigit() or not 1 <= int(port) <= 65535: raise ValueError
                if kind == 'duration' and not re.fullmatch(r'(?:[0-9]+(?:\.[0-9]+)?(?:ms|s|m|h))+', value): raise ValueError
                if kind == 'bytes' and not re.fullmatch(r'[1-9][0-9]*(?:B|KiB|MiB|GiB|KB|MB|GB)', value): raise ValueError
                if kind == 'timezone':
                    try: ZoneInfo(value)
                    except (ZoneInfoNotFoundError, ValueError): raise ValueError from None
            result[name] = value
        except (ValueError, TypeError, KeyError):
            raise ConfigError(f'Invalid value for {name}.') from None
    return result


def valid_host(value: str, *, port: bool = False) -> bool:
    """Data-only hosts; also safe in the legacy ZeroNet argument builder."""
    if not value or value.startswith('-'): return False
    host = value
    if port and ':' in value and not value.startswith('['):
        host, number = value.rsplit(':', 1)
        if not number.isdigit() or not 1 <= int(number) <= 65535: return False
    if host.startswith('[') and host.endswith(']'):
        try: ipaddress.IPv6Address(host[1:-1]); return True
        except ValueError: return False
    return bool(re.fullmatch(r'[a-zA-Z0-9_][a-zA-Z0-9_.-]*', host))


def defaults() -> dict:
    return {option['name']: option['default'] for option in OPTIONS}


def read_config(path: Path) -> dict | None:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    except OSError:
        raise ConfigError('Cannot read runtime configuration; check file permissions and type.') from None
    try:
        with os.fdopen(fd, 'r') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                raise ConfigError('Runtime configuration must be a bounded regular file.')
            data = json.loads(stream.read(MAX_BYTES + 1))
        if (not isinstance(data, dict) or set(data) != {'version', 'setup_complete', 'runtime'}
                or type(data['version']) is not int or data['version'] != 1 or type(data['setup_complete']) is not bool):
            raise ConfigError('Unsupported runtime configuration format; preserve the file and restore version 1.')
        data['runtime'] = validate_values(data['runtime'])
        return data
    except (json.JSONDecodeError, UnicodeError):
        raise ConfigError('Runtime configuration is not valid UTF-8 JSON; the file was not changed.') from None


def revision(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


@contextmanager
def locked(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path) + '.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def write_config(path: Path, data: dict):
    if path.is_symlink(): raise ConfigError('Runtime configuration must not be a symbolic link.')
    fd, temporary = tempfile.mkstemp(prefix='.runtime-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, indent=2, allow_nan=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def bootstrap_values(environment: dict, saved: dict | None = None) -> dict:
    saved = saved or {}
    # Never parse a superseded environment value (even if it is now invalid).
    selected = {key: value for key, value in environment.items() if key in OPTION_MAP and key not in saved}
    for old, new in ALIASES.items():
        if new not in saved and environment.get(old) and not selected.get(new): selected[new] = environment[old]
    values = {**defaults(), **validate_values(selected, bootstrap=True), **saved}
    for name, port in [('IPFS_GATEWAY_URL', 'IPFS_GATEWAY_PORT'), ('ZERONET_URL', 'ZERONET_UI_PORT')]:
        if name not in saved and name not in selected:
            values[name] = f'http://127.0.0.1:{values[port]}'
    if 'ACEXY_LISTEN_ADDR' not in saved and 'ACEXY_LISTEN_ADDR' not in selected:
        values['ACEXY_LISTEN_ADDR'] = ':' + str(environment.get('ACEXY_STATUS_PORT') or 8080)
    if values['ENABLE_ACESTREAM_ENGINE']:
        for name, source in [('ACEXY_HOST', 'ACESTREAM_HTTP_HOST'), ('ACEXY_PORT', 'ACESTREAM_HTTP_PORT')]:
            if name not in saved and name not in selected: values[name] = values[source]
    return validate_values(values)


def resolved_values(values: dict) -> dict:
    """Resolve automatic endpoints without storing a managed checker as external."""
    result = {**defaults(), **values}
    if result['ENABLE_ACESTREAM_ENGINE'] and not result['ACE_ENGINE_URL']:
        result['ACE_ENGINE_URL'] = f"http://{result['ACESTREAM_HTTP_HOST']}:{result['ACESTREAM_HTTP_PORT']}"
    if result['ENABLE_ACESTREAM_CHECK_ENGINE']:
        result['ACE_CHECK_ENGINE_URL'] = 'http://127.0.0.1:6880'
    return result


def ensure_config(path: Path, environment: dict) -> dict:
    with locked(path):
        data = read_config(path)
        if data is None:
            data = {'version': 1, 'setup_complete': False, 'runtime': bootstrap_values(environment)}
            write_config(path, data)
        else:
            values = bootstrap_values(environment, data['runtime'])
            if values != data['runtime']:
                data = {**data, 'runtime': values}
                write_config(path, data)
        _APPLIED.setdefault(str(path), dict(data['runtime']))
        return data


def remember_applied(path: Path, values: dict):
    _APPLIED.setdefault(str(path), dict(values))


def restart_required(path: Path, data: dict) -> bool:
    return data['runtime'] != _APPLIED.get(str(path), data['runtime'])


def update_config(path: Path, values: dict, expected: str, complete: bool) -> dict:
    values = validate_values(values)
    with locked(path):
        current = read_config(path)
        if current is None or revision(current) != expected:
            raise ConfigConflict('Configuration changed in another session. Reload before saving.')
        data = {'version': 1, 'setup_complete': complete, 'runtime': {**current['runtime'], **values}}
        validate_combination(data['runtime'])
        write_config(path, data)
        return data


def validate_combination(values: dict):
    if values.get('ENABLE_ACESTREAM_CHECK_ENGINE'):
        if not values.get('ENABLE_ACESTREAM_ENGINE') or values.get('ACE_CHECK_ENGINE_URL'):
            raise ConfigError('Bundled checks require the bundled playback engine and an empty external checker address.')
        if values.get('ACESTREAM_HTTP_PORT', 6878) == 6880:
            raise ConfigError('Playback HTTP port conflicts with the bundled checking engine.')
    if values.get('ENABLE_ACEXY') and not values.get('ENABLE_ACESTREAM_ENGINE'):
        if values.get('ACEXY_HOST', 'localhost') in ('localhost', '127.0.0.1', '[::1]') and values.get('ACEXY_PORT', 6878) == values.get('ACESTREAM_HTTP_PORT', 6878):
            raise ConfigError('Acexy needs the bundled playback engine or an external upstream host.')
    if values.get('ENABLE_TOR') and not values.get('ENABLE_ZERONET'):
        raise ConfigError('Tor requires the bundled ZeroNet service.')
    if values.get('WARP_ENABLE_NAT') and not values.get('ENABLE_WARP'):
        raise ConfigError('WARP auto-connect requires WARP to be enabled.')


def environment_for(data: dict, environment: dict) -> dict:
    result = {key: value for key, value in environment.items() if key not in OPTION_MAP and key not in ALIASES}
    for key, value in bootstrap_values(environment, data['runtime']).items():
        result[key] = str(value).lower() if type(value) is bool else str(value)
    return result


def active_value(name: str, default: str = '') -> str:
    """Use the boot snapshot, with environment compatibility before first boot."""
    try:
        from app.config.settings import get_settings
        values = _APPLIED.get(str(config_path(get_settings().DATABASE_URL)))
    except ConfigError:
        values = None
    value = values.get(name, default) if values is not None else os.environ.get(name, default)
    return str(value).lower() if type(value) is bool else str(value)


def main():
    # No shell serialization or eval. Values are passed as an exec environment.
    mode, *command = sys.argv[1:]
    if mode not in ('run', 'health') or not command: raise ConfigError('Expected run|health followed by a command.')
    path = config_path()
    snapshot = Path(os.environ.get('SUPERVISOR_RUN_DIR', '/run/acestream-scraper')) / 'runtime-applied.json'
    if mode == 'health':
        data = read_config(snapshot)
        if data is None:
            data = read_config(Path(tempfile.gettempdir()) / 'acestream-scraper-run/runtime-applied.json')
        if data is None: raise ConfigError('Runtime configuration has not been initialized.')
    else:
        data = ensure_config(path, dict(os.environ))
        try:
            snapshot.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            snapshot = Path(tempfile.gettempdir()) / 'acestream-scraper-run/runtime-applied.json'
            snapshot.parent.mkdir(parents=True, exist_ok=True)
        os.environ['SUPERVISOR_RUN_DIR'] = str(snapshot.parent)
        write_config(snapshot, data)
    environment = environment_for(data, dict(os.environ))
    environment['SCRAPER_LEGACY_ENV_NAMES'] = ','.join(key for key in ALIASES if os.environ.get(key))
    environment['SCRAPER_RUNTIME_LOADED'] = '1'
    os.execvpe(command[0], command, environment)


if __name__ == '__main__':
    try:
        main()
    except (ConfigError, OSError):
        print('Runtime configuration could not be loaded. Check runtime-config.json, its version, values and permissions. No services were started.', file=sys.stderr)
        sys.exit(1)
