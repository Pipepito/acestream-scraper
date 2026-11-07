"""Atomic message admission, observations and cursor advancement."""
from datetime import datetime, timedelta, timezone
from app.config.database import SessionLocal
from app.models.telegram import TelegramSourceRow, TelegramObservation
from app.schemas.extraction import RecipePreview
from app.services.import_exclusion_service import ImportExclusionService

def record(source_id: int, account_id: str, generation: int, message_id: int,
           revision: str, result: RecipePreview, advance: bool) -> bool:
    from app.services.incremental_ingestion_service import ingest_records
    with SessionLocal() as db:
        policy = ImportExclusionService(db).snapshot(claim=True)
        row = db.get(TelegramSourceRow, source_id)
        if row is None or row.account_id != account_id or row.generation != generation or not row.config['enabled']:
            return False
        now = datetime.now(timezone.utc)
        obs = db.get(TelegramObservation, (source_id, message_id))
        if obs is None or obs.revision != revision:
            count = ingest_records(db, result.channels, f'telegram-source:{source_id}', policy=policy)
            row.excluded_count = sum(bool(policy.matches(c.channel_id, c.name)) for c in result.channels)
            row.imported_count += count
            if obs is None:
                obs = TelegramObservation(source_id=source_id, message_id=message_id)
                db.add(obs)
            obs.revision, obs.channel_ids, obs.observed_at = revision, [c.channel_id for c in result.channels], now
        if advance:
            row.cursor = max(row.cursor, message_id)
        row.last_success, row.state, row.message = now, 'current', ''
        db.flush()
        # No bodies retained. Retain at most 1000 revisions/source and 30 days.
        db.query(TelegramObservation).filter(TelegramObservation.source_id == source_id,
            TelegramObservation.observed_at < now - timedelta(days=30)).delete(synchronize_session=False)
        excess = [mid for (mid,) in db.query(TelegramObservation.message_id).filter_by(source_id=source_id)
                  .order_by(TelegramObservation.message_id.desc()).offset(1000).all()]
        if excess:
            db.query(TelegramObservation).filter(TelegramObservation.source_id == source_id,
                TelegramObservation.message_id.in_(excess)).delete(synchronize_session=False)
        db.commit()
        return True



def preview_exclusions(channels):
    with SessionLocal() as db:
        policy = ImportExclusionService(db).snapshot()
        return {c.channel_id: matches for c in channels if (matches := policy.matches(c.channel_id, c.name))}
