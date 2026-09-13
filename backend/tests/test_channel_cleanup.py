"""The daily cleanup must not delete channels a user merely hid from the playlist."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.models import AcestreamChannel, TVChannel
from app.tasks.channel_cleanup_task import cleanup_hidden_channels


def _channel(db, cid: str, *, active: bool, seen_days_ago: int, tv: TVChannel | None = None) -> AcestreamChannel:
    channel = AcestreamChannel(
        id=cid * 40,
        name=cid,
        is_active=active,
        is_online=True,
        last_seen=datetime.now(timezone.utc) - timedelta(days=seen_days_ago),
        tv_channel_id=tv.id if tv else None,
    )
    db.add(channel)
    return channel


def test_only_hidden_stale_unassigned_channels_are_removed(db_session):
    tv = TVChannel(name="Linked TV")
    db_session.add(tv)
    db_session.flush()
    _channel(db_session, "a", active=False, seen_days_ago=2)          # hidden but fresh -> keep
    _channel(db_session, "b", active=False, seen_days_ago=45)         # hidden, stale, unassigned -> delete
    _channel(db_session, "c", active=False, seen_days_ago=45, tv=tv)  # hidden, stale, linked -> keep
    _channel(db_session, "d", active=True, seen_days_ago=400)         # visible -> keep
    db_session.commit()

    result = cleanup_hidden_channels(db_session, days=30)

    remaining = {c.name for c in db_session.query(AcestreamChannel).all()}
    assert remaining == {"a", "c", "d"}
    assert result["deleted"] == 1
    assert result["days"] == 30
