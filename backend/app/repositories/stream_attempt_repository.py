"""DB-only access for per-attempt playback outcomes."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, List, Tuple

from sqlalchemy import case, func

from app.models.models import AcestreamChannel
from app.models.stream_attempts import StreamAttempt


class StreamAttemptRepository:
    def __init__(self, db):
        self.db = db

    def add(self, content_id: str, tv_channel_id: int | None, outcome: str, *, seconds: float,
            peers: int | None, speed_down: int | None, created_at: datetime) -> StreamAttempt:
        content_id = content_id.lower()
        stream = self.db.get(AcestreamChannel, content_id)
        sources = None
        if tv_channel_id is not None:
            sources = (self.db.query(func.count(AcestreamChannel.id))
                       .filter(AcestreamChannel.tv_channel_id == tv_channel_id,
                               AcestreamChannel.is_active.is_(True)).scalar())
        row = StreamAttempt(content_id=content_id, tv_channel_id=tv_channel_id, outcome=outcome,
                            seconds=max(0.0, float(seconds or 0.0)), peers=peers, speed_down=speed_down,
                            source_url=stream.source_url if stream is not None else None,
                            channel_sources=sources, created_at=created_at)
        self.db.add(row)
        self.db.commit()
        return row

    def update(self, row_id: int, outcome: str, *, seconds: float) -> StreamAttempt | None:
        """Rewrite the outcome and seconds of an attempt written while it played."""
        row = self.db.get(StreamAttempt, row_id)
        if row is None:
            return None
        row.outcome = outcome
        row.seconds = max(0.0, float(seconds or 0.0))
        self.db.commit()
        return row

    def prune(self, before: datetime) -> int:
        deleted = self.db.query(StreamAttempt).filter(StreamAttempt.created_at < before).delete(synchronize_session=False)
        self.db.commit()
        return deleted

    def attempts_since(self, content_ids: Iterable[str], since: datetime) -> List[Tuple[str, str, float, datetime]]:
        ids = sorted({cid.lower() for cid in content_ids})
        if not ids:
            return []
        return (self.db.query(StreamAttempt.content_id, StreamAttempt.outcome, StreamAttempt.seconds,
                              StreamAttempt.created_at)
                .filter(StreamAttempt.content_id.in_(ids), StreamAttempt.created_at >= since).all())

    def list_health(self, source_urls: Iterable[str]) -> Dict[str, Tuple[int, int]]:
        """Active sources per list and how many of them the last check found online."""
        urls = sorted({url for url in source_urls if url})
        if not urls:
            return {}
        rows = (self.db.query(AcestreamChannel.source_url, func.count(AcestreamChannel.id),
                              func.sum(case((AcestreamChannel.is_online.is_(True), 1), else_=0)))
                .filter(AcestreamChannel.source_url.in_(urls), AcestreamChannel.is_active.is_(True))
                .group_by(AcestreamChannel.source_url).all())
        return {url: (int(total), int(online or 0)) for url, total, online in rows}
