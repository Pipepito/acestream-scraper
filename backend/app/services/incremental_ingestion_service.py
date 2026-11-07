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
    return result.count('added')
