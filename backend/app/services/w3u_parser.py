"""Bounded W3U traversal. External fields are data, never executable instructions."""
import asyncio
import hashlib
import json
import re
import time
from dataclasses import dataclass
from collections import deque
from urllib.parse import parse_qs, urldefrag, urljoin, urlsplit, urlunsplit

from app.services.m3u_service import M3UService
from app.services.live_providers import for_stream_url
from app.utils.bounded_source import source_get

COMPATIBLE = frozenset({'acestream', 'hls', 'mpegts', 'resolver'})
HEX_ID = re.compile(r'[0-9a-fA-F]{40}')


@dataclass(frozen=True)
class Limits:
    requests: int = 64
    depth: int = 12
    bytes: int = 16 * 1024 * 1024
    document_bytes: int = 4 * 1024 * 1024
    records: int = 10000
    seconds: float = 45


class LimitReached(ValueError):
    pass


class FetchLimit(LimitReached):
    pass


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()[:32]


def safe_text(value, limit=255):
    if not isinstance(value, str):
        return ''
    # A publisher can put signed links in any descriptive field. Never echo them.
    from app.services.diagnostics_service import redact
    value = redact(value[:max(4096, limit * 2)])
    value = re.sub(r'\bacestream://[^\s<>]+', '[link]', value, flags=re.I)
    return ' '.join(value.split())[:limit]


def http_url(value, base=''):
    if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 32 for c in value):
        raise ValueError('Invalid URL')
    result = urldefrag(urljoin(base, value.strip()))[0]
    parsed = urlsplit(result)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Only HTTP(S) URLs without embedded credentials are supported')
    _ = parsed.port
    return result


def origin(value):
    try:
        parsed = urlsplit(value or '')
        return parsed.hostname or 'Local upload'
    except ValueError:
        return 'Unknown source'


def safe_image(value, base):
    try:
        result = http_url(value, base)
        parsed = urlsplit(result)
        # No browser fetches of private addresses or signed image URLs. Artwork
        # is opt-in in the UI and sent without referrers.
        import ipaddress
        try:
            if not ipaddress.ip_address(parsed.hostname).is_global:
                return None
        except ValueError:
            if '.' not in parsed.hostname or parsed.hostname.endswith(('.local', '.localhost')):
                return None
        if parsed.query:
            return None
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
    except (ValueError, TypeError):
        return None


def headers_for(record, inherited):
    if any(key in record for key in ('headers', 'cookie', 'authorization')):
        raise ValueError('Unsupported header fields')
    headers = dict(inherited)
    for key, name in (('userAgent', 'User-Agent'), ('referer', 'Referer'), ('referrer', 'Referer'), ('origin', 'Origin')):
        if key in record:
            value = record[key]
            if not isinstance(value, str) or len(value) > 2048 or any(ord(c) < 32 for c in value):
                raise ValueError('Invalid source header')
            headers[name] = value
    return headers


def content_type(record):
    kind = str(record.get('type', '')).casefold()
    if kind in ('movie', 'series', 'episode', 'vod'):
        return 'vod'
    if kind in ('event', 'sportsevent', 'sports_event'):
        return 'event'
    if kind in ('live', 'channel', 'tv'):
        return 'live'
    return 'unknown'


