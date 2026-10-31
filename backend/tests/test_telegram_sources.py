from app.services.telegram import ingestion
"""No live Telegram account or credentials. Transport is synthetic throughout."""
import asyncio
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from datetime import datetime, timezone
import pytest
from cryptography.fernet import Fernet
from telethon import errors, types
from app.schemas.telegram import TelegramPeer, TelegramPreviewRequest, TelegramSourceConfig, TelegramSourceCreate, TelegramLogin
from app.schemas.extraction import ExtractionRecipe, RecipePreview
from app.services.telegram.extraction import Message, PAIR_RECIPE, preview_message, EMPTY
from app.services.telegram.transport import normalize, Transport
from app.services.telegram.manager import Manager
from app.repositories import telegram_repository as repo

IDS = ['6176281b9c46a5621a0e88524f8dc621f173b8e0', 'ac675c82d6dfd4a201532c18b42e48dacb7c32c6',
       '31c19ffb3472c289c5bbbbc174449c8ed0d19e38', 'e572a5178ff72eed7d1d751a18b4b3419699f370',
       'bb5a8bf7752e978460ee1710e5e8950a5c9e1f99', '0f0850a62ecdc4f79eec221cbebad01f3e0242bc']
NAMES = ['🇷🇺 Eurosport 2 HD', '🇩🇪Eurosport 2 HD', '🇪🇸M. Liga 🇻4️⃣'] + ['🇪🇸 Campeones 🇻4️⃣'] * 3
SAMPLE = '7raul:\n' + '\n\n'.join(f'{name}\n{cid}' for name, cid in zip(NAMES, IDS))


def config(**kwargs):
    return TelegramSourceConfig(name='Sports', chat_id='-100123', **kwargs)


@pytest.mark.parametrize('newline', ['\n', '\r\n'])
@pytest.mark.parametrize('custom', [False, True])
def test_representative_pairs_and_promotions(newline, custom):
    source = config(recipe=ExtractionRecipe.model_validate(PAIR_RECIPE) if custom else None)
    sample = ('Join us!\nhttps://example.com/' + 'f'*40 + '\n\n' + SAMPLE + '\nThanks!').replace('\n', newline)
    outcome, result = preview_message(source, Message(1, sample))
    assert outcome == 'matched'
    assert [c.channel_id for c in result.channels] == IDS
    assert [c.name for c in result.channels] == NAMES


@pytest.mark.parametrize('kwargs,message,reason', [
    ({'sender_ids': ['123']}, Message(1, SAMPLE, sender_id='-100123'), 'sender filtered'),
    ({'sender_ids': ['123']}, Message(1, SAMPLE, sender_id=None), 'sender filtered'),
    ({'sender_ids': ['123'], 'sender_rule': 'original'}, Message(1, SAMPLE, sender_id='123', forwarded=True), 'sender filtered'),
    ({'include_forwards': False}, Message(1, SAMPLE, forwarded=True), 'forward filtered'),
    ({'topic_id': 7}, Message(1, SAMPLE, topic_id=8), 'topic filtered'),
    ({'include': 'football'}, Message(1, SAMPLE), 'message filtered'),
    ({'exclude': 'EUROSPORT'}, Message(1, SAMPLE), 'message filtered'),
    ({'include': '^football', 'filter_mode': 'regex'}, Message(1, SAMPLE), 'message filtered'),
])
def test_filters_run_before_extraction(kwargs, message, reason):
    outcome, result = preview_message(config(**kwargs), message)
    assert outcome == reason and not result.channels


def test_forward_identity_and_link_entities():
    msg = Message(1, 'A caption', sender_id='456', original_id='123', forwarded=True,
                  links=[('🇪🇸 Sports', 'acestream://' + IDS[0]), ('unrelated', 'https://example.com/' + IDS[1])])
    outcome, result = preview_message(config(sender_ids=['123'], sender_rule='original'), msg)
    assert outcome == 'matched' and result.channels[0].name == '🇪🇸 Sports'
    assert len(result.channels) == 1
    assert preview_message(config(sender_ids=['123']), msg)[0] == 'sender filtered'


