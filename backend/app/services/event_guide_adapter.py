"""A bounded subset of schema.org SportsEvent JSON / HTML JSON-LD.

No JavaScript execution, remote contexts, inferred dates or title identities.
Sources without stable IDs or explicit dates require another reviewed adapter.
"""
import hashlib
from html.parser import HTMLParser
import json

from app.schemas.events import EventImport, EventObservation, EventBroadcast


class _Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = False
        self.blocks = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.active = dict(attrs).get('type', '').lower() == 'application/ld+json'
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.active:
            self.blocks.append(''.join(self.parts))
            self.parts = []
            self.active = False
            if len(self.blocks) > 64:
                raise ValueError('Too many structured guide blocks')


def _items(value):
    return value if isinstance(value, list) else [value] if value is not None else []


def _name(value):
    if isinstance(value, dict):
        value = value.get('name', '')
    return value if isinstance(value, str) else ''


def _type(value, name):
    return any(kind in (name, 'https://schema.org/' + name, 'http://schema.org/' + name)
               for kind in _items(value.get('@type')))


def _identity(value):
    identity = value.get('@id') or value.get('identifier')
    if isinstance(identity, dict):
        identity = identity.get('value')
    return str(identity) if isinstance(identity, (str, int)) and not isinstance(identity, bool) else ''


def parse_guide(raw, *, source_id, source_name, zone):
    if raw.lstrip().startswith(('{', '[')):
        roots = [json.loads(raw)]
    else:
        parser = _Scripts()
        parser.feed(raw)
        roots = [json.loads(block) for block in parser.blocks]
    nodes = []
    pending = [(root, 0) for root in roots]
    visited = 0
    while pending:
        value, depth = pending.pop()
        visited += 1
        if depth > 32 or visited > 20000:
            raise ValueError('Structured guide nesting or inventory limit exceeded')
        if isinstance(value, dict):
            nodes.append(value)
            pending.extend((child, depth + 1) for key, child in value.items() if key != '@context')
        elif isinstance(value, list):
            pending.extend((child, depth + 1) for child in value)
    matches = {}
    broadcasts = {}
    for node in nodes:
        if _type(node, 'BroadcastEvent'):
            for ref in _items(node.get('broadcastOfEvent')):
                key = ref if isinstance(ref, str) else _identity(ref) if isinstance(ref, dict) else ''
                if key:
                    broadcasts.setdefault(key, []).append(node)
    for node in nodes:
        if not _type(node, 'SportsEvent'):
            continue
        external_id = _identity(node)
        if not external_id:
            raise ValueError('SportsEvent requires a stable @id or identifier')
        variants = {}
        media = [item for item in _items(node.get('subjectOf')) + _items(node.get('video'))
                 if isinstance(item, dict) and _type(item, 'VideoObject')]
        linked = broadcasts.get(external_id, [])
        for item in media + linked:
            label = _name(item.get('publishedOn')) or _name(item.get('name')) or 'Event broadcast'
            language = _name(item.get('inLanguage'))
            quality = _name(item.get('videoFormat'))
            # Ticket/event/homepage URLs are not media. Broadcasts without an
            # explicit VideoObject content/embed URL remain useful unresolved rows.
            url = (item.get('contentUrl') or item.get('embedUrl')) if _type(item, 'VideoObject') else None
            key = _identity(item) or hashlib.sha256(json.dumps([label, language, quality]).encode()).hexdigest()[:32]
            variant = EventBroadcast(id=key, label=label, language=language, quality=quality, url=url)
            if key in variants and variants[key] != variant:
                raise ValueError('Ambiguous broadcast identity; supply stable variant IDs')
            variants[key] = variant
        participants = list(dict.fromkeys(filter(None, (_name(team) for team in
            _items(node.get('homeTeam')) + _items(node.get('awayTeam')) + _items(node.get('competitor'))))))
        state = {'EventScheduled': 'scheduled', 'EventRescheduled': 'scheduled',
                 'EventPostponed': 'postponed', 'EventCancelled': 'cancelled'}.get(
                     _name(node.get('eventStatus')).rsplit('/', 1)[-1], 'unknown')
        images = _items(node.get('image'))
        artwork = images[0] if images else None
        if isinstance(artwork, dict):
            artwork = artwork.get('contentUrl') or artwork.get('url')
        observation = EventObservation(artwork_url=artwork,source_id=source_id, source_name=source_name, source_kind='guide',
            external_id=external_id, title=node.get('name', ''), timezone=zone,
            sport=_name(node.get('sport')), competition=_name(node.get('superEvent')),
            participants=participants, starts_at=node.get('startDate'), ends_at=node.get('endDate'), state=state,
            time_notes=f'Structured guide; local times use {zone}. No relative date or duration inference.',
            broadcasts=list(variants.values()))
        if external_id in matches and matches[external_id] != observation:
            raise ValueError('Conflicting observations for the same publisher ID')
        matches[external_id] = observation
        if len(matches) > 500:
            raise ValueError('At most 500 event observations per guide')
    if not matches:
        raise ValueError('No supported SportsEvent records found')
    return EventImport(observations=list(matches.values()))
