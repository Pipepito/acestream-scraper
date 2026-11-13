"""Stable channel categories, live discovery, and explicitly reviewed suggestions."""
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
import re

from app.repositories.category_repository import CategoryRepository
from app.schemas.categories import CategoryView, CategoryInventory, CategorySuggestion, CategoryCoverage, CategoryCoverageRow
from app.services.category_taxonomy import (Category, CHANNEL_IDS, GENRES, BY_ID,
    TAXONOMY_VERSION, channel_category, normalize_label, classify_genres, artwork_status)
from app.services.guide_projection import projected_guide
from app.services.programme_categories import genres, observations


def category_view(item, count=0):
    return CategoryView(**asdict(item), artwork_status=artwork_status(item), count=count)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


# Reviewed broadcaster identities, never substring guesses about a channel title.
_IDENTITIES = {
    'la 1': 'general', 'la 2': 'general', 'antena 3': 'general', 'cuatro': 'general',
    'telecinco': 'general', 'la sexta': 'general', 'lasexta': 'general',
    '24h': 'news', '24 horas': 'news', 'canal 24 horas': 'news', 'clan': 'kids',
    'boing': 'kids', 'disney channel': 'kids', 'teledeporte': 'sports',
    'tdp': 'sports', 'dmax': 'documentaries', 'national geographic': 'documentaries',
    'discovery channel': 'documentaries', 'historia': 'documentaries',
    'canal cocina': 'lifestyle', 'decasa': 'lifestyle', 'mtv': 'music',
}


