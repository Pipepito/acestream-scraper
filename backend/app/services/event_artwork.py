"""Small raster artwork through the same pinned outbound boundary as sources."""
import asyncio
import threading
import aiohttp
from app.utils.outbound_http import source_session

_SLOTS = threading.BoundedSemaphore(2)


def raster_type(data):
    width = height = 0
    kind = ''
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 24 and data[12:16] == b'IHDR':
        width, height = int.from_bytes(data[16:20], 'big'), int.from_bytes(data[20:24], 'big')
        kind = 'image/png'
    elif data.startswith(b'\xff\xd8'):
        offset = 2
        while offset + 4 <= len(data):
            if data[offset] != 255:
                break
            while offset < len(data) and data[offset] == 255:
                offset += 1
            if offset + 3 > len(data):
                break
            marker = data[offset]
            size = int.from_bytes(data[offset + 1:offset + 3], 'big')
            if size < 2 or offset + 1 + size > len(data):
                break
            if marker in (0xc0, 0xc1, 0xc2) and size >= 8:
                height = int.from_bytes(data[offset + 4:offset + 6], 'big')
                width = int.from_bytes(data[offset + 6:offset + 8], 'big')
                kind = 'image/jpeg'
                break
            offset += 1 + size
    elif len(data) >= 30 and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        if data[12:16] == b'VP8X' and not data[20] & 2:  # no animation
            width = 1 + int.from_bytes(data[24:27], 'little')
            height = 1 + int.from_bytes(data[27:30], 'little')
        elif data[12:16] == b'VP8 ' and data[23:26] == b'\x9d\x01\x2a':
            width = int.from_bytes(data[26:28], 'little') & 0x3fff
            height = int.from_bytes(data[28:30], 'little') & 0x3fff
        elif data[12:16] == b'VP8L' and data[20] == 0x2f:
            bits = int.from_bytes(data[21:25], 'little')
            width, height = (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
        kind = 'image/webp'
    if not kind or not 0 < width <= 4096 or not 0 < height <= 4096 or width * height > 4_000_000:
        raise ValueError('Artwork must be a small PNG, JPEG or static WebP image')
    return kind


async def _fetch(url):
    async with source_session(timeout=aiohttp.ClientTimeout(total=10)) as session:
        async with session.get(url, max_redirects=5) as response:
            response.raise_for_status()
            data = bytearray()
            async for chunk in response.content.iter_chunked(32768):
                data.extend(chunk)
                if len(data) > 512 * 1024:
                    raise ValueError('Artwork is too large')
    data = bytes(data)
    return data, raster_type(data)


def fetch_artwork(url):
    if not _SLOTS.acquire(blocking=False):
        raise ValueError('Artwork requests are busy; try again shortly')
    try:
        return asyncio.run(_fetch(url))
    except Exception:
        raise ValueError('Artwork could not be loaded as a small raster image') from None
    finally:
        _SLOTS.release()
