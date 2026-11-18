"""The one spelling of a configured AceStream engine address."""


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
