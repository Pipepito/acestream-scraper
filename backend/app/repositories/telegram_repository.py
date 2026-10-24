"""Short transactions; never hold a session across Telegram or regex work."""
from app.services.telegram.errors import TelegramActionError

from datetime import datetime, timedelta, timezone
from app.config.database import SessionLocal
from app.models.models import AcestreamChannel
from app.models.telegram import TelegramSourceRow, TelegramObservation
from app.schemas.telegram import TelegramSource, TelegramSourceConfig
from app.schemas.extraction import RecipePreview


def dto(row: TelegramSourceRow) -> TelegramSource:
    return TelegramSource(**row.config, id=row.id, chat_label=row.chat_label,
        sender_labels=row.sender_labels, cursor=row.cursor, state=row.state,
        last_success=row.last_success, imported_count=row.imported_count, message=row.message)


def list_sources(account_id: str) -> list[TelegramSource]:
    with SessionLocal() as db:
        return [dto(row) for row in db.query(TelegramSourceRow).filter_by(account_id=account_id).order_by(TelegramSourceRow.id).all()]


def save_source(account_id: str, config: TelegramSourceConfig, chat_label: str,
                labels: dict[str, str], cursor: int, source_id: int | None = None) -> TelegramSource:
    with SessionLocal() as db:
        row = db.get(TelegramSourceRow, source_id) if source_id else None
        if source_id and (row is None or row.account_id != account_id):
            raise TelegramActionError('Source no longer exists')
        if row is None:
            if db.query(TelegramSourceRow).filter_by(account_id=account_id).count() >= 25:
                raise TelegramActionError('At most 25 Telegram sources are supported')
            row = TelegramSourceRow(account_id=account_id, cursor=cursor, imported_count=0, generation=0)
            db.add(row)
        elif row.config['chat_id'] != config.chat_id:
            raise TelegramActionError('Create a new source to select a different chat')
        row.config = config.model_dump(mode='json')
        row.chat_label, row.sender_labels = chat_label[:255], labels
        row.generation += 1
        row.state = 'waiting' if config.enabled else 'paused'
        row.message = ''
        db.commit()
        return dto(row)


def snapshot(source_id: int, account_id: str) -> tuple[TelegramSource, int] | None:
    with SessionLocal() as db:
        row = db.get(TelegramSourceRow, source_id)
        if row is None or row.account_id != account_id:
            return None
        return dto(row), row.generation


def set_status(source_id: int, state: str, message: str = '') -> None:
    with SessionLocal() as db:
        row = db.get(TelegramSourceRow, source_id)
        if row:
            row.state, row.message = state, message
            db.commit()


def record(source_id: int, account_id: str, generation: int, message_id: int,
           revision: str, result: RecipePreview, advance: bool) -> bool:
    from app.services.incremental_ingestion_service import ingest_records
    with SessionLocal() as db:
        row = db.get(TelegramSourceRow, source_id)
        if row is None or row.account_id != account_id or row.generation != generation or not row.config['enabled']:
            return False
        now = datetime.now(timezone.utc)
        obs = db.get(TelegramObservation, (source_id, message_id))
        if obs is None or obs.revision != revision:
            count = ingest_records(db, result.channels, f'telegram-source:{source_id}')
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


def observed_ids(source_id: int) -> list[int]:
    with SessionLocal() as db:
        return [mid for (mid,) in db.query(TelegramObservation.message_id).filter_by(source_id=source_id)
                .order_by(TelegramObservation.message_id).limit(1000).all()]


def existing_ids(ids: list[str]) -> set[str]:
    with SessionLocal() as db:
        return {cid for (cid,) in db.query(AcestreamChannel.id).filter(AcestreamChannel.id.in_(ids)).all()}


def remove(account_id: str, source_id: int | None = None) -> None:
    with SessionLocal() as db:
        query = db.query(TelegramSourceRow).filter_by(account_id=account_id)
        if source_id is not None:
            query = query.filter_by(id=source_id)
        for row in query.all():
            db.query(TelegramObservation).filter_by(source_id=row.id).delete()
            db.delete(row)
        db.commit()


def revision(source_id: int, message_id: int) -> str | None:
    with SessionLocal() as db:
        row = db.get(TelegramObservation, (source_id, message_id))
        return row.revision if row else None


def prune_observations() -> None:
    """Retention also applies to quiet, paused and disconnected accounts."""
    with SessionLocal() as db:
        db.query(TelegramObservation).filter(TelegramObservation.observed_at <
            datetime.now(timezone.utc) - timedelta(days=30)).delete(synchronize_session=False)
        db.commit()
