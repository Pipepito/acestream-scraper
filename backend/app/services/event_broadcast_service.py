"""Read-only broadcaster links, independent from stream resolution and signal."""
from app.schemas.events import EventChannelTarget
from app.services.tv_matching_service import normalize_name, name_score


class EventBroadcastService:
    def __init__(self, repo):
        self.repo = repo
        self.indexes = {}
        self.manual_targets = {}

    @staticmethod
    def view(kind, row):
        return EventChannelTarget(kind=kind, id=row['id'], name=row['name'],
                                  country=row.get('country') or '', source_name=row.get('source_name') or '')

    def search(self, search):
        return [self.view(kind, row) for kind in ('tv', 'epg') for row in self.repo.target_rows(kind, search)]

    def match(self, broadcast):
        name = normalize_name(broadcast.label, broadcast.country)
        for kind in ('tv', 'epg'):
            if kind not in self.indexes:
                rows = self.repo.target_rows(kind)
                # Do not claim uniqueness after a truncated inventory scan.
                if len(rows) > 20000:
                    self.indexes[kind] = None
                else:
                    index = {}
                    for row in rows:
                        candidate = normalize_name(row['name'], row.get('country'))
                        index.setdefault(candidate.text, []).append((candidate, row))
                    self.indexes[kind] = index
            index = self.indexes[kind]
            if index is None:
                return None
            matches = [row for candidate, row in index.get(name.text, []) if name_score(name, candidate)]
            if len(matches) == 1:
                return self.view(kind, matches[0])
            if len(matches) > 1:
                return None
        return None

    def reviewed_target(self, mapping):
        key = (mapping['kind'], mapping['id'])
        if key not in self.manual_targets:
            self.manual_targets[key] = self.repo.target(*key)
        row = self.manual_targets[key]
        if not row:
            return None
        # IDs can be reused after an EPG replacement/deletion. Do not point a
        # saved manual choice at a different channel that inherited the row ID.
        if any(row.get(key) != mapping.get(key) for key in ('name', 'epg_source_id', 'channel_xml_id')):
            return None
        return self.view(mapping['kind'], row)