def test_share_links_with_a_content_id_are_recognised():
    """AceStream's own share links read acestream:?content_id=<id>, often with
    an infohash after it. Seen in a real account (29-10); they gave no match."""
    text = ('🇪🇸 Liga Hypermotion\nacestream:?content_id=' + IDS[0] + '&infohash=' + 'c' * 40 + '\n\n'
            'Copa\nacestream://?content_id=' + IDS[1])
    outcome, result = preview_message(config(), Message(1, text))
    assert outcome == 'matched'
    assert [(c.name, c.channel_id) for c in result.channels] == [('🇪🇸 Liga Hypermotion', IDS[0]), ('Copa', IDS[1])]
    msg = Message(2, 'See below', links=[('🇪🇸 Sports', 'acestream:?content_id=' + IDS[2])])
    assert [(c.name, c.channel_id) for c in preview_message(config(), msg)[1].channels] == [('🇪🇸 Sports', IDS[2])]
    # An infohash alone is a different key, and the bare-ID switch still applies.
    assert not preview_message(config(), Message(3, 'Only\nacestream:?infohash=' + IDS[3]))[1].channels


def test_chatter_malformed_ids_duplicates_and_bare_switch():
    assert preview_message(config(), Message(1, 'No streams here'))[0] == 'no match'
    assert not preview_message(config(), Message(1, 'Wrong\n' + 'a'*41))[1].channels
    assert not preview_message(config(bare_ids=False), Message(1, SAMPLE))[1].channels
    result = preview_message(config(), Message(1, SAMPLE + '\n' + SAMPLE))[1]
    assert len(result.channels) == 6 and result.duplicate_count == 6


def test_filter_timeout_is_isolated_and_releases_capacity():
    with pytest.raises(ValueError, match='time limit|Extraction failed'):
        preview_message(config(include='(a+)+$', filter_mode='regex'), Message(1, 'a'*100 + '!'))
    assert preview_message(config(), Message(1, SAMPLE))[1].channels


def test_telethon_normalization_never_trusts_signature():
    raw = types.Message(id=42, peer_id=types.PeerChannel(123), date=datetime.now(timezone.utc),
        message=SAMPLE, from_id=types.PeerChannel(123), post_author='123',
        fwd_from=types.MessageFwdHeader(date=datetime.now(timezone.utc), from_name='123'),
        reply_to=types.MessageReplyHeader(reply_to_msg_id=9, forum_topic=True))
    msg = normalize(raw)
    assert msg.sender_id == '-1000000000123' and msg.original_id is None and msg.topic_id == 9


def test_additive_replay_edit_delete_and_manual_ownership(alembic_backend_runtime):
    from app.models.models import AcestreamChannel
    from app.models.telegram import TelegramObservation
    source = repo.save_source('account', config(), 'Sports chat', {}, 0)
    _, generation = repo.snapshot(source.id, 'account')
    result = preview_message(config(), Message(1, SAMPLE))[1]
    assert ingestion.record(source.id, 'account', generation, 1, 'one', result, True)
    assert ingestion.record(source.id, 'account', generation, 1, 'one', result, True)
    with alembic_backend_runtime.SessionLocal() as db:
        assert db.query(AcestreamChannel).count() == 6
        channel = db.get(AcestreamChannel, IDS[0]); channel.name = 'Manual'; channel.is_active = False
        db.commit()
    assert ingestion.record(source.id, 'account', generation, 1, 'edit', result, False)
    assert ingestion.record(source.id, 'account', generation, 1, 'delete', RecipePreview(**EMPTY), False)
    with alembic_backend_runtime.SessionLocal() as db:
        assert db.query(AcestreamChannel).count() == 6
        assert db.get(AcestreamChannel, IDS[0]).name == 'Manual'
        assert db.get(AcestreamChannel, IDS[0]).is_active is False
        assert db.get(AcestreamChannel, IDS[0]).is_online is None
        assert db.query(TelegramObservation).count() == 1
        assert db.get(TelegramObservation, (source.id, 1)).channel_ids == []
    assert repo.list_sources('account')[0].imported_count == 6
    repo.save_source('account', config(enabled=False), 'Sports', {}, 0, source.id)
    assert not ingestion.record(source.id, 'account', generation, 2, 'stale', result, True)
    assert repo.list_sources('account')[0].cursor == 1
    repo.remove('account')
    with alembic_backend_runtime.SessionLocal() as db:
        assert db.query(AcestreamChannel).count() == 6
        assert db.query(TelegramObservation).count() == 0


