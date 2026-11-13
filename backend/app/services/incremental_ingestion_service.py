"""Additive stream ingestion shared by message transports; caller owns commit."""
from sqlalchemy.orm import Session
from app.schemas.extraction import ExtractedChannel
from app.services.import_pipeline import ImportEntry, ImportPipeline, ImportReference


def ingest_records(db: Session, records: list[ExtractedChannel], provenance: str, *, policy=None) -> int:
    # Existing labels, assignments, opt-outs and probe results belong to
    # their owners. A Telegram observation is not proof of signal: existing
    # rows only get last_seen.
    result = ImportPipeline.apply(db, ImportReference(provenance, touch_existing=True), [
        ImportEntry(record.channel_id, record.name, group=record.metadata.get('group_title'),
                    logo=record.metadata.get('tvg_logo'), tvg_id=record.metadata.get('tvg_id'))
        for record in records], 'insert_only', policy=policy)
    assign_new_streams(db, [item.channel for item in result.items if item.outcome == 'added' and item.channel is not None])
    return result.count('added')


def assign_new_streams(db: Session, channels) -> int:
    """Link streams this import just added to the one active TV channel with the same name.

    Uses the conservative identity rule of automatch: the normalized names must be
    equal, a country on only one side rules the candidate out, and exactly one
    active TV channel may qualify. A tvg-id, when present,
    must agree with the candidate's guide ID. TV channels are never created and
    rows that existed before the import are never touched."""
    from app.models.models import TVChannel
    from app.repositories.channel_repository import ChannelRepository
    from app.services.tv_matching_service import name_score, normalize_name
    if not channels:
        return 0
    index = {}
    for tv in db.query(TVChannel.id, TVChannel.name, TVChannel.country, TVChannel.epg_id).filter(TVChannel.is_active.is_(True)).all():
        candidate = normalize_name(tv.name, tv.country)
        index.setdefault(candidate.text, []).append((candidate, tv))
    repository = ChannelRepository(db)
    excluded = repository.get_import_assignment_exclusions(channel.id for channel in channels)
    targets = {}
    for channel in channels:
        if channel.id in excluded:
            continue
        name = normalize_name(channel.name)
        matches = [tv for candidate, tv in index.get(name.text, [])
                   if name_score(name, candidate)
                   and not (channel.tvg_id and tv.epg_id and channel.tvg_id != tv.epg_id)]
        if len(matches) == 1:
            targets.setdefault(matches[0].id, []).append(channel.id)
    return sum(repository.assign_acestreams_to_tv_channel(ids, tv_id, commit=False) for tv_id, ids in targets.items())
