"""Bounded sample fetching and isolated recipe evaluation, with no persistence."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from urllib.parse import urljoin, urlsplit
import aiohttp
from app.schemas.extraction import ExtractionRecipe, RecipePreview, MAX_SAMPLE_BYTES
from app.utils.url_guard import validate_outbound_url, BlockedURLError
from app.utils.outbound_http import source_session

_WORKERS = threading.BoundedSemaphore(2)
_FETCHES = threading.BoundedSemaphore(2)


def preview_recipe(recipe: ExtractionRecipe, sample: str) -> RecipePreview:
    if len(sample.encode('utf-8')) > MAX_SAMPLE_BYTES:
        raise ValueError('Sample exceeds 32 MiB')
    if not _WORKERS.acquire(blocking=False):
        raise ValueError('Two extraction tests are already running; try again shortly')
    try:
        root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, '-m', 'app.services.recipe_worker'],
            input=json.dumps({'recipe': recipe.model_dump(), 'sample': sample}, ensure_ascii=False),
            capture_output=True, text=True, timeout=15, cwd=root,
            env={'PATH': os.defpath, 'PYTHONPATH': str(root), 'PYTHONIOENCODING': 'utf-8'},
        )
        if result.returncode:
            raise ValueError('Extraction failed. Check rules and sample, or simplify an expensive pattern.')
        return RecipePreview.model_validate_json(result.stdout)
    except subprocess.TimeoutExpired:
        raise ValueError('Extraction exceeded its time limit; simplify the pattern') from None
    finally:
        _WORKERS.release()


async def fetch_recipe_sample(url: str, url_type: str = 'auto') -> str:
    from app.models.url_types import create_url_object, IpfsURL, ZeronetURL
    from app.config.settings import settings
    if not _FETCHES.acquire(blocking=False):
        raise ValueError('Two source checks are already running; try again shortly')
    try:
        url_object = create_url_object(url, url_type)
        current = url_object.get_normalized_url()
        if isinstance(url_object, IpfsURL):
            current = IpfsURL.to_gateway_url(url, settings.IPFS_GATEWAY_URL)
        elif isinstance(url_object, ZeronetURL):
            current = (settings.ZERONET_URL.rstrip('/') + '/' + current[7:]
                       if current.startswith('zero://') else url_object.get_internal_url())
        async with source_session(timeout=aiohttp.ClientTimeout(total=20)) as session:
            for _ in range(6):
                parts = urlsplit(current)
                if parts.username or parts.password:
                    raise ValueError('Source checks do not accept credentials in URLs')
                await asyncio.to_thread(validate_outbound_url, current)
                async with session.get(current, allow_redirects=False) as response:
                    if response.status in (301, 302, 303, 307, 308):
                        location = response.headers.get('Location')
                        if not location:
                            raise ValueError('Redirect has no destination')
                        current = urljoin(current, location)
                        continue
                    response.raise_for_status()
                    data = bytearray()
                    async for chunk in response.content.iter_chunked(16384):
                        data.extend(chunk)
                        if len(data) > MAX_SAMPLE_BYTES:
                            raise ValueError('Source exceeds 32 MiB; copy the channel section or use its data endpoint')
                    try:
                        return data.decode(response.charset or 'utf-8', errors='replace')
                    except LookupError:
                        return data.decode('utf-8', errors='replace')
            raise ValueError('Too many redirects')
    except (aiohttp.ClientError, asyncio.TimeoutError, BlockedURLError):
        raise ValueError('Could not fetch the source. Check its address, access rules and availability.') from None
    finally:
        _FETCHES.release()