@pytest.fixture
def private_settings(tmp_path, monkeypatch):
    from app.config.settings import get_settings
    monkeypatch.setattr('app.repositories.startup_recovery.database_path', lambda: tmp_path / 'config' / 'scraper.db')
    key = tmp_path / 'key'; key.write_bytes(Fernet.generate_key()); key.chmod(0o600)
    root = tmp_path / 'sessions'
    monkeypatch.setenv('TELEGRAM_KEY_FILE', str(key))
    monkeypatch.setenv('TELEGRAM_SESSION_DIR', str(root))
    monkeypatch.setenv('TELEGRAM_ADMIN_TOKEN', 'admin-' + 'x'*40)
    get_settings.cache_clear()
    yield key, root
    get_settings.cache_clear()


def test_vault_encryption_permissions_lock_and_recovery(private_settings):
    from app.services.telegram.vault import Vault
    key, root = private_settings
    vault = Vault(); vault.acquire()
    data = {'session': 'session-secret', 'api_hash': 'hash-secret'}
    vault.save(data)
    assert vault.load() == data
    assert b'session-secret' not in (root / 'account.enc').read_bytes()
    assert (root / 'account.enc').stat().st_mode & 0o077 == 0
    other = Vault()
    with pytest.raises(ValueError, match='Another process'):
        other.acquire()
    vault.close(); other.acquire(); assert other.load() == data; other.close()
    key.chmod(0o644)
    with pytest.raises(ValueError, match='0600'):
        Vault()


def test_vault_loads_account_encrypted_before_cryptography_upgrade(private_settings):
    """A synthetic cryptography 47 token stays readable with the security update."""
    import base64
    from app.services.telegram.vault import Vault

    key, root = private_settings
    key.write_bytes(base64.urlsafe_b64encode(bytes(range(32))))
    vault = Vault()
    token = (
        b"gAAAAABlU_EANzzHlQJI9VE4YgUCePSwzGT6yCqvpWKiff5IRUDQyyRRi-xd9x5C5scE"
        b"DeMq9H_h7qhXBou_Rm198NIGg-toYd341l9io2jWCB_Btpb45Sl56ifN9jiP-E_I1wgbb"
        b"EgTvOfsQeI46yb77tTDNkEMyyc6OblLSja3wR9PiAjODY0="
    )
    vault.path.write_bytes(token)
    vault.path.chmod(0o600)
    expected = {"session": "synthetic-upgrade-fixture", "api_hash": "synthetic"}
    assert vault.load() == expected
    vault.save(expected)
    assert Vault().load() == expected


@pytest.mark.asyncio
async def test_admin_requires_explicit_token_transport_and_same_origin(private_settings):
    from starlette.requests import Request
    from fastapi import HTTPException
    from app.api.endpoints.telegram import require_telegram_admin
    def request(headers=(), scheme='http', peer='127.0.0.1', host='localhost'):
        return Request({'type':'http','method':'GET','path':'/api/v1/telegram/status','scheme':scheme,
            'query_string':b'', 'client':(peer, 123), 'server':('localhost',80),
            'headers':[(b'host',host.encode()), *headers]})
    token = [(b'x-telegram-admin', b'admin-' + b'x'*40)]
    with pytest.raises(HTTPException) as missing:
        await require_telegram_admin(request())
    assert missing.value.status_code == 403
    await require_telegram_admin(request(token))
    with pytest.raises(HTTPException):
        await require_telegram_admin(request(token, peer='192.0.2.1'))
    await require_telegram_admin(request(token, scheme='https', peer='192.0.2.1'))
    with pytest.raises(HTTPException):
        await require_telegram_admin(request(token + [(b'origin', b'https://evil.invalid')], scheme='https'))


