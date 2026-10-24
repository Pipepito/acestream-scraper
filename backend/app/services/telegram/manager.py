"""One leased account, a bounded event queue, durable incremental progress.

Event notifications are hints: forward history is always read from the committed
cursor. Queue overflow/reconnect reconciles the retained message window. No DB
session survives an await. All upstream errors are translated into fixed copy.
"""
from app.services.telegram.errors import TelegramActionError

import asyncio
import hashlib
from contextlib import suppress
from typing import Any, Callable, TypeVar
from datetime import datetime, timedelta, timezone
import time
import uuid
from telethon import errors
from app.config.settings import get_settings
from app.repositories import telegram_repository as repo
from app.schemas.telegram import (TelegramStatus, TelegramSource, TelegramSourceConfig, TelegramSourceCreate, TelegramLogin, TelegramPreviewRequest,
                                  TelegramPreview, TelegramPreviewMessage)
from app.services.telegram.extraction import Message, preview_message
from app.services.telegram.transport import Transport, normalize
from app.services.telegram.vault import Vault


_T = TypeVar("_T")


async def threaded(function: Callable[..., _T], *args: Any) -> _T:
    task = asyncio.create_task(asyncio.to_thread(function, *args))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        # Finish a durable write before shutdown releases the session lease.
        with suppress(Exception):
            await task
        raise