def classify(value, record, base):
    if record.get('drm') or record.get('license') or record.get('licenseUrl'):
        return 'unsupported', None, None, 'DRM playback is not supported'
    if content_type(record) == 'vod':
        return 'vod', None, None, 'VOD retained separately; playback and progress tracking follow issue #99'

    if not isinstance(value, str) or not value.strip():
        return 'invalid', None, None, 'Missing stream URL'
    value = value.strip()
    if len(value) > 2048 or any(ord(c) < 32 for c in value):
        return 'invalid', None, None, 'Invalid stream URL'
    if value.lower().startswith('acestream://'):
        content_id = value[len('acestream://'):]
        if HEX_ID.fullmatch(content_id):
            return 'acestream', content_id.lower(), None, 'AceStream; signal not checked'
        return 'invalid', None, None, 'AceStream ID must contain exactly 40 hexadecimal characters'
    if for_stream_url(value):
        return 'resolver', M3UService._stream_id(value), value, 'Broadcaster adapter; resolved at browser playback. Private catalogue inputs are excluded from playlist exports.'
    try:
        url = http_url(value, base)
        parsed = urlsplit(url)
    except ValueError:
        return 'unsupported', None, None, 'Unsupported scheme or URL credentials'
    if parsed.path == '/ace/getstream' and parsed.hostname in ('127.0.0.1', 'localhost', '::1') and parsed.port in (None, 6878):
        ids = parse_qs(parsed.query).get('id', [])
        if len(ids) == 1 and HEX_ID.fullmatch(ids[0]):
            return 'acestream', ids[0].lower(), None, 'Engine URL normalized; uses configured playback route'
        return 'invalid', None, None, 'Engine URL has an invalid or ambiguous ID'
    import ipaddress
    from app.utils.url_guard import validate_resolved_addresses
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        address = None
    if address is not None:
        try:
            validate_resolved_addresses(parsed.hostname, [address])
        except ValueError:
            return 'invalid', None, None, 'Blocked media destination'
    if record.get('drm') or record.get('license') or record.get('licenseUrl'):
        return 'unsupported', None, None, 'DRM playback is not supported'
    if record.get('isHost') or record.get('embed'):
        return 'unsupported', None, None, 'Website/embed source needs an explicit resolver adapter'
    path = parsed.path.lower()
    if path.endswith('.mpd'):
        return 'unsupported', None, None, 'DASH playback is not supported'
    if path.endswith(('.mp4', '.mkv', '.mov', '.avi', '.webm')) or str(record.get('type', '')).lower() in ('movie', 'series', 'vod'):
        return 'vod', None, None, 'VOD catalogue retained; playback and progress tracking follow issue #99'
    kind = 'hls' if path.endswith('.m3u8') else 'mpegts' if path.endswith('.ts') else None
    if kind:
        return kind, M3UService._stream_id(url), url, 'Browser playback; availability and codecs are not verified. Private catalogue inputs are excluded from playlist exports.'
    return 'unsupported', None, None, 'Website or unrecognized media URL; needs a tested resolver'