class FakeTransport:
    def __init__(self, *args):
        self.closed = False
        self.revoked = False
        self.messages = []
        self.need_password = False
        self.lost_access = False
    async def connect(self): pass
    async def disconnect(self): self.closed = True
    async def authorized(self): return True
    def session(self): return 'encrypted-session-payload'
    def subscribe(self, callback): self.callback = callback
    async def send_code(self, phone): return 'temporary-code-hash'
    async def code(self, *args):
        if self.need_password: raise errors.SessionPasswordNeededError(None)
    async def password(self, value): pass
    async def me(self): return SimpleNamespace(id=123, first_name='Test account')
    async def logout(self): self.revoked = True
    async def member(self, chat):
        if self.lost_access: raise ValueError('lost')
        return chat, 'Sports chat'
    async def label(self, identity): return 'Test sender'
    async def topics(self, entity): return [TelegramPeer(id='7', label='Links', kind='topic')]
    def _in(self, m, topic_id):
        # Like Telegram's GetReplies: a topic other than General only returns its own thread.
        return not topic_id or topic_id == 1 or normalize(m).topic_id == topic_id
    async def recent(self, entity, limit, topic_id=None):
        return [m for m in reversed(self.messages) if self._in(m, topic_id)][:limit]
    async def after(self, entity, cursor, limit, topic_id=None):
        return [m for m in self.messages if m.id > cursor and self._in(m, topic_id)][:limit]
    async def by_ids(self, entity, ids): return [next((m for m in self.messages if m.id == mid), None) for mid in ids]


def raw(mid, text=SAMPLE):
    return types.Message(id=mid, peer_id=types.PeerChannel(123), from_id=types.PeerUser(123),
                         message=text, date=datetime.now(timezone.utc))


@pytest.mark.asyncio
async def test_login_restart_sources_pause_replay_and_logout(alembic_backend_runtime, private_settings):
    manager = Manager(FakeTransport)
    await manager.login(TelegramLogin(api_id=12345, api_hash='a'*32, phone='+123456789'))
    manager.client.need_password = True
    await manager.authorize('12345')
    assert manager.state == 'password_required' and manager.phone is None
    await manager.authorize('password', password=True)
    assert manager.state == 'connected'
    client = manager.client
    client.messages = [raw(1)]
    source = await manager.save_source(TelegramSourceCreate(name='Sports', chat_id='-100123'))
    assert source.cursor == 1  # Explicit default: new messages only.
    client.messages.append(raw(2))
    await manager.scan(source.id, [])
    assert (await manager.sources())[0].cursor == 2
    source = await manager.save_source(config(enabled=False), source.id)
    client.messages.append(raw(3))
    await manager.scan(source.id, [])
    assert (await manager.sources())[0].cursor == 2
    await manager.save_source(config(), source.id)
    await manager.scan(source.id, [])
    assert (await manager.sources())[0].cursor == 3
    await manager.stop()
    restored = Manager(FakeTransport)
    await restored.resume()
    assert restored.state == 'connected'
    assert (await restored.sources())[0].cursor == 3
    client = restored.client
    await restored.logout()
    assert client.revoked and await restored.sources() == []
    assert not (private_settings[1] / 'account.enc').exists()
    await restored.stop()


