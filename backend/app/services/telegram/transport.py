"""The only MTProto boundary. Never send messages, join chats or fetch media."""
from app.services.telegram.errors import TelegramActionError

import logging
from typing import Any, Callable
from telethon import TelegramClient, events, functions, types, utils
from telethon.sessions import StringSession
from app.schemas.telegram import TelegramPeer
from app.services.telegram.extraction import Message

# Third-party debug logs can contain requests/session details. Operational status
# is translated explicitly by the manager, never by echoing upstream exceptions.
_log = logging.getLogger('telegram_private_transport')
_log.addHandler(logging.NullHandler())
_log.propagate = False
_log.setLevel(logging.CRITICAL + 1)


def normalize(message: Any, forum: bool = False) -> Message:
    if isinstance(message, types.MessageEmpty):
        return Message(id=message.id, deleted=True)
    forward = getattr(message, 'fwd_from', None)
    reply = getattr(message, 'reply_to', None)
    original = getattr(forward, 'from_id', None)
    links = []
    for entity, text in message.get_entities_text():
        if isinstance(entity, types.MessageEntityTextUrl):
            links.append((text, entity.url))
        elif isinstance(entity, types.MessageEntityUrl):
            links.append((text, text))
    topic_id = ((getattr(reply, 'reply_to_top_id', None) or getattr(reply, 'reply_to_msg_id', None))
                if getattr(reply, 'forum_topic', False) else 1 if forum else None)
    if isinstance(getattr(message, 'action', None), types.MessageActionTopicCreate):
        topic_id = message.id
    return Message(id=message.id, text=message.message or '',
        sender_id=str(message.sender_id) if message.sender_id is not None else None,
        topic_id=topic_id,
        forwarded=forward is not None,
        original_id=str(utils.get_peer_id(original)) if original else None,
        links=links[:101])


class Transport:
    def __init__(self, api_id: int, api_hash: str, session: str = '') -> None:
        # One retry: an account on another data centre answers PHONE_MIGRATE /
        # USER_MIGRATE, and Telethon re-sends the request only after switching.
        # Flood waits still raise at once (flood_sleep_threshold=0).
        self.client = TelegramClient(StringSession(session), api_id, api_hash,
            flood_sleep_threshold=0, request_retries=1, connection_retries=3,
            retry_delay=2, auto_reconnect=True, base_logger=_log,
            entity_cache_limit=1000)
        self.client.session.save_entities = False

    async def connect(self) -> None:
        await self.client.connect()

    async def disconnect(self) -> None:
        await self.client.disconnect()

    async def authorized(self) -> bool:
        return await self.client.is_user_authorized()

    def session(self) -> str:
        return self.client.session.save()

    async def send_code(self, phone: str) -> str:
        return (await self.client.send_code_request(phone)).phone_code_hash

    async def code(self, phone: str, code: str, phone_hash: str) -> Any:
        return await self.client.sign_in(phone=phone, code=code, phone_code_hash=phone_hash)

    async def password(self, password: str) -> Any:
        return await self.client.sign_in(password=password)

    async def me(self) -> Any:
        return await self.client.get_me()

    async def logout(self) -> None:
        if not await self.client.log_out():
            raise TelegramActionError('Telegram did not confirm revocation')

    def subscribe(self, callback: Callable[[str | None, list[int], bool], None]) -> None:
        async def changed(event: Any) -> None:
            if event.chat_id is not None:
                callback(str(event.chat_id), [event.id], False)
        async def deleted(event: Any) -> None:
            # Telegram omits chat identity for some private/basic-group deletes.
            # Reconciliation checks known message IDs in their selected chat.
            callback(str(event.chat_id) if event.chat_id is not None else None, event.deleted_ids, True)
        self.client.add_event_handler(changed, events.NewMessage())
        self.client.add_event_handler(changed, events.MessageEdited())
        self.client.add_event_handler(deleted, events.MessageDeleted())

    async def chats(self) -> list[TelegramPeer]:
        result = []
        async for dialog in self.client.iter_dialogs(limit=500):
            if (dialog.is_group or dialog.is_channel) and not getattr(dialog.entity, 'left', False):
                result.append(TelegramPeer(id=str(dialog.id), label=dialog.name or str(dialog.id),
                                          kind='channel' if dialog.is_channel else 'chat'))
        return result

    async def member(self, chat_id: str) -> tuple[Any, str]:
        # Resolve only joined dialogs. Arbitrary usernames/invite links cannot
        # turn this into a public-chat crawler or automatic join operation.
        async for dialog in self.client.iter_dialogs(limit=500):
            if str(dialog.id) != chat_id:
                continue
            entity = dialog.entity
            if not (dialog.is_group or dialog.is_channel) or getattr(entity, 'left', False) or getattr(entity, 'deactivated', False):
                break
            if isinstance(entity, types.Channel):
                participant = (await self.client(functions.channels.GetParticipantRequest(entity, 'me'))).participant
                if isinstance(participant, types.ChannelParticipantBanned):
                    raise TelegramActionError('Chat access lost')
            return entity, dialog.name or chat_id
        raise TelegramActionError('Chat access lost. Refresh joined chats and select a chat you belong to.')

    async def topics(self, entity: Any) -> list[TelegramPeer]:
        if not getattr(entity, 'forum', False):
            return []
        response = await self.client(functions.messages.GetForumTopicsRequest(
            entity, offset_date=None, offset_id=0, offset_topic=0, limit=100))
        return [TelegramPeer(id=str(topic.id), label=topic.title, kind='topic')
                for topic in response.topics if isinstance(topic, types.ForumTopic)]

    async def label(self, identity: str) -> str:
        try:
            entity = await self.client.get_entity(int(identity))
            return utils.get_display_name(entity)[:100] or identity
        except (ValueError, TypeError):
            return identity

    async def resolve(self, username: str) -> TelegramPeer:
        entity = await self.client.get_entity(username)
        if not isinstance(entity, (types.User, types.Chat, types.Channel)):
            raise TelegramActionError('Choose a Telegram user or channel identity')
        return TelegramPeer(id=str(utils.get_peer_id(entity)), label=utils.get_display_name(entity),
                            kind='user' if isinstance(entity, types.User) else 'channel' if isinstance(entity, types.Channel) else 'chat')

    @staticmethod
    def _thread(topic_id: int | None) -> dict:
        # Read a forum topic's own thread, so a quiet topic in a busy chat is not
        # crowded out by other topics. General (1) has no thread: it stays chat-wide.
        return {'reply_to': topic_id} if topic_id and topic_id != 1 else {}

    async def recent(self, entity: Any, limit: int, topic_id: int | None = None) -> list[Any]:
        return [message async for message in self.client.iter_messages(entity, limit=limit, **self._thread(topic_id))]

    async def after(self, entity: Any, cursor: int, limit: int = 10, topic_id: int | None = None) -> list[Any]:
        return [message async for message in self.client.iter_messages(
            entity, min_id=cursor, reverse=True, limit=limit, **self._thread(topic_id))]

    async def by_ids(self, entity: Any, ids: list[int]) -> list[Any]:
        return await self.client.get_messages(entity, ids=ids)
