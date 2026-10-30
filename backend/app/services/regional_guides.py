"""Opt-in HTML guides: bounded transport over the same pinned source client."""
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import aiohttp

from app.services import sincroguia_guide, tvrioja_guide
from app.utils.outbound_http import source_session


def supports(url):
    return tvrioja_guide.is_tvrioja_url(url) or sincroguia_guide.is_sincroguia_url(url)


async def _fetch(url):
    today = datetime.now(ZoneInfo('Europe/Madrid')).date()
    rioja = tvrioja_guide.is_tvrioja_url(url)
    pages = tvrioja_guide.page_urls(url) if rioja else [url]
    documents = []
    async with asyncio.timeout(90):
        async with source_session(timeout=aiohttp.ClientTimeout(total=30)) as session:
            for page in pages:
                async with session.get(page, allow_redirects=False) as response:
                    if response.status != 200:
                        raise ValueError('Regional guide page unavailable; previous guide retained')
                    data = bytearray()
                    async for chunk in response.content.iter_chunked(65536):
                        data.extend(chunk)
                        if len(data) > 2 * 1024 * 1024:
                            raise ValueError('Regional guide page exceeds 2 MiB')
                converter = tvrioja_guide.html_to_xmltv if rioja else sincroguia_guide.html_to_xmltv
                documents.append(await asyncio.to_thread(converter, bytes(data), page, today))
    return tvrioja_guide.merge_xmltv(documents) if rioja else documents[0]


async def fetch(url):
    try:
        return await _fetch(url)
    except Exception:
        raise ValueError('Regional guide unavailable or invalid. Check the channel page, dates and local times; limits are 2 MiB per page and 90 seconds per refresh. Previous guide retained.') from None
