"""A scrape must not un-hide a channel the user hid from the playlist."""
from __future__ import annotations

from app.models.models import AcestreamChannel
from app.repositories.channel_repository import ChannelRepository


def test_upsert_keeps_user_hidden_state(db_session):
    repo = ChannelRepository(db_session)
    cid = "f" * 40
    db_session.add(AcestreamChannel(id=cid, name="Old name", is_active=False, is_online=False))
    db_session.commit()

    repo.create_or_update_channel(cid, "New name", source_url="http://src.test/list.m3u", is_online=True)
    db_session.commit()

    channel = db_session.get(AcestreamChannel, cid)
    assert channel.name == "New name"
    assert channel.is_online is True
    assert channel.is_active is False, "scrape re-activated a hidden channel"

    created = repo.create_or_update_channel("e" * 40, "Brand new", source_url="http://src.test/list.m3u")
    db_session.commit()
    assert created.is_active is True
