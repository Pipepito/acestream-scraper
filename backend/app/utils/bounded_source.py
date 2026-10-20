"""Bounded, cancellable reads through the existing DNS-pinned source client."""
from dataclasses import dataclass

import aiohttp

from app.utils.outbound_http import source_session


@dataclass
class SourceResponse:
    status_code: int
    content: bytes
    headers: dict
    truncated: bool = False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise ValueError(f'HTTP {self.status_code}')


async def source_get(url, *, headers=None, timeout=10, max_bytes=4 * 1024 * 1024,
                     sample=False, media_limit=None):
    """Read one guarded hop. Sampling stops at the cap; documents reject overflow.

    Range is an optimization only: origins may ignore it. ClientTimeout covers
    the complete request, including a slow trickle. Cancellation closes both the
    response and session; callers share a separate budget across redirects.
    """
    if timeout <= 0:
        raise TimeoutError('Source read deadline exceeded')
    async with source_session() as session:
        async with session.get(url, headers=headers, allow_redirects=False,
                               timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status >= 300:
                return SourceResponse(response.status, b'', response.headers.copy())
            body = bytearray()
            async for chunk in response.content.iter_chunked(16 * 1024):
                if media_limit is not None and len(body) + len(chunk) >= 512:
                    prefix = (body + chunk)[:512]
                    if b'#EXTM3U' not in prefix:
                        max_bytes, sample = min(max_bytes, media_limit), True
                    media_limit = None
                remaining = max_bytes - len(body)
                body.extend(chunk[:remaining])
                if len(chunk) > remaining or (sample and len(body) == max_bytes):
                    if not sample:
                        raise ValueError('Source response exceeds byte limit')
                    return SourceResponse(response.status, bytes(body), response.headers.copy(), True)
            return SourceResponse(response.status, bytes(body), response.headers.copy())


async def source_request(url, *, method='GET', headers=None, payload=None, timeout=10,
                         max_bytes=2 * 1024 * 1024, cancelled=None):
    """Bound provider JSON/text, including cancellation from its resolving thread."""
    import asyncio

    async def read():
        async with source_session() as session:
            async with session.request(method, url, headers=headers, json=payload,
                                       allow_redirects=False, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                if response.status >= 300:
                    return SourceResponse(response.status, b'', response.headers.copy())
                body = bytearray()
                async for chunk in response.content.iter_chunked(16 * 1024):
                    if len(body) + len(chunk) > max_bytes:
                        raise ValueError('Provider response exceeds byte limit')
                    body.extend(chunk)
                return SourceResponse(response.status, bytes(body), response.headers.copy())

    task = asyncio.create_task(read())
    try:
        while not task.done():
            if cancelled is not None and cancelled.is_set():
                raise TimeoutError('Provider resolution cancelled')
            await asyncio.wait({task}, timeout=0.05)
        return await task
    finally:
        if not task.done():
            task.cancel()
        await asyncio.gather(task, return_exceptions=True)
