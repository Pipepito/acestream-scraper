"""Source HTTP clients that validate redirects and connect only to checked IPs."""
import asyncio
import socket
from urllib.parse import urljoin, urlsplit

import aiohttp
import requests
from requests.adapters import HTTPAdapter

from app.utils import url_guard


class PinnedResolver(aiohttp.abc.AbstractResolver):
    async def resolve(self, host, port=0, family=socket.AF_INET):
        addresses = await asyncio.to_thread(url_guard._resolve_addresses, host)
        url_guard.validate_resolved_addresses(host, addresses)
        return [{'hostname': host, 'host': str(address), 'port': port,
                 'family': socket.AF_INET6 if address.version == 6 else socket.AF_INET,
                 'proto': socket.IPPROTO_TCP, 'flags': socket.AI_NUMERICHOST}
                for address in addresses]

    async def close(self):
        pass


def source_session(*, ssl=True, **kwargs):
    """Keep original URL/Host/TLS identity while pinning connection addresses."""
    trace = aiohttp.TraceConfig()

    async def start(session, context, params):
        # Also checks literal IPs, which aiohttp does not pass to its resolver.
        await asyncio.to_thread(url_guard.validate_outbound_url, str(params.url))

    async def redirect(session, context, params):
        location = params.response.headers.get('Location') or params.response.headers.get('URI')
        if location:
            await asyncio.to_thread(url_guard.validate_outbound_url, urljoin(str(params.url), location))

    trace.on_request_start.append(start)
    trace.on_request_redirect.append(redirect)
    return aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(resolver=PinnedResolver(), use_dns_cache=False, ssl=ssl),
        trace_configs=[trace], trust_env=False, **kwargs,
    )


class PinnedHTTPAdapter(HTTPAdapter):
    def _connection(self, url, pool_kwargs=None):
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            raise url_guard.BlockedURLError('Only HTTP(S) source URLs are supported')
        addresses = url_guard._resolve_addresses(parsed.hostname)
        url_guard.validate_resolved_addresses(parsed.hostname, addresses)
        options = dict(pool_kwargs or {})
        if parsed.scheme == 'https':
            options.update(server_hostname=parsed.hostname, assert_hostname=parsed.hostname)
        return self.poolmanager.connection_from_host(
            str(addresses[0]), port=parsed.port, scheme=parsed.scheme, pool_kwargs=options,
        )

    def get_connection_with_tls_context(self, request, verify, proxies=None, cert=None):
        _, options = self.build_connection_pool_key_attributes(request, verify, cert)
        return self._connection(request.url, options)

    def get_connection(self, url, proxies=None):
        # requests 2.31 uses this hook; newer releases use the TLS-context hook.
        return self._connection(url)

    def add_headers(self, request, **kwargs):
        request.headers['Host'] = urlsplit(request.url).netloc.rsplit('@', 1)[-1]


def source_get(url, *, timeout=60, allow_redirects=False):
    """Fetch one hop synchronously. Callers must validate/follow redirects."""
    if allow_redirects:
        raise ValueError('Source redirects must be handled explicitly')
    with requests.Session() as session:
        session.trust_env = False
        session.mount('http://', PinnedHTTPAdapter())
        session.mount('https://', PinnedHTTPAdapter())
        # Content is materialized before the session is closed (stream=False).
        return session.get(url, timeout=timeout, allow_redirects=False)
