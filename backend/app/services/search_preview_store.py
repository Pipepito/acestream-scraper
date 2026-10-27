"""Installation-local, bounded private snapshots; no client-supplied resolved IDs."""
import copy
import json
import secrets
import threading
import time
from collections import OrderedDict
from app.api.error_handlers import APIError
from app.services.search_catalogue_client import MAX_STORAGE_BYTES

_LOCK = threading.Lock()
_CACHE = OrderedDict()
TTL = 300


def remember(value):
    size = len(json.dumps(value).encode())
    if size > MAX_STORAGE_BYTES:
        raise APIError('SEARCH_LIMIT_REACHED', 'Preview exceeds its storage budget.', 413)
    token = secrets.token_urlsafe(32)
    with _LOCK:
        for key, (expiry, _, _) in list(_CACHE.items()):
            if expiry < time.monotonic():
                del _CACHE[key]
        while _CACHE and (len(_CACHE) >= 8 or sum(v[1] for v in _CACHE.values()) + size > MAX_STORAGE_BYTES):
            _CACHE.popitem(last=False)
        _CACHE[token] = (time.monotonic() + TTL, size, copy.deepcopy(value))
    return token


def recall(token):
    with _LOCK:
        entry = _CACHE.get(token)
        if entry is None or entry[0] < time.monotonic():
            _CACHE.pop(token, None)
            raise APIError('SEARCH_PREVIEW_EXPIRED', 'Preview expired or was evicted. Preview again.', 410)
        return copy.deepcopy(entry[2])