@pytest.mark.asyncio
async def test_membership_failure_queue_bounds_flood_and_revision_retry(alembic_backend_runtime, private_settings):
    manager = Manager(FakeTransport)
    await manager.login(TelegramLogin(api_id=12345, api_hash='a'*32, phone='+123456789'))
    await manager.authorize('12345')
    source = await manager.save_source(TelegramSourceCreate(name='Sports', chat_id='-100123'))
    manager.event('-999', range(1000), False)
    assert manager.queue.qsize() == 0
    manager.event('-100123', range(1000), False)
    assert manager.queue.qsize() == 512 and '*' in manager.reconcile
    manager.client.lost_access = True
    await manager.scan(source.id, [])
    assert (await manager.sources())[0].state == 'access_lost'
    assert (await manager.sources())[0].cursor == 0
    manager.failure(errors.FloodWaitError(None, capture=123))
    assert manager.retry_at > datetime.now(timezone.utc)
    manager.client.lost_access = False
    manager.client.messages = [raw(1)]
    await manager.scan(source.id, [])
    manager.client.messages = [raw(1, 'Edited chatter')]
    manager.reconcile.add(source.id)
    await manager.scan(source.id, [])
    from app.models.telegram import TelegramObservation
    with alembic_backend_runtime.SessionLocal() as db:
        assert db.get(TelegramObservation, (source.id, 1)).channel_ids == []
    await manager.stop()


