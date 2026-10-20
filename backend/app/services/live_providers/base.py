"""Shared pieces of the live providers: one HTTP client, swappable in tests.

Every provider talks only to the fixed hosts written in its own module --
never to a URL a user typed -- so this is a plain requests session that
ignores environment proxies, not the pinned source getter. That one guards
user-supplied URLs and cannot send headers or a POST body, which Mediaset's
anonymous login needs.
"""
import logging
from typing import Any, Dict, Optional

import requests

log = logging.getLogger(__name__)

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
TIMEOUT = 20


class Http:
    def _send(self, method: str, url: str, headers: Optional[Dict[str, str]], body: Any) -> requests.Response:
        with requests.Session() as session:
            session.trust_env = False
            response = session.request(method, url, headers=headers or {}, json=body,
                                       timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            return response

    def get_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        return self._send('GET', url, headers, None).json()

    def post_json(self, url: str, body: Any, headers: Optional[Dict[str, str]] = None) -> Any:
        return self._send('POST', url, headers, body).json()

    def get_text(self, url: str, headers: Optional[Dict[str, str]] = None) -> str:
        return self._send('GET', url, headers, None).text


# Tests replace this with a fake; nothing in the package imports requests
# directly, so a test can never reach the network by accident.
http = Http()