class Manager:
    def __init__(self, transport_factory: Callable[..., Transport] = Transport) -> None:
        self.factory = transport_factory
        self.client: Transport | None = None
        self.vault: Vault | None = None
        self.account: dict[str, Any] | None = None
        self.task: asyncio.Task[None] | None = None
        self.lock = asyncio.Lock()
        self.queue = asyncio.Queue(maxsize=512)
        self.reconcile = set()
        self.pending = {}
        self.chat_ids = set()
        self.last_reconcile = 0.0
        self.last_prune = 0.0
        self.wake = asyncio.Event()
        self.state, self.message = 'disconnected', ''
        self.retry_at = None
        self.phone = self.phone_hash = None
        self.login_deadline = 0.0
        self.last_login_attempt = 0.0
        self.failures = 0
        self.suspended = False

    def status(self) -> TelegramStatus:
        configured = len(get_settings().TELEGRAM_ADMIN_TOKEN.get_secret_value()) >= 32 and bool(get_settings().TELEGRAM_KEY_FILE)
        return TelegramStatus(state=self.state if configured else 'disabled', message=self.message,
            account_label=(self.account or {}).get('label', ''), queue_size=self.queue.qsize(), retry_at=self.retry_at)

    async def _vault(self) -> Vault:
        if self.vault is None:
            vault = await threaded(Vault)
            try:
                await threaded(vault.acquire)
            except BaseException:
                vault.close()
                raise
            self.vault = vault
        return self.vault

    async def start(self) -> None:
        if self.task is None:
            # Lifespan can restart on a new event loop (startup recovery/tests).
            # asyncio primitives remember the loop of their first wait.
            self.lock = asyncio.Lock()
            self.wake = asyncio.Event()
            self.queue = asyncio.Queue(maxsize=512)
            self.task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
            self.task = None
        try:
            if self.client:
                await self.client.disconnect()
        finally:
            self.client = None
            self.phone = self.phone_hash = None
            self.account = None
            self.pending.clear()
            self.reconcile.clear()
            self.chat_ids.clear()
            while not self.queue.empty():
                self.queue.get_nowait()
            self.retry_at = None
            self.state, self.message = 'disconnected', ''
            self.suspended = False
            if self.vault:
                await threaded(self.vault.close)
                self.vault = None

    async def persist(self) -> None:
        self.account['session'] = self.client.session()
        await threaded(self.vault.save, self.account)

    async def resume(self) -> None:
        self.suspended = False
        if self.client:
            return
        vault = await self._vault()
        self.account = await threaded(vault.load)
        if not self.account:
            self.state = 'disconnected'
            return
        self.client = self.factory(self.account['api_id'], self.account['api_hash'], self.account['session'])
        try:
            await self.client.connect()
            if not await self.client.authorized():
                raise errors.AuthKeyUnregisteredError(None)
            self.client.subscribe(self.event)
            self.state, self.message = 'connected', ''
            self.reconcile.update(s.id for s in await self.sources())
        except BaseException:
            await self.client.disconnect()
            self.client = None
            raise

    def event(self, chat_id: str | None, ids: list[int], deleted: bool) -> None:
        if chat_id is None:
            self.reconcile.add('*')
            self.wake.set()
            return
        if chat_id not in self.chat_ids:
            return
        for mid in ids:
            try:
                self.queue.put_nowait((chat_id, mid, deleted))
            except asyncio.QueueFull:
                # Poll all enabled sources from their durable cursor and retained
                # revisions. No forward progress is ever advanced by a hint.
                self.reconcile.add('*')
                break
        self.wake.set()

    def require_connected(self) -> None:
        if not self.client or self.state != 'connected':
            raise TelegramActionError('Connect your Telegram account first')

    async def login(self, data: TelegramLogin) -> None:
        if self.account:
            raise TelegramActionError('Log out the existing account before connecting another')
        if time.monotonic() - self.last_login_attempt < 5:
            raise TelegramActionError('Wait a few seconds before requesting another code')
        self.last_login_attempt = time.monotonic()
        await self._vault()
        # Check disk even if the background task has not restored the session yet.
        saved = await threaded(self.vault.load)
        if saved:
            raise TelegramActionError('Reconnect or log out the saved account first')
        if self.client:
            await self.client.disconnect()
        self.client = self.factory(data.api_id, data.api_hash.get_secret_value())
        try:
            await self.client.connect()
            self.phone = data.phone.get_secret_value()
            self.phone_hash = await self.client.send_code(self.phone)
        except BaseException:
            self.phone = self.phone_hash = None
            await self.client.disconnect()
            self.client = None
            raise
        self.account = {'api_id': data.api_id, 'api_hash': data.api_hash.get_secret_value(), 'id': uuid.uuid4().hex}
        self.login_deadline = time.monotonic() + 300
        self.state, self.message = 'code_required', 'Enter the code sent by Telegram.'
        self.suspended = False

    async def authorize(self, value: str, password: bool = False) -> None:
        expected = 'password_required' if password else 'code_required'
        if self.state != expected or time.monotonic() > self.login_deadline:
            raise TelegramActionError('Authorization expired. Disconnect and start again.')
        try:
            if password:
                await self.client.password(value)
            else:
                await self.client.code(self.phone, value, self.phone_hash)
        except errors.SessionPasswordNeededError:
            self.phone = self.phone_hash = None
            self.state, self.message = 'password_required', 'Enter your Telegram two-step verification password.'
            return
        me = await self.client.me()
        self.account['label'] = (getattr(me, 'first_name', '') or 'Telegram account')[:100]
        self.account['user_id'] = str(me.id)
        self.phone = self.phone_hash = None
        await self.persist()
        self.client.subscribe(self.event)
        self.state, self.message = 'connected', ''
        self.wake.set()

    async def disconnect(self) -> None:
        if self.client:
            await self.client.disconnect()
            self.client = None
        if self.state in ('code_required', 'password_required'):
            self.account = None
        self.phone = self.phone_hash = None
        self.state, self.message, self.suspended = 'disconnected', 'Collection is stopped. Reconnect to catch up.', True

    async def logout(self) -> None:
        if not self.account:
            try:
                await self.resume()
            except (errors.AuthKeyUnregisteredError, errors.SessionRevokedError):
                pass
        if self.account and self.account.get('session'):
            try:
                if not self.client:
                    await self.resume()
                # Keep encrypted session if revocation fails so the operator can retry.
                await self.client.logout()
            except (errors.AuthKeyUnregisteredError, errors.SessionRevokedError):
                pass  # Telegram already revoked this authorization.
            await threaded(repo.remove, self.account['id'])
        await self.disconnect()
        if self.vault:
            await threaded(self.vault.remove)
        self.account = None
        self.pending.clear()
        self.reconcile.clear()
        while not self.queue.empty():
            self.queue.get_nowait()
        self.message = 'Account removed. Existing catalogue streams are preserved.'

    async def sources(self) -> list[TelegramSource]:
        sources = await threaded(repo.list_sources, self.account['id']) if self.account else []
        self.chat_ids = {s.chat_id for s in sources if s.enabled}
        return sources

    async def save_source(self, data: TelegramSourceConfig | TelegramSourceCreate, source_id: int | None = None) -> TelegramSource:
        self.require_connected()
        if source_id is not None and not data.enabled:
            snapshot = await threaded(repo.snapshot, source_id, self.account['id'])
            if snapshot is None:
                raise TelegramActionError('Source no longer exists')
            previous = snapshot[0]
            source = await threaded(repo.save_source, self.account['id'], data, previous.chat_label,
                                    previous.sender_labels, previous.cursor, source_id)
            await self.sources()
            return source
        entity, label = await self.client.member(data.chat_id)
        if data.topic_id is not None:
            topics = await self.client.topics(entity)
            if str(data.topic_id) not in {t.id for t in topics}:
                raise TelegramActionError('Topic is unavailable. Refresh the topic list.')
        labels = {}
        # Stable IDs may represent users or channels; display labels remain hints.
        for identity in data.sender_ids:
            labels[identity] = await self.client.label(identity)
        cursor = 0
        if source_id is None:
            recent = await self.client.recent(entity, max(1, data.history_count))
            if data.history_count:
                recent = [m for m in recent if not data.history_since or m.date >= data.history_since]
                cursor = min((m.id for m in recent), default=1) - 1
                if not recent:
                    head = await self.client.recent(entity, 1)
                    cursor = head[0].id if head else 0
            else:
                cursor = recent[0].id if recent else 0
        config = TelegramSourceConfig.model_validate(data.model_dump(include=set(TelegramSourceConfig.model_fields)))
        source = await threaded(repo.save_source, self.account['id'], config, label, labels, cursor, source_id)
        await self.sources()
        if source_id is not None:
            self.reconcile.add(source.id)
        self.wake.set()
        return source

    async def preview(self, request: TelegramPreviewRequest) -> TelegramPreview:
        self.require_connected()
        entity, _ = await self.client.member(request.source.chat_id)
        messages = await self.client.recent(entity, request.limit)
        results = []
        for raw in messages:
            msg = normalize(raw, forum=getattr(entity, 'forum', False))
            outcome, result = await threaded(preview_message, request.source, msg)
            known = await threaded(repo.existing_ids, [c.channel_id for c in result.channels])
            result.duplicate_count += len(known)
            results.append(TelegramPreviewMessage(message_id=msg.id, sender_id=msg.sender_id, outcome=outcome, result=result))
        return TelegramPreview(chat_id=request.source.chat_id, messages=results)

    async def process(self, source: TelegramSource, generation: int, message: Message, advance: bool) -> bool:
        config = TelegramSourceConfig.model_validate(source.model_dump(include=set(TelegramSourceConfig.model_fields)))
        revision = hashlib.sha256((message.revision() + config.model_dump_json()).encode()).hexdigest()
        previous = await threaded(repo.revision, source.id, message.id)
        if previous == revision and not advance:
            return True
        _, result = await threaded(preview_message, config, message)
        return await threaded(repo.record, source.id, self.account['id'], generation,
                                       message.id, revision, result, advance)

    async def scan(self, source_id: int, hints: list[tuple[str | None, int, bool]]) -> None:
        snap = await threaded(repo.snapshot, source_id, self.account['id'])
        if not snap or not snap[0].enabled:
            return
        source, generation = snap
        try:
            entity, _ = await self.client.member(source.chat_id)
        except (ValueError, errors.UserNotParticipantError, errors.ChannelPrivateError):
            await threaded(repo.set_status, source.id, 'access_lost', 'Chat access lost. Rejoin in Telegram, then scan again.')
            return
        # Reconcile persisted observations on restart/overflow; chunked network
        # reads avoid unbounded Telegram batches. No whole message history stored.
        pending = self.pending.setdefault(source.id, set())
        retained = set(await threaded(repo.observed_ids, source.id))
        pending.intersection_update(retained)
        pending.update(mid for chat, mid, _ in hints if chat == source.chat_id and mid in retained)
        if source.id in self.reconcile or '*' in self.reconcile:
            pending.update(retained)
            self.reconcile.discard(source.id)
        # At most 1000 retained IDs plus 512 event hints. Process ten per turn;
        # controls and other sources get the lock between these bounded batches.
        batch = sorted(pending)[:10]
        if batch:
            messages = await self.client.by_ids(entity, batch)
            for mid, raw in zip(batch, messages):
                message = normalize(raw, forum=getattr(entity, 'forum', False)) if raw else Message(id=mid, deleted=True)
                if not await self.process(source, generation, message, False):
                    return
                pending.discard(mid)
        if pending:
            self.wake.set()
        messages = await self.client.after(entity, source.cursor, 10)
        for raw in messages:
            if not await self.process(source, generation, normalize(raw, forum=getattr(entity, 'forum', False)), True):
                return
        await threaded(repo.set_status, source.id, 'catching_up' if len(messages) == 10 else 'reconciling' if pending else 'current')
        if len(messages) == 10:
            self.wake.set()

    def failure(self, exc: Exception) -> int:
        if isinstance(exc, TelegramActionError):
            self.message = str(exc)
            return 30
        messages = {
            errors.PhoneCodeInvalidError: 'The Telegram code is incorrect. Enter the latest code.',
            errors.PhoneCodeExpiredError: 'The Telegram code expired. Disconnect and request a new code.',
            errors.PasswordHashInvalidError: 'The Telegram two-step verification password is incorrect.',
            errors.PhoneNumberInvalidError: 'Enter a valid phone number including the country code.',
            errors.ApiIdInvalidError: 'Telegram rejected the API ID or hash. Check your registered application.',
        }
        for kind, message in messages.items():
            if isinstance(exc, kind):
                self.message = message
                return 5
        if isinstance(exc, errors.FloodWaitError):
            seconds = max(1, exc.seconds)
            self.retry_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
            self.message = 'Telegram rate limit. Collection resumes after the displayed retry time.'
            return seconds
        if isinstance(exc, (errors.AuthKeyUnregisteredError, errors.SessionRevokedError, errors.UserDeactivatedError)):
            self.state, self.message, self.suspended = 'authorization_expired', 'Telegram authorization expired. Log out and connect again.', True
        else:
            self.failures += 1
            self.message = 'Telegram operation failed. Check connection, access and settings, then retry.'
        return min(300, 5 * 2 ** min(self.failures, 6))

    async def run(self) -> None:
        delay = 1
        while True:
            try:
                try:
                    await asyncio.wait_for(self.wake.wait(), timeout=delay)
                except asyncio.TimeoutError:
                    pass
                self.wake.clear()
                if time.monotonic() - self.last_prune > 300:
                    await threaded(repo.prune_observations)
                    self.last_prune = time.monotonic()
                if len(get_settings().TELEGRAM_ADMIN_TOKEN.get_secret_value()) < 32 or not get_settings().TELEGRAM_KEY_FILE:
                    delay = 30
                    continue
                if self.retry_at and self.retry_at > datetime.now(timezone.utc):
                    delay = min(30, (self.retry_at - datetime.now(timezone.utc)).total_seconds())
                    continue
                self.retry_at = None
                async with self.lock:
                    if self.suspended:
                        continue
                    if self.state in ('code_required', 'password_required'):
                        if time.monotonic() > self.login_deadline:
                            await self.disconnect()
                            self.message = 'Authorization expired. Start again.'
                        continue
                    if not self.client:
                        await asyncio.wait_for(self.resume(), 30)
                    if not self.client:
                        delay = 30
                        continue
                    hints = []
                    while not self.queue.empty():
                        hints.append(self.queue.get_nowait())
                    if any(chat is None for chat, _, _ in hints):
                        self.reconcile.add('*')
                    sources = await self.sources()
                    if time.monotonic() - self.last_reconcile > 300:
                        self.reconcile.add('*')
                        self.last_reconcile = time.monotonic()
                # One source per lock acquisition allows control operations
                # between sources. Sources never hold the global maintenance FIFO.
                if '*' in self.reconcile:
                    self.reconcile.update(source.id for source in sources)
                    self.reconcile.discard('*')
                for source in sources:
                    async with self.lock:
                        if self.state != 'connected' or not self.client:
                            break
                        try:
                            async with asyncio.timeout(60):
                                await self.scan(source.id, hints)
                        except ValueError:
                            await threaded(repo.set_status, source.id, 'error', 'Extraction failed. Test the source recipe before retrying.')
                self.message = ''
                self.failures = 0
                delay = 10
                await asyncio.sleep(0.25)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                delay = self.failure(exc)
                if not self.retry_at:
                    self.retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                self.reconcile.add('*')


manager = Manager()
