"""One admission and write path for every permanent channel import.

Lists, W3U catalogues, Telegram messages, saved searches and manual Add all
reach ``acestream_channels`` through :meth:`ImportPipeline.apply`. The mode
keeps each path's semantics:

- ``snapshot``: a complete list owned by one source. Exclusions apply by
  identity, rows are upserted, TV channels are created from the guide, and
  rows of that source absent from the snapshot are pruned only when the
  snapshot is non-empty after exclusions, comes without a custom recipe and
  its status is exactly ``'OK'``.
- ``insert_only``: additive sources. Only missing rows are inserted; existing
  rows keep operator names, assignments, activity, headers and ownership.
  Nothing is ever deleted.
- ``manual``: one operator request. Upsert, with the explicit
  ``allow_excluded`` override that exists only in this mode.

The session belongs to the caller: ``apply`` flushes but never commits or
rolls back. When no ``policy`` is given, the exclusion snapshot is claimed
inside the caller's transaction, so rule edits and this import serialize.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Literal, Optional

from sqlalchemy.orm import Session

from app.models.models import AcestreamChannel
from app.repositories.channel_repository import ChannelRepository
from app.services.import_exclusion_service import ImportExclusionService, PolicySnapshot

ImportMode = Literal['snapshot', 'insert_only', 'manual']
MODES: tuple[str, ...] = ('snapshot', 'insert_only', 'manual')


@dataclass(frozen=True)
class ImportReference:
    """Where the entries come from and the options their mode accepts."""
    source_url: Optional[str]
    # snapshot: other spellings of ``source_url`` whose rows the snapshot also owns.
    aliases: tuple[str, ...] = ()
    # snapshot: the fetch status; only exactly 'OK' may prune.
    status: str = 'OK'
    # snapshot: a custom extraction recipe never prunes.
    custom_recipe: bool = False
    # insert_only: refresh ``last_seen`` of rows that already exist.
    touch_existing: bool = False
    # insert_only: classify without writing.
    dry_run: bool = False
    # manual: the operator's explicit override for this one request.
    allow_excluded: bool = False

    def check(self, mode: str) -> None:
        if mode not in MODES:
            raise ValueError(f'Unknown import mode: {mode!r}')
        allowed = {'snapshot': {'aliases', 'status', 'custom_recipe'},
                   'insert_only': {'touch_existing', 'dry_run'},
                   'manual': {'allow_excluded'}}[mode]
        defaults = ImportReference(None)
        used = {name for name in ('aliases', 'status', 'custom_recipe', 'touch_existing', 'dry_run', 'allow_excluded')
                if getattr(self, name) != getattr(defaults, name)}
        if used - allowed:
            raise ValueError(f'{", ".join(sorted(used - allowed))} cannot be used in {mode} mode')


@dataclass
class ImportEntry:
    """One stream offered by a source."""
    channel_id: str
    name: str
    group: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    stream_url: Optional[str] = None
    stream_headers: Optional[dict] = None
    is_online: Optional[bool] = None
    # snapshot: the publisher metadata read by the guide step, which stores
    # the TV channel it assigns under 'tv_channel_id'.
    metadata: dict = field(default_factory=dict)
    # manual: the fields the operator sent, applied as-is to an existing row.
    updates: Optional[dict] = None

    @classmethod
    def from_scrape(cls, channel_id: str, name: str, metadata: dict) -> 'ImportEntry':
        """A list entry, with the metadata names the list extractors produce."""
        return cls(channel_id, name,
                   group=metadata.get('group_title', metadata.get('group', '')),
                   logo=metadata.get('tvg_logo', metadata.get('logo', '')),
                   tvg_id=metadata.get('tvg_id', ''),
                   tvg_name=metadata.get('tvg_name', ''),
                   # Set only for streams addressed by URL instead of by an
                   # acestream id. See M3UService._looks_like_stream.
                   stream_url=metadata.get('stream_url'),
                   stream_headers=metadata.get('stream_headers'),
                   metadata=metadata)


ImportOutcome = Literal['added', 'updated', 'upserted', 'existing', 'duplicate', 'excluded']


@dataclass
class ImportItem:
    entry: ImportEntry
    outcome: ImportOutcome
    rule_ids: list[int] = field(default_factory=list)
    channel: Optional[AcestreamChannel] = None


@dataclass
class ImportResult:
    policy: PolicySnapshot
    items: list[ImportItem]
    # snapshot: IDs refused by the policy, and those plus the source's stored
    # rows that match it; follow-up automation must leave both alone.
    excluded_ids: set[str] = field(default_factory=set)
    protected_ids: set[str] = field(default_factory=set)

    @property
    def channels(self) -> list[AcestreamChannel]:
        """Rows written by this import, in entry order."""
        return [item.channel for item in self.items if item.channel is not None]

    def count(self, outcome: ImportOutcome) -> int:
        return sum(item.outcome == outcome for item in self.items)


class ImportPipeline:
    @staticmethod
    def apply(db: Session, reference: ImportReference, entries: Iterable[ImportEntry], mode: ImportMode, *,
              policy: Optional[PolicySnapshot] = None) -> ImportResult:
        reference.check(mode)
        entries = list(entries)
        if policy is None:
            policy = ImportExclusionService(db).snapshot(claim=True)
        apply_mode = {'snapshot': _snapshot, 'insert_only': _insert_only, 'manual': _manual}[mode]
        return apply_mode(db, reference, entries, policy)


def _snapshot(db: Session, reference: ImportReference, entries: list[ImportEntry],
              policy: PolicySnapshot) -> ImportResult:
    from app.services.epg_service import EPGService
    from app.services.m3u_service import M3UService
    from app.services.tvchannel_service import TVChannelService
    observed_ids = {entry.channel_id for entry in entries}
    excluded_ids = {entry.channel_id for entry in entries if policy.matches(entry.channel_id, entry.name)}
    items = [ImportItem(entry, 'excluded', policy.matches(entry.channel_id, entry.name))
             if entry.channel_id in excluded_ids else ImportItem(entry, 'upserted') for entry in entries]
    admitted = [item for item in items if item.outcome != 'excluded']
    source_urls = {reference.source_url, *reference.aliases}
    source_query = db.query(AcestreamChannel).filter(AcestreamChannel.source_url.in_(source_urls))
    protected_ids = excluded_ids | {ch.id for ch in source_query.all() if policy.matches(ch.id, ch.name)}
    # All-excluded, empty, failed and partial snapshots never prune.
    if admitted and observed_ids and not reference.custom_recipe and reference.status == 'OK':
        missing = source_query.filter(~AcestreamChannel.id.in_(observed_ids | protected_ids))
        ChannelRepository(db).remove_search_memberships([row.id for row in missing.all()])
        missing.delete(synchronize_session=False)
    # The guide step stores the TV channel it assigns in each entry's metadata
    # and may refuse more entries under its own claimed policy snapshot.
    assigned = M3UService().auto_create_tv_channels_from_epg(
        db, [(item.entry.channel_id, item.entry.name, item.entry.metadata) for item in admitted],
        EPGService(db), TVChannelService(db))
    # The guide step returns the same metadata dicts it was given, in input
    # order, so each assignment is matched back to its entry by identity.
    pending = iter(admitted)
    repository = ChannelRepository(db)
    for _cid, _name, metadata in assigned:
        item = next(candidate for candidate in pending if candidate.entry.metadata is metadata)
        entry = item.entry
        item.channel = repository.create_or_update_channel(
            channel_id=entry.channel_id, name=entry.name, source_url=reference.source_url,
            group=entry.group, logo=entry.logo, tvg_id=entry.tvg_id, tvg_name=entry.tvg_name,
            # auto_create_tv_channels_from_epg also handles IDs that have not
            # been persisted yet. Carry its staged association into the
            # INSERT; existing rows are assigned by the repository's
            # conflict-checked UPDATE.
            tv_channel_id=metadata.get('tv_channel_id'),
            stream_url=entry.stream_url, stream_headers=entry.stream_headers,
            # Catalogue presence is not evidence of a live signal.
            is_online=None, commit=False)
    for item in admitted:
        if item.channel is None:
            item.outcome, item.rule_ids = 'excluded', policy.matches(item.entry.channel_id, item.entry.name)
    return ImportResult(policy, items, excluded_ids, protected_ids)


def _insert_only(db: Session, reference: ImportReference, entries: list[ImportEntry],
                 policy: PolicySnapshot) -> ImportResult:
    repository = ChannelRepository(db)
    existing_ids = repository.existing_import_ids(entry.channel_id for entry in entries)
    items: list[ImportItem] = []
    seen: set[str] = set()
    for entry in entries:
        rules = policy.matches(entry.channel_id, entry.name)
        if rules:
            items.append(ImportItem(entry, 'excluded', rules))
            continue
        if entry.channel_id in seen or entry.channel_id in existing_ids:
            # Existing labels, assignments, opt-outs and probe results belong
            # to their owners; an observation is not proof of signal.
            outcome = 'duplicate' if entry.channel_id in seen else 'existing'
            if reference.touch_existing and not reference.dry_run:
                repository.get_channel_by_id(entry.channel_id).last_seen = datetime.now(timezone.utc)
            items.append(ImportItem(entry, outcome))
        else:
            channel = None
            if not reference.dry_run:
                channel = repository.create_or_update_channel(
                    entry.channel_id, entry.name, source_url=reference.source_url, group=entry.group,
                    logo=entry.logo, tvg_id=entry.tvg_id, tvg_name=entry.tvg_name,
                    stream_url=entry.stream_url, stream_headers=entry.stream_headers,
                    is_online=None, commit=False)
            items.append(ImportItem(entry, 'added', channel=channel))
        seen.add(entry.channel_id)
    return ImportResult(policy, items)


def _manual(db: Session, reference: ImportReference, entries: list[ImportEntry],
            policy: PolicySnapshot) -> ImportResult:
    from app.api.error_handlers import APIError
    repository = ChannelRepository(db)
    items: list[ImportItem] = []
    for entry in entries:
        rules = policy.matches(entry.channel_id, entry.name)
        if rules and not reference.allow_excluded:
            raise APIError('IMPORT_EXCLUDED', 'This stream matches an import exclusion.', 409,
                           {'rule_ids': rules})
        if repository.get_channel_by_id(entry.channel_id) is not None:
            updates: dict[str, Any] = dict(entry.updates) if entry.updates is not None else {'name': entry.name}
            channel = repository.update_channel(entry.channel_id, updates, commit=False)
            items.append(ImportItem(entry, 'updated', rules, channel))
        else:
            channel = repository.create_or_update_channel(
                channel_id=entry.channel_id, name=entry.name, source_url=reference.source_url,
                group=entry.group, logo=entry.logo, tvg_id=entry.tvg_id, tvg_name=entry.tvg_name,
                is_online=entry.is_online, commit=False)
            items.append(ImportItem(entry, 'added', rules, channel))
    return ImportResult(policy, items)
