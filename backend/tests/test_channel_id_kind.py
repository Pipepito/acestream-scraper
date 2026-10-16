"""The 40 hex digits of an acestream id are of two kinds, and we remember which.

A content id is asked for as `?id=`, a torrent infohash as `?infohash=`. They
look identical and are not interchangeable: asking for one as the other comes
back as "not found", which reads like a dead stream rather than a wrong key.

`check_channel_status` already takes `identifier=`, so the engine's answer
already tells the two apart. These tests fix the part that was missing: that
the answer is written down, so the next probe does not have to guess.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.models import AcestreamChannel
from app.services.channel_status_service import ChannelStatusService


@pytest.fixture(autouse=True)
def isolated_queue(monkeypatch):
    from app.services.probe_queue import ProbeQueue
    monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0, outage_backoff=0))


@pytest.fixture
def probe(db_session):
    service = ChannelStatusService(db_session)
    service._get_engine_url = lambda: 'http://engine.test:6878'
    service._get_timeout = lambda: 0.015
    service._engine_ready = AsyncMock(return_value=True)
    service.channel_repository = MagicMock()
    return service


def found_response():
    return {'response': {
        'is_live': 1,
        'playback_url': 'http://127.0.0.1:6878/ace/r/hash/session',
        'stat_url': 'http://127.0.0.1:6878/ace/stat/hash/session',
        'command_url': 'http://127.0.0.1:6878/ace/cmd/hash/session',
    }, 'error': None}


@pytest.mark.asyncio
@pytest.mark.parametrize('identifier', ['id', 'infohash'])
async def test_a_recognised_id_records_which_parameter_worked(probe, identifier):
    probe._fetch_engine_response = AsyncMock(return_value=(200, found_response(), None))
    result = await probe.check_channel_status(
        AcestreamChannel(id='a' * 40, name='Example'), identifier=identifier)
    assert result['id_kind'] == identifier
    assert probe.channel_repository.update_channel_status.call_args.kwargs['id_kind'] == identifier


@pytest.mark.asyncio
async def test_a_not_found_lookup_records_nothing(probe):
    """The key was not recognised, so it says nothing about which kind it is."""
    probe._fetch_engine_response = AsyncMock(
        return_value=(200, {'error': 'content id not found'}, None))
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'))
    assert result['id_kind'] is None
    assert probe.channel_repository.update_channel_status.call_args.kwargs['id_kind'] is None


@pytest.mark.asyncio
async def test_an_unreadable_answer_records_nothing(probe):
    """A broken reply is not evidence either: it must not overwrite what is known."""
    probe._fetch_engine_response = AsyncMock(return_value=(500, None, 'boom'))
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'))
    assert result['id_kind'] is None


@pytest.mark.asyncio
async def test_what_is_already_known_survives_a_failed_probe(probe):
    """The channel was identified before; today's failure must not erase it."""
    probe._fetch_engine_response = AsyncMock(
        return_value=(200, {'error': 'content id not found'}, None))
    channel = AcestreamChannel(id='a' * 40, name='Example')
    channel.id_kind = 'infohash'
    result = await probe.check_channel_status(channel)
    assert result['id_kind'] == 'infohash'


def test_the_repository_never_clears_a_known_kind(db_session):
    """`update_channel_status(id_kind=None)` means "no news", not "forget it"."""
    from app.repositories.channel_repository import ChannelRepository
    repo = ChannelRepository(db_session)
    channel = AcestreamChannel(id='b' * 40, name='Example', id_kind='id')
    db_session.add(channel)
    db_session.commit()

    repo.update_channel_status('b' * 40, False, 'offline')
    assert repo.get_channel_by_id('b' * 40).id_kind == 'id'

    repo.update_channel_status('b' * 40, True, None, id_kind='infohash')
    assert repo.get_channel_by_id('b' * 40).id_kind == 'infohash'


@pytest.mark.parametrize('id_kind', [None, 'id', 'infohash'])
def test_channel_api_exposes_confirmed_kind(client, db_session, id_kind):
    channel = AcestreamChannel(id='c' * 40, name='Example', id_kind=id_kind)
    db_session.add(channel)
    db_session.commit()

    response = client.get(f'/api/v1/channels/{channel.id}')
    assert response.status_code == 200
    assert response.json()['id_kind'] == id_kind


def test_id_kind_migration_preserves_existing_channels(tmp_path):
    from sqlalchemy import create_engine, inspect, text
    from migration_test_utils import (
        database_url_for, downgrade_to_revision, upgrade_to_revision,
    )

    db_path = tmp_path / 'id-kind-upgrade.db'
    upgrade_to_revision(db_path, '20260915_1200')
    engine = create_engine(database_url_for(db_path))
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO acestream_channels (id, name) VALUES ('existing', 'Example')"
            ))

        upgrade_to_revision(db_path, '20260928_1200')
        with engine.begin() as connection:
            row = connection.execute(text(
                "SELECT name, id_kind FROM acestream_channels WHERE id = 'existing'"
            )).one()
            assert tuple(row) == ('Example', None)
            connection.execute(text(
                "UPDATE acestream_channels SET id_kind = 'infohash' WHERE id = 'existing'"
            ))

        downgrade_to_revision(db_path, '20260915_1200')
        assert 'id_kind' not in {
            column['name'] for column in inspect(engine).get_columns('acestream_channels')
        }
        with engine.connect() as connection:
            assert connection.execute(text(
                "SELECT name FROM acestream_channels WHERE id = 'existing'"
            )).scalar_one() == 'Example'
    finally:
        engine.dispose()
