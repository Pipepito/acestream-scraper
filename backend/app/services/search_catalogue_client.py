"""Bounded catalogue reads. Never starts media, follows redirects or uses proxies."""
import asyncio
import hashlib
import json
import re
import threading
import time
import httpx

PAGE_SIZE = 100
MAX_PAGES = 10
MAX_CANDIDATES = 1000
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_STORAGE_BYTES = 8 * 1024 * 1024
RUN_SECONDS = 120
REQUEST_SECONDS = 10
ENGINE_SLOTS = threading.BoundedSemaphore(2)
HEX_ID = re.compile(r'^[a-fA-F0-9]{40}$')


class CatalogueReadError(Exception):
    def __init__(self, code='SEARCH_ENGINE_UNAVAILABLE'):
        self.code = code
        super().__init__(code)


def flatten_results(payload, limit=MAX_CANDIDATES):
    """Validate grouped/flat results before allocating a bounded candidate list."""
    if not isinstance(payload, dict) or not isinstance(payload.get('result'), dict):
        raise CatalogueReadError()
    result = payload['result']
    rows, total = result.get('results'), result.get('total')
    if not isinstance(rows, list) or not isinstance(total, int) or isinstance(total, bool) or total < 0:
        raise CatalogueReadError()
    items, invalid, capped = [], 0, False
    storage_bytes = 0
    for row in rows:
        if not isinstance(row, dict):
            invalid += 1
            continue
        children = row.get('items', [row])
        if not isinstance(children, list):
            invalid += 1
            continue
        for item in children:
            if len(items) >= limit:
                capped = True
                break
            if not isinstance(item, dict):
                invalid += 1
                continue
            ih = item.get('infohash', item.get('id'))
            name = row.get('name', item.get('name', 'Unnamed Channel'))
            if isinstance(name, (int, float)) and not isinstance(name, bool):
                name = str(name)
            if not isinstance(ih, str) or not HEX_ID.fullmatch(ih) or not isinstance(name, str) or not name.strip():
                invalid += 1
                continue
            categories = item.get('categories', [])
            categories = [c[:100] for c in categories[:20] if isinstance(c, str)] if isinstance(categories, list) else []
            candidate = dict(infohash=ih.lower(), name=name[:512], category=next(iter(categories), ''), categories=categories)
            for key in ('bitrate', 'status', 'availability_updated_at'):
                value = item.get(key)
                if isinstance(value, int) and not isinstance(value, bool):
                    candidate[key] = value
            value = item.get('availability')
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                import math
                if math.isfinite(value):
                    candidate['availability'] = value
            size = len(json.dumps(candidate).encode()) + 128  # reserve resolution metadata
            if storage_bytes + size > MAX_STORAGE_BYTES:
                capped = True
                break
            storage_bytes += size
            items.append(candidate)
        if capped:
            break
    return items, total, invalid, capped


class SearchCatalogueClient:
    def __init__(self, engine_url, *, deadline=None, shutdown=None, transport=None):
        if not (engine_url or '').strip():
            raise CatalogueReadError('SEARCH_ENGINE_UNCONFIGURED')
        engine_url = engine_url.strip()
        if '://' not in engine_url:
            engine_url = 'http://' + engine_url
        self.url = engine_url.rstrip('/')
        self.deadline = deadline or time.monotonic() + RUN_SECONDS
        self.shutdown = shutdown
        self.transport = transport

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def remaining(self):
        if self.shutdown is not None and self.shutdown.is_set():
            raise CatalogueReadError('shutdown')
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise CatalogueReadError('deadline')
        return remaining

    def get(self, path, params):
        acquired = False
        try:
            while not acquired:
                acquired = ENGINE_SLOTS.acquire(timeout=min(.25, self.remaining()))
            async def read():
                # A whole-request timeout cancels socket IO, including slow
                # trickle responses. The slot is held until context cleanup ends.
                async with asyncio.timeout(min(REQUEST_SECONDS, self.remaining())):
                    async with httpx.AsyncClient(trust_env=False, follow_redirects=False,
                                                transport=self.transport) as client:
                        async with client.stream('GET', self.url + path, params=params,
                                                 timeout=min(REQUEST_SECONDS, self.remaining())) as response:
                            response.raise_for_status()
                            body = bytearray()
                            async for chunk in response.aiter_bytes():
                                self.remaining()
                                if len(body) + len(chunk) > MAX_RESPONSE_BYTES:
                                    raise CatalogueReadError('response_limit')
                                body.extend(chunk)
                        self.remaining()
                        return json.loads(body)
            return asyncio.run(read())
        except TimeoutError:
            raise CatalogueReadError('deadline') from None
        except (httpx.HTTPError, ValueError):
            raise CatalogueReadError() from None
        finally:
            if acquired:
                ENGINE_SLOTS.release()

    def resolve(self, infohash):
        payload = self.get('/server/api', {'api_version': 3, 'method': 'get_content_id', 'infohash': infohash})
        result = payload.get('result') if isinstance(payload, dict) and not payload.get('error') else None
        cid = result.get('content_id') if isinstance(result, dict) else None
        if not isinstance(cid, str) or not HEX_ID.fullmatch(cid):
            raise CatalogueReadError('unresolved')
        return cid.lower()

    def collect(self, query, category):
        candidates, seen, pages, invalid, duplicates = [], set(), 0, 0, 0
        fingerprints = set()
        storage_bytes = 0
        reason = None
        try:
            for page in range(MAX_PAGES):
                payload = self.get('/search', dict(query=query, category=category, page=page, page_size=PAGE_SIZE))
                items, total, bad, capped = flatten_results(payload, MAX_CANDIDATES - len(candidates))
                pages += 1
                invalid += bad
                fingerprint = hashlib.sha256(json.dumps(items, sort_keys=True).encode()).hexdigest()
                if fingerprint in fingerprints and items:
                    reason = 'repeated_page'
                    break
                fingerprints.add(fingerprint)
                before = len(candidates)
                for item in items:
                    if item['infohash'] in seen:
                        duplicates += 1
                    else:
                        size = len(json.dumps(item).encode()) + 128
                        if storage_bytes + size > MAX_STORAGE_BYTES:
                            capped = True
                            break
                        storage_bytes += size
                        seen.add(item['infohash'])
                        candidates.append(item)
                if capped or len(candidates) >= MAX_CANDIDATES:
                    reason = 'candidate_limit'
                    break
                if not items or (page + 1) * PAGE_SIZE >= total:
                    break
                if len(candidates) == before:
                    reason = 'no_progress'
                    break
            else:
                reason = 'page_limit'
        except CatalogueReadError as exc:
            reason = exc.code
        return candidates, dict(pages_fetched=pages, candidates_seen=len(candidates) + duplicates + invalid,
            unique_infohashes=len(candidates), unresolved_candidates=invalid, duplicates=duplicates,
            stop_reason=reason)
