"""Shared pieces of the live providers: one HTTP client, swappable in tests.

Provider requests use the pinned source client, bounded response bodies and a
shared resolving deadline. The synchronous provider adapters remain swappable
in tests; their HTTP worker observes cancellation from the async caller.
"""
import logging
from typing import Any, Dict, Optional

import asyncio
from contextvars import ContextVar
import json
import time
from urllib.parse import urljoin, urlsplit

from app.utils.bounded_source import source_request

resolution_limits = ContextVar('provider_resolution_limits', default=None)

log = logging.getLogger(__name__)

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
TIMEOUT = 20


class Http:
    def _send(self, method: str, url: str, headers: Optional[Dict[str, str]], body: Any):
        limits = resolution_limits.get()
        deadline, cancelled = limits if limits else (time.monotonic() + TIMEOUT, None)
        headers = dict(headers or {})
        for _ in range(6):
            remaining = deadline - time.monotonic()
            if remaining <= 0 or (cancelled is not None and cancelled.is_set()):
                raise TimeoutError('Provider resolution deadline exceeded')
            response = asyncio.run(source_request(url, method=method, headers=headers,
                payload=body, timeout=remaining, cancelled=cancelled))
            if response.status_code in (301, 302, 303, 307, 308) and response.headers.get('Location'):
                destination = urljoin(url, response.headers['Location'])
                if urlsplit(destination)[:2] != urlsplit(url)[:2]:
                    headers = {key: value for key, value in headers.items()
                               if key.lower() not in ('authorization', 'cookie')}
                if response.status_code == 303 or (method == 'POST' and response.status_code in (301, 302)):
                    method, body = 'GET', None
                url = destination
                continue
            response.raise_for_status()
            return response
        raise ValueError('Too many provider redirects')

    def get_json(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        return json.loads(self._send('GET', url, headers, None).content)

    def post_json(self, url: str, body: Any, headers: Optional[Dict[str, str]] = None) -> Any:
        return json.loads(self._send('POST', url, headers, body).content)

    def get_text(self, url: str, headers: Optional[Dict[str, str]] = None) -> str:
        return self._send('GET', url, headers, None).content.decode('utf-8', 'replace')


# Tests replace this with a fake; nothing in the package imports requests
# directly, so a test can never reach the network by accident.
http = Http()
