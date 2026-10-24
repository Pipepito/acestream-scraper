"""Additive stream ingestion shared by message transports; caller owns commit."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.channel_repository import ChannelRepository
from app.schemas.extraction import ExtractedChannel


def ingest_records(db: Session, records: list[ExtractedChannel], provenance: str) -> int:
    repository = ChannelRepository(db)
    imported = 0
    for record in records:
        existing = repository.get_channel_by_id(record.channel_id)
        if existing is None:
            repository.create_or_update_channel(record.channel_id, record.name,
                source_url=provenance, group=record.metadata.get('group_title'),
                logo=record.metadata.get('tvg_logo'), tvg_id=record.metadata.get('tvg_id'),
                commit=False)
            imported += 1
        else:
            # Existing labels, assignments, opt-outs and probe results belong to
            # their owners. A Telegram observation is not proof of signal.
            existing.last_seen = datetime.now(timezone.utc)
    return imported
