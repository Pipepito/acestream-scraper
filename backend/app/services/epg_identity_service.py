"""Shared, collision-free XMLTV identifiers for playlists and guide exports."""
from collections import defaultdict
from urllib.parse import quote
from app.repositories.epg_identity_repository import guide_identities

PREFIX = 'acestream-scraper:'


class EPGIdentityService:
    def __init__(self, db):
        self.sources = defaultdict(set)
        for source_id, xml_id in guide_identities(db):
            self.sources[xml_id].add(source_id)

    def resolve(self, source_id, xml_id):
        if not xml_id:
            return None
        # Preserve upstream identifiers except where they collide or cannot be
        # represented verbatim in an M3U attribute. Reserve our namespace too.
        if (len(self.sources[xml_id]) > 1 or xml_id.startswith(PREFIX)
                or any(char in xml_id for char in '\"\r\n')):
            if source_id is None:
                return None  # an unqualified raw stream cannot choose a source
            return f'{PREFIX}{source_id}:{quote(xml_id, safe="")}'
        return xml_id
