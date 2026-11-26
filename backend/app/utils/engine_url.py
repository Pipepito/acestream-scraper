"""The one spelling of a configured AceStream engine address, and its routes."""
from urllib.parse import urlencode

# Engine HTTP API routes, appended to ``engine_base_url``.
ENGINE_START_PATH = '/ace/getstream'
ENGINE_API_PATH = '/server/api'
ENGINE_STATUS_PARAMS = {'api_version': '3', 'method': 'get_status'}
ENGINE_STATUS_QUERY = urlencode(ENGINE_STATUS_PARAMS)
ENGINE_NETWORK_STATUS_QUERY = urlencode({'api_version': '3', 'method': 'get_network_connection_status'})
ENGINE_VERSION_PATH = '/webui/api/service?method=get_version'


def engine_base_url(value: object) -> str:
    """``host:port`` or a full http(s) URL -> ``http(s)://host:port`` without a trailing slash.

    Empty or missing configuration stays ``''`` so each caller keeps its own
    answer to "no engine configured" (raise, 503, skip).
    """
    url = str(value or '').strip()
    if not url:
        return ''
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'
    return url.rstrip('/')
