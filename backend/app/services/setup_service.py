"""File-backed first-run setup; database preferences remain owned by their APIs."""
import os
from pathlib import Path
import shutil
import json
from urllib.parse import urlsplit, urlunsplit

from app.config.settings import get_settings
from app.schemas.setup import SetupState, SetupUpdate
from runtime_config import (OPTIONS, ConfigError, config_path, defaults, ensure_config,
                            restart_required, revision, update_config, resolved_values)


def unavailable_options() -> dict[str, str]:
    result = {}
    supervised = bool(os.environ.get('SUPERVISOR_RUN_DIR'))
    flags = {'ENABLE_ACESTREAM_ENGINE': 'IMAGE_HAS_ACESTREAM',
             'ENABLE_ACESTREAM_CHECK_ENGINE': 'IMAGE_HAS_ACESTREAM',
             'ENABLE_ACEXY': 'IMAGE_HAS_ACEXY', 'ENABLE_IPFS': 'IMAGE_HAS_IPFS',
             'ENABLE_ZERONET': 'IMAGE_HAS_ZERONET'}
    for option, flag in flags.items():
        if not supervised or os.environ.get(flag, '').lower() != 'true':
            result[option] = 'This installation does not include a supervised service. Choose a compatible Docker image or use an external endpoint.'
    for option, executable in [('ENABLE_WARP', 'warp-cli'), ('ENABLE_TOR', 'tor')]:
        if not supervised or not shutil.which(executable):
            result[option] = 'This installation does not include the supervised service.'
    if 'ENABLE_WARP' not in result and not Path('/dev/net/tun').exists():
        result['ENABLE_WARP'] = 'Recreate the container with /dev/net/tun, NET_ADMIN and SYS_ADMIN before enabling WARP.'
    return result


def visible_endpoint(value: str) -> str:
    """Do not echo credentials or query tokens from older saved preferences."""
    try:
        parsed = urlsplit(value)
        if not parsed.hostname: return ''
        host = parsed.hostname
        if ':' in host: host = f'[{host}]'
        if parsed.port: host += f':{parsed.port}'
        return urlunsplit((parsed.scheme, host, parsed.path, '', ''))
    except ValueError:
        return 'Invalid saved address; review Settings'


class SetupService:
    def __init__(self, repository=None):
        settings = get_settings()
        self.path = config_path(settings.DATABASE_URL)
        self.environment = {**os.environ, **settings.model_dump()}
        self.repository = repository

    def saved_overrides(self) -> dict[str, str]:
        raw = self.repository.get_setup_overrides() if self.repository else {}
        result = {}
        for key, name in [('ace_engine_url', 'ACE_ENGINE_URL'), ('public_base_url', 'PUBLIC_BASE_URL')]:
            if key in raw and (raw[key] or key == 'ace_engine_url'):
                result[name] = visible_endpoint(raw[key] or '')
        for key, name, flag, url in [('check_engine_config', 'ACE_CHECK_ENGINE_URL', 'use_dedicated', 'url'),
                                      ('playback_routing', 'ACEXY_URL', 'use_acexy', 'acexy_url')]:
            if raw.get(key):
                try:
                    value = json.loads(raw[key])
                    result[name] = visible_endpoint(value.get(url, '')) if value.get(flag) else ''
                except (ValueError, AttributeError, TypeError):
                    result[name] = 'Invalid saved preference; review Settings'
        return result

    def state(self) -> SetupState:
        data = ensure_config(self.path, self.environment)
        return SetupState(
            setup_complete=data['setup_complete'], revision=revision(data), runtime={**defaults(), **data['runtime']},
            options=OPTIONS, unavailable=unavailable_options(),
            restart_required=restart_required(self.path, data), api_protected=bool(os.environ.get('API_TOKEN', '').strip()),
            resolved_runtime=resolved_values(data['runtime']), saved_overrides=self.saved_overrides(),
            recordings_configured=bool(get_settings().RECORDINGS_DIR),
        )

    def save(self, request: SetupUpdate) -> SetupState:
        current = self.state()
        for name, reason in current.unavailable.items():
            if request.runtime.get(name) and not current.runtime.get(name):
                raise ConfigError(reason)
        desired = {**current.runtime, **request.runtime}
        if os.environ.get('ACESTREAM_GLUETUN_PORT_FILE') and not desired.get('ENABLE_ACESTREAM_ENGINE'):
            raise ConfigError('Remove Gluetun port synchronization from the deployment before disabling the bundled engine.')
        update_config(self.path, request.runtime, request.expected_revision, request.setup_complete)
        return self.state()
