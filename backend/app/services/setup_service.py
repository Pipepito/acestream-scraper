"""File-backed first-run setup; database preferences remain owned by their APIs."""
import os
from pathlib import Path
import shutil

from app.config.settings import get_settings
from app.schemas.setup import SetupState, SetupUpdate
from runtime_config import (OPTIONS, ConfigError, config_path, ensure_config,
                            restart_required, revision, update_config)


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


class SetupService:
    def __init__(self):
        settings = get_settings()
        self.path = config_path(settings.DATABASE_URL)
        self.environment = {**os.environ, **settings.model_dump()}
        self.existing_database = Path(settings.DATABASE_URL[len('sqlite:///'):]).exists()

    def state(self) -> SetupState:
        data = ensure_config(self.path, self.environment, existing_database=self.existing_database)
        return SetupState(
            setup_complete=data['setup_complete'], revision=revision(data), runtime=data['runtime'],
            options=OPTIONS, unavailable=unavailable_options(),
            restart_required=restart_required(self.path, data), api_protected=bool(os.environ.get('API_TOKEN', '').strip()),
        )

    def save(self, request: SetupUpdate) -> SetupState:
        current = self.state()
        for name, reason in current.unavailable.items():
            if request.runtime.get(name) and not current.runtime.get(name):
                raise ConfigError(reason)
        desired = {**current.runtime, **request.runtime}
        if desired.get('ENABLE_ACEXY') and not desired.get('ENABLE_ACESTREAM_ENGINE'):
            host, port = os.environ.get('ACEXY_HOST', 'localhost'), os.environ.get('ACEXY_PORT', '6878')
            if host in ('localhost', '127.0.0.1') and port == '6878':
                raise ConfigError('Acexy needs the bundled playback engine or an external ACEXY_HOST/ACEXY_PORT in your deployment.')
        if desired.get('ENABLE_ACESTREAM_CHECK_ENGINE') and os.environ.get('ACESTREAM_HTTP_PORT') == '6880':
            raise ConfigError('Playback HTTP port conflicts with the bundled checking engine. Change the deployment port first.')
        if os.environ.get('ACESTREAM_GLUETUN_PORT_FILE') and not desired.get('ENABLE_ACESTREAM_ENGINE'):
            raise ConfigError('Remove Gluetun port synchronization from the deployment before disabling the bundled engine.')
        update_config(self.path, request.runtime, request.expected_revision, request.setup_complete)
        return self.state()