def test_migration_upgrade_downgrade_preserves_existing_streams(tmp_path):
    from migration_test_utils import current_head_revision, upgrade_to_revision, upgrade_to_head, downgrade_to_revision, database_url_for
    from sqlalchemy import create_engine, text, inspect
    path = tmp_path / 'migration.db'
    upgrade_to_revision(path, '20261023_1400')
    engine = create_engine(database_url_for(path))
    try:
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO acestream_channels (id, name) VALUES (:id, 'Manual')"), {'id': IDS[0]})
            connection.execute(text("INSERT INTO w3u_catalogues (name, revision, snapshot, selected_branches, mode, refresh_enabled, updated_at) VALUES ('Saved catalogue', 3, '{}', '[]', 'compatible', 0, '2026-10-23')"))
            connection.execute(text("INSERT INTO sporting_events (id, owner_id, revision, fields, followed, archived) VALUES ('match', 'source', 2, '{}', 1, 0)"))
        upgrade_to_head(path)
        assert {'telegram_sources', 'telegram_observations'} <= set(inspect(engine).get_table_names())
        with engine.connect() as connection:
            assert connection.execute(text('SELECT version_num FROM alembic_version')).scalars().all() == [current_head_revision()]
        downgrade_to_revision(path, '20261023_1400')
        assert not {'telegram_sources', 'telegram_observations'} & set(inspect(engine).get_table_names())
        with engine.connect() as connection:
            assert connection.execute(text('SELECT name FROM acestream_channels')).scalar() == 'Manual'
            assert connection.execute(text('SELECT name, revision FROM w3u_catalogues')).one() == ('Saved catalogue', 3)
            assert connection.execute(text('SELECT id, followed FROM sporting_events')).one() == ('match', 1)
            assert connection.execute(text('SELECT version_num FROM alembic_version')).scalar() == '20261023_1400'
        upgrade_to_head(path)
        assert {'telegram_sources', 'telegram_observations'} <= set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_private_routes_never_echo_secrets_and_preview_never_writes(alembic_backend_runtime, private_settings, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api.endpoints import telegram
    from app.models.models import AcestreamChannel
    service = Manager(FakeTransport)
    monkeypatch.setattr(telegram, 'manager', service)
    app = FastAPI(); app.include_router(telegram.router, prefix='/api/v1/telegram')
    headers = {'X-Telegram-Admin': 'admin-' + 'x'*40}
    with TestClient(app, base_url='https://testserver') as client:
        invalid = client.post('/api/v1/telegram/login', headers=headers,
            json={'api_id': 'secret-invalid', 'api_hash': 'never-echo-this', 'phone': '+12345'})
        assert invalid.status_code == 422 and 'never-echo-this' not in invalid.text and 'secret-invalid' not in invalid.text
        assert client.get('/api/v1/telegram/status').status_code == 403
        disconnected_scan = client.post('/api/v1/telegram/sources/1/scan', headers=headers)
        assert disconnected_scan.status_code == 400
        assert disconnected_scan.json()['detail'] == 'Connect your Telegram account first'
        assert client.post('/api/v1/telegram/login', headers=headers,
            json={'api_id':12345, 'api_hash':'a'*32, 'phone':'+123456789'}).status_code == 200
        assert client.post('/api/v1/telegram/code', headers=headers, json={'code':'12345'}).status_code == 200
        service.client.messages = [raw(1)]
        preview = client.post('/api/v1/telegram/preview', headers=headers, json={'source':config().model_dump(), 'limit':10})
        assert preview.status_code == 200 and len(preview.json()['messages'][0]['result']['channels']) == 6
        assert preview.headers['cache-control'] == 'no-store'
        state = client.get('/api/v1/telegram/status', headers=headers)
        assert 'encrypted-session' not in state.text and 'a'*32 not in state.text and '+123456789' not in state.text
        with alembic_backend_runtime.SessionLocal() as db:
            assert db.query(AcestreamChannel).count() == 0
        assert client.delete('/api/v1/telegram/account', headers=headers).status_code == 200
    if service.vault:
        service.vault.close()


def test_observation_retention_is_bounded(alembic_backend_runtime):
    from app.models.telegram import TelegramObservation
    from datetime import timedelta
    source = repo.save_source('account', config(), 'Sports', {}, 0)
    _, generation = repo.snapshot(source.id, 'account')
    now = datetime.now(timezone.utc)
    with alembic_backend_runtime.SessionLocal() as db:
        db.add_all([TelegramObservation(source_id=source.id, message_id=mid, revision='old', channel_ids=[],
            observed_at=now - timedelta(days=31) if mid == 1 else now) for mid in range(1, 1003)])
        db.commit()
    ingestion.record(source.id, 'account', generation, 1003, 'new', RecipePreview(**EMPTY), True)
    with alembic_backend_runtime.SessionLocal() as db:
        assert db.query(TelegramObservation).count() == 1000
        assert db.get(TelegramObservation, (source.id, 1)) is None
        assert db.get(TelegramObservation, (source.id, 1003)) is not None


@pytest.mark.asyncio
async def test_rule_changes_reprocess_retained_messages_and_failed_writes_do_not_advance(alembic_backend_runtime, private_settings, monkeypatch):
    manager = Manager(FakeTransport)
    await manager.login(TelegramLogin(api_id=12345, api_hash='a'*32, phone='+123456789'))
    await manager.authorize('12345')
    source = await manager.save_source(TelegramSourceCreate(name='Sports', chat_id='-100123', include='not present'))
    manager.client.messages = [raw(1)]
    await manager.scan(source.id, [])
    assert (await manager.sources())[0].imported_count == 0
    await manager.save_source(config(), source.id)
    await manager.scan(source.id, [])
    assert (await manager.sources())[0].imported_count == 6
    manager.client.messages.append(raw(2))
    with monkeypatch.context() as patch:
        patch.setattr(ingestion, 'record', lambda *args: (_ for _ in ()).throw(RuntimeError('disk full')))
        with pytest.raises(RuntimeError):
            await manager.scan(source.id, [])
    assert (await manager.sources())[0].cursor == 1
    await manager.scan(source.id, [])
    assert (await manager.sources())[0].cursor == 2
    await manager.stop()


@pytest.mark.asyncio
async def test_disconnect_retains_session_and_expired_logout_removes_it(alembic_backend_runtime, private_settings):
    manager = Manager(FakeTransport)
    await manager.login(TelegramLogin(api_id=12345, api_hash='a'*32, phone='+123456789'))
    await manager.authorize('12345')
    await manager.disconnect()
    assert manager.suspended and (private_settings[1] / 'account.enc').exists()
    await manager.resume()
    manager.client.logout = AsyncMock(side_effect=errors.SessionRevokedError(None))
    await manager.logout()
    assert not (private_settings[1] / 'account.enc').exists()
    await manager.stop()


def test_browser_fixture_matches_server_preset():
    fixture = json.loads((Path(__file__).parents[2] / 'frontend/src/recipes/telegram.fixture.json').read_text())
    assert fixture['recipe'] == ExtractionRecipe.model_validate(PAIR_RECIPE).model_dump()
    result = preview_message(config(recipe=ExtractionRecipe.model_validate(fixture['recipe'])), Message(1, fixture['sample']))[1]
    assert [c.channel_id for c in result.channels] == IDS


def test_consumer_lifespan_can_restart_on_another_event_loop():
    service = Manager(FakeTransport)
    async def lifespan():
        await service.start()
        await asyncio.sleep(0.02)
        await service.stop()
    asyncio.run(lifespan())
    asyncio.run(lifespan())
    assert service.task is None


@pytest.mark.asyncio
async def test_login_code_follows_the_account_to_its_data_centre():
    """A new session starts on Telegram's default data centre. An account
    that lives elsewhere gets PHONE_MIGRATE_X for auth.sendCode; Telethon
    switches DC and must send the request again there. With no retry left it
    raised ValueError("Request was unsuccessful 1 time(s)"), shown as the
    generic "Telegram action could not complete". Seen with a real Spanish
    account (28-10); with one retry the code arrived at once."""
    transport = Transport(12345, '0' * 32)
    client = transport.client
    loop = asyncio.get_running_loop()
    answers = [errors.PhoneMigrateError(request=None, capture=4),
               types.auth.SentCode(type=types.auth.SentCodeTypeApp(length=5), phone_code_hash='code-hash')]
    sent = []

    def send(request, ordered=False):
        sent.append(type(request).__name__)
        future = loop.create_future()
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            future.set_exception(answer)
        else:
            future.set_result(answer)
        return future

    client._sender = SimpleNamespace(send=send)
    client._switch_dc = AsyncMock()
    client.is_user_authorized = AsyncMock(return_value=False)
    assert await transport.send_code('+34600000000') == 'code-hash'
    client._switch_dc.assert_awaited_once_with(4)
    assert sent == ['SendCodeRequest', 'SendCodeRequest']


def in_topic(mid, topic, text=SAMPLE):
    return types.Message(id=mid, peer_id=types.PeerChannel(123), from_id=types.PeerUser(123), message=text,
                         date=datetime.now(timezone.utc),
                         reply_to=types.MessageReplyHeader(reply_to_msg_id=topic, forum_topic=True))


@pytest.mark.asyncio
async def test_topic_preview_and_history_read_inside_the_topic(alembic_backend_runtime, private_settings):
    """Forum channels seen with a real account (29-10) post links in quiet
    topics while other topics are busy. Reading the last N messages of the
    whole chat and filtering afterwards left 27-30 of 30 as "topic
    filtered", so a topic preview or bounded history import found nothing."""
    manager = Manager(FakeTransport)
    await manager.login(TelegramLogin(api_id=12345, api_hash='a'*32, phone='+123456789'))
    await manager.authorize('12345')
    client = manager.client
    client.messages = [in_topic(1, 7)] + [in_topic(mid, 8, 'chatter') for mid in range(2, 42)]
    source = config(topic_id=7)
    preview = await manager.preview(TelegramPreviewRequest(source=source, limit=10))
    assert [m.message_id for m in preview.messages] == [1]
    assert preview.messages[0].outcome == 'matched'
    saved = await manager.save_source(TelegramSourceCreate(**source.model_dump(), history_count=10))
    assert saved.cursor == 0
    client.messages.append(in_topic(42, 8, 'more chatter'))
    await manager.scan(saved.id, [])
    assert (await manager.sources())[0].cursor == 1
    assert set(repo.existing_ids(IDS)) == set(IDS)
    await manager.stop()