class W3UTraversal:
    def __init__(self, *, limits=None, cached=None):
        self.limits = limits or Limits()
        self.cached = cached or {}
        self.documents = {}
        self.counts = dict(accepted=0, duplicates=0, invalid=0, unsupported=0,
                           failed_fetches=0, requests=0, bytes_read=0, cached_documents=0)
        self.entries = []
        self.warnings = []
        self.partial = False
        self.deadline = time.monotonic() + self.limits.seconds
        self.identities = set()
        self.occurrences = {}
        self.failed_urls = set()

    def budget(self):
        if time.monotonic() >= self.deadline:
            raise LimitReached('Traversal time limit reached')
        if len(self.entries) >= self.limits.records:
            raise LimitReached('Catalogue record limit reached')

    async def document(self, url):
        requested = url
        if requested in self.documents:
            saved = self.documents[requested]
            return saved['data'], saved['url']
        if requested in self.failed_urls:
            raise ValueError('Previously failed document')
        visited = set()
        for _ in range(6):
            self.budget()
            if url in visited:
                raise ValueError('Redirect cycle')
            visited.add(url)
            if self.counts['requests'] >= self.limits.requests:
                raise FetchLimit('Catalogue request limit reached')
            remaining = self.limits.bytes - self.counts['bytes_read']
            if remaining <= 0:
                raise FetchLimit('Catalogue byte limit reached')
            previous = self.cached.get(url, {})
            headers = {}
            if previous.get('etag'):
                headers['If-None-Match'] = previous['etag']
            if previous.get('modified'):
                headers['If-Modified-Since'] = previous['modified']
            self.counts['requests'] += 1
            allowance = min(self.limits.document_bytes, remaining)
            self.counts['bytes_read'] += allowance
            response = await source_get(url, headers=headers,
                timeout=min(10, max(0, self.deadline - time.monotonic())),
                max_bytes=min(self.limits.document_bytes, remaining))
            self.counts['bytes_read'] += len(response.content) - allowance
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get('Location')
                if not location:
                    raise ValueError('Missing redirect target')
                url = http_url(location, url)
                continue
            if response.status_code == 304 and previous.get('data') is not None:
                data = previous['data']
                # Cached bytes still consume the aggregate parsing budget.
                self.counts['bytes_read'] += previous['size']
                if self.counts['bytes_read'] > self.limits.bytes:
                    raise FetchLimit('Catalogue byte limit reached')
                self.counts['cached_documents'] += 1
                saved = previous
            else:
                response.raise_for_status()
                if response.status_code != 200:
                    raise ValueError('Unexpected document response')
                data = await asyncio.to_thread(json.loads, response.content.decode('utf-8-sig'))
                if not isinstance(data, dict) or not any(key in data for key in ('groups', 'stations')):
                    raise ValueError('Expected a W3U object with groups or stations')
                saved = dict(data=data, url=url, size=len(response.content),
                             etag=response.headers.get('ETag', '')[:512],
                             modified=response.headers.get('Last-Modified', '')[:128])
            self.documents[url] = saved
            self.documents[requested] = saved
            return data, url
        raise ValueError('Too many redirects')

    def node(self, record, parent, base, kind, identity):
        self.budget()
        key = digest(f'{parent}:{identity}')
        count = self.occurrences.get(key, 0)
        self.occurrences[key] = count + 1
        node_id = digest(f'{key}:{count}')
        number = record.get('number')
        return dict(id=node_id, parent_id=parent, name=safe_text(record.get('name')) or 'Unnamed entry',
                    kind=kind, content_type=content_type(record), reason='', description=safe_text(record.get('info') or record.get('description'), 2000),
                    image=safe_image(record.get('image'), base),
                    guide_id=safe_text(record.get('epgId')) or None,
                    number=number if type(number) is int and 0 < number < 100000 else None,
                    origin=origin(base), header_names=[], channel_id=None, duplicate=False,
                    retained=False, imported=False)

    async def run(self, *, url=None, sample=None):
        base = url or ''
        try:
            if sample is not None:
                raw = sample.encode('utf-8')
                if len(raw) > self.limits.document_bytes:
                    raise ValueError('Local W3U file exceeds 4 MiB')
                self.counts['bytes_read'] = len(raw)
                data = await asyncio.to_thread(json.loads, raw.decode('utf-8-sig'))
                if not isinstance(data, dict) or not any(k in data for k in ('groups', 'stations')):
                    raise ValueError('Expected W3U groups or stations')
            else:
                base = http_url(url)
                data, base = await self.document(base)
        except Exception as exc:
            raise ValueError('Unable to read a valid W3U catalogue. Check the URL/file and source access.') from exc
        root = self.node(data, None, base, 'folder', 'root')
        root['id'] = 'root'
        self.entries.append(root)
        # Breadth-first navigation gives shallow sections a chance before a
        # large linked archive consumes the budget. Never recurse in Python.
        stack = deque([(data, 'root', base, 0, frozenset({base}), {}, content_type(data))])
        try:
            while stack:
                self.budget()
                record, parent, base, depth, ancestors, inherited, inherited_type = stack.popleft()
                if depth > self.limits.depth:
                    self.partial = True
                    self.warnings.append('Maximum folder depth reached')
                    continue
                try:
                    headers = headers_for(record, inherited)
                except ValueError:
                    self.partial = True
                    self.warnings.append('A folder has invalid headers; its entries were skipped')
                    continue
                children = []
                for field, folder in (('groups', True), ('stations', False)):
                    values = record.get(field, [])
                    if not isinstance(values, list):
                        self.partial = True
                        self.warnings.append('Expected an array of groups or stations')
                        continue
                    for child in values:
                        self.budget()
                        if not isinstance(child, dict):
                            entry = self.node({'name': 'Invalid entry'}, parent, base, 'invalid', 'invalid')
                            entry['reason'] = 'Expected a W3U record object'
                            self.entries.append(entry)
                            self.counts['invalid'] += 1
                            continue
                        child = dict(child)
                        if content_type(child) == 'unknown' and inherited_type != 'unknown':
                            child['type'] = inherited_type
                        value = child.get('url', '')
                        has_children = 'groups' in child or 'stations' in child
                        linked = folder or child.get('import') is True or (
                            isinstance(value, str) and value.split('?', 1)[0].lower().endswith(('.w3u', '.json')))
                        if folder or has_children or linked:
                            entry = self.node(child, parent, base, 'folder', str(value) or safe_text(child.get('name')))
                            self.entries.append(entry)
                            if has_children:
                                children.append((child, entry['id'], base, depth + 1, ancestors, headers, content_type(child)))
                            elif value:
                                try:
                                    target = http_url(value, base)
                                    if target in ancestors:
                                        entry['reason'] = 'Cycle/update reference skipped'
                                        continue
                                    document, final_url = await self.document(target)
                                    if final_url in ancestors:
                                        entry['reason'] = 'Cycle/update reference skipped'
                                        continue
                                    children.append((document, entry['id'], final_url, depth + 1,
                                                     ancestors | {target, final_url}, headers_for(child, headers), content_type(child)))
                                except FetchLimit as exc:
                                    entry['reason'] = str(exc)
                                    self.partial = True
                                    self.warnings.append(str(exc))
                                except LimitReached:
                                    raise
                                except Exception:
                                    # Never include the upstream exception, URL, or response body.
                                    self.failed_urls.add(str(value))
                                    entry['reason'] = 'Child catalogue unavailable or invalid; previous entries are retained on refresh'
                                    self.counts['failed_fetches'] += 1
                                    self.partial = True
                            continue
                        kind, channel_id, stream_url, reason = classify(value, child, base)
                        entry = self.node(child, parent, base, kind, channel_id or str(value) or safe_text(child.get('name')))
                        entry.update(channel_id=channel_id, reason=reason)
                        publisher_id = child.get('id')
                        if isinstance(publisher_id, (str, int)) and not isinstance(publisher_id, bool):
                            entry['_publisher_id'] = digest(str(publisher_id))
                        try:
                            media_headers = headers_for(child, headers)
                        except ValueError:
                            entry.update(kind='unsupported', channel_id=None, reason='Unsupported or invalid source headers')
                            kind, channel_id = 'unsupported', None
                            media_headers = {}
                        if channel_id and stream_url and media_headers:
                            channel_id = M3UService._stream_id(stream_url + '\n' + json.dumps(media_headers, sort_keys=True))
                            entry['channel_id'] = channel_id
                        if channel_id:
                            entry['duplicate'] = channel_id in self.identities
                            self.identities.add(channel_id)
                            self.counts['duplicates' if entry['duplicate'] else 'accepted'] += 1
                            entry['_stream_url'] = stream_url
                            entry['_headers'] = media_headers if stream_url else {}
                            entry['header_names'] = sorted(entry['_headers'])
                        else:
                            self.counts['invalid' if kind == 'invalid' else 'unsupported'] += 1
                        self.entries.append(entry)
                stack.extend(children)
        except LimitReached as exc:
            self.partial = True
            self.warnings.append(str(exc))
        return dict(entries=self.entries, counts=self.counts, partial=self.partial,
                    warnings=list(dict.fromkeys(self.warnings))[:20], documents=self.documents)