class CategoryService:
    def __init__(self, db):
        self.db = db
        self.repo = CategoryRepository(db)

    def decorate(self, channels):
        lookup = self.repo.guide_lookup(channels)
        for channel in channels:
            guide = lookup.get((channel.epg_source_id, channel.epg_id))
            channel.epg_logo_url = guide.icon_url if guide else None
        return channels

    def membership(self, filters):
        reference = filters.as_of or datetime.now(timezone.utc)
        # Reference timestamps are short-lived browsing snapshots, not historical
        # programme-search parameters. Bound cache/query lifetime and future reads.
        if abs((reference - datetime.now(timezone.utc)).total_seconds()) > 900:
            raise ValueError('Category reference expired; refresh the category list')
        rows = self.repo.catalogue(filters)
        members, definitions, boundaries = defaultdict(set), {}, []
        projection = projected_guide(self.db, rows, reference) if filters.category_basis == 'now' else {}
        for channel in rows:
            if filters.category_basis == 'channel':
                definition = channel_category(channel.category)
                definitions[definition.id] = definition
                keys = [definition.id]
            else:
                _, current, following = projection[channel.id]
                if current:
                    keys = genres(current) or ['uncategorized']
                    boundaries.append(current.end_time)
                else:
                    keys = ['no-guide']
                if following:
                    boundaries.append(following.start_time)
                for key in keys:
                    definitions[key] = BY_ID.get(key) or Category(key,
                        'No current guide' if key == 'no-guide' else 'Uncategorized',
                        'Sin programa actual' if key == 'no-guide' else 'Sin categoría')
            for key in keys:
                members[key].add(channel.id)
        return reference, rows, members, definitions, min(boundaries, default=None)

    def inventory(self, filters):
        reference, rows, members, definitions, boundary = self.membership(filters)
        ordered = sorted(members, key=lambda key: (key in ('uncategorized', 'no-guide'), definitions[key].label.casefold()))
        return CategoryInventory(basis=filters.category_basis, as_of=reference, taxonomy_version=TAXONOMY_VERSION,
            total=len(rows), items=[category_view(definitions[key], len(members[key])) for key in ordered], next_change_at=boundary)

    def matching_ids(self, filters):
        _, _, members, _, _ = self.membership(filters)
        return sorted(members.get(filters.category_id, set()))

    def preview(self, ids):
        channels = self.repo.selected_channels(ids)
        if len(channels) != len(ids):
            raise ValueError('Channel inventory changed; reload the selection')
        lookup = self.repo.guide_lookup(channels, enabled_only=True)
        guide_ids = sorted({row.id for row in lookup.values() if row})
        anchor = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        schedule = defaultdict(list)
        for program in self.repo.programmes(guide_ids, anchor - timedelta(days=7), anchor + timedelta(days=7)):
            schedule[program.epg_channel_id].append(program)
        result = []
        for channel in channels:
            guide = lookup.get((channel.epg_source_id, channel.epg_id))
            programs = schedule.get(guide.id, []) if guide else []
            groups = sorted({s.group for s in channel.acestream_channels if s.group})
            group_keys = {channel_category(group).id for group in groups}
            recognized = group_keys & CHANNEL_IDS
            name = re.sub(r'\s+(?:hd|uhd|4k|sd)$', '', normalize_label(channel.name))
            identity = _IDENTITIES.get(name)
            evidence, suggested, reason = [], None, 'Insufficient evidence'
            protected = channel.category_origin in ('manual', 'reviewed') or bool(channel.category and channel.category_origin in ('legacy', 'import'))
            counts, days = Counter(), set()
            for program in programs:
                keys = set(genres(program)) & CHANNEL_IDS
                # Count a programme once only when its broad channel role is clear.
                if len(keys) == 1:
                    counts.update(keys)
                    days.add(program.start_time.date().isoformat())
            if protected:
                reason = 'Saved assignment is protected'
            elif len(recognized) > 1 or (recognized and group_keys != recognized) or (identity and recognized and recognized != {identity}):
                reason = 'Conflicting channel evidence'
                evidence = [f'Source group: {group}' for group in groups]
            elif recognized:
                suggested = next(iter(recognized))
                reason = 'Recognized source group'
                evidence = [f'Source group: {group}' for group in groups]
            elif identity:
                suggested, reason = identity, 'Reviewed broadcaster identity'
                evidence = [channel.name]
            elif counts and len(programs) >= 12 and len(days) >= 3:
                key, count = counts.most_common(1)[0]
                if count / len(programs) >= .8:
                    suggested, reason = key, 'Consistent programme schedule'
                evidence = [f'{count}/{len(programs)} programmes; {len(days)} days', f'Window: {anchor.date()} ±7 days']
            fingerprint = digest(dict(version=TAXONOMY_VERSION, id=channel.id, revision=channel.category_revision,
                category=channel.category, origin=channel.category_origin, name=channel.name,
                mapping=[channel.epg_source_id, channel.epg_id, guide.id if guide else None], groups=groups,
                schedule=[(p.id, p.start_time, p.end_time, observations(p)) for p in programs],
                suggestion=suggested, anchor=anchor))
            result.append(CategorySuggestion(channel_id=channel.id, name=channel.name,
                current_category=channel.category, category_origin=channel.category_origin,
                category_revision=channel.category_revision, suggested_category=suggested,
                reason=reason, evidence=evidence, fingerprint=fingerprint))
        return result

    def apply(self, request):
        ids = [item.channel_id for item in request.items]
        if len(set(ids)) != len(ids):
            raise ValueError('Choose unique channels')
        try:
            for channel_id in sorted(ids):
                self.repo.claim(channel_id)
            previews = {item.channel_id: item for item in self.preview(ids)}
            channels = {item.id: item for item in self.repo.selected_channels(ids)}
            for item in request.items:
                preview = previews[item.channel_id]
                if (item.fingerprint != preview.fingerprint or not preview.suggested_category
                        or item.category_id != preview.suggested_category):
                    raise ValueError('Category evidence changed; preview the selection again')
                row = channels[item.channel_id]
                row.category = item.category_id
                row.category_origin = 'reviewed'
                row.category_evidence = {'reason': preview.reason, 'evidence': preview.evidence,
                                         'taxonomy_version': TAXONOMY_VERSION}
                row.category_revision += 1
                row.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return {'updated': len(ids)}
        except Exception:
            self.db.rollback()
            raise

    def assign(self, channel_id, request):
        try:
            self.repo.claim(channel_id, request.expected_revision)
            row = self.repo.selected_channels([channel_id])[0]
            row.category = request.category.strip() if request.category and request.category.strip() else None
            row.category_origin = 'manual' if request.mode == 'manual' else 'automatic'
            if request.mode == 'automatic':
                row.category = None
            row.category_evidence = None
            row.category_revision += 1
            row.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return self.decorate([row])[0]
        except Exception:
            self.db.rollback()
            raise

    def coverage(self, source_id, skip, limit):
        now = datetime.now(timezone.utc)
        total, rows = self.repo.coverage(source_id, now - timedelta(days=7), now + timedelta(days=14), skip, limit)
        items = []
        for label, source, count, channels in rows:
            keys = classify_genres([label])
            statuses = {artwork_status(BY_ID[key]) for key in keys}
            state = 'unmapped' if not keys else 'specific' if 'specific' in statuses else 'parent' if 'parent' in statuses else 'neutral'
            items.append(CategoryCoverageRow(label=label, source_id=source, programme_count=count,
                guide_channel_count=channels, genre_ids=keys, artwork_status=state))
        return CategoryCoverage(taxonomy_version=TAXONOMY_VERSION, total_labels=total, items=items,
                                catalogue=[category_view(item) for item in GENRES])
