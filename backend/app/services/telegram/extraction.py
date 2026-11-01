"""Transport-neutral messages and shared bounded extraction/filtering."""
from dataclasses import dataclass, field, asdict
import hashlib
import json
import re
from app.schemas.extraction import ExtractionRecipe, RecipePreview
from app.schemas.telegram import TelegramSourceConfig

MAX_MESSAGE_BYTES = 64 * 1024
EMPTY = {'channels': [], 'record_count': 0, 'invalid_count': 0, 'duplicate_count': 0, 'issues': []}
PAIR_RECIPE = {
    'schema_version': 1, 'name': 'Telegram name and ID pairs', 'version': '1.0.0',
    'mode': 'regex', 'flags': 'im',
    'records': r'^[^\r\n]+\r?\n[ \t]*(?:acestream://)?[0-9a-f]{40}[ \t]*(?=\r?$)',
    'fields': {'name': {'pattern': r'^([^\r\n]+)'},
               'id': {'pattern': r'\r?\n[ \t]*(?:acestream://)?([0-9a-f]{40})[ \t]*(?=\r?$)'}}
}


@dataclass
class Message:
    id: int
    text: str = ''
    sender_id: str | None = None
    topic_id: int | None = None
    forwarded: bool = False
    original_id: str | None = None
    links: list[tuple[str, str]] = field(default_factory=list)
    deleted: bool = False

    def revision(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def worker_extract(config: TelegramSourceConfig, message: Message) -> dict:
    """Only called in the disposable recipe process (including user regex)."""
    from app.services.recipe_worker import extract
    def skipped(reason):
        return {'outcome': reason, 'result': dict(EMPTY)}
    if message.deleted:
        return skipped('deleted')
    if len(message.text.encode()) > MAX_MESSAGE_BYTES or len(message.links) > 100 or any(len(label) > 2048 or len(url) > 2048 for label, url in message.links):
        raise ValueError('Message is too large')
    if config.topic_id is not None and message.topic_id != config.topic_id:
        return skipped('topic filtered')
    if message.forwarded and not config.include_forwards:
        return skipped('forward filtered')
    identity = message.original_id if config.sender_rule == 'original' and message.forwarded else message.sender_id
    if config.sender_ids and (identity is None or identity not in config.sender_ids):
        return skipped('sender filtered')
    for value, include in [(config.include, True), (config.exclude, False)]:
        if value:
            match = bool(re.search(value, message.text, re.I | re.M)) if config.filter_mode == 'regex' else value.casefold() in message.text.casefold()
            if match != include:
                return skipped('message filtered')
    # Link entity labels become local name/ID records. No unrelated URL is fetched.
    entity_records = []
    for label, url in message.links:
        url = share_link(url)
        if re.fullmatch(r'acestream://[0-9a-fA-F]{40}', url):
            entity_records.append(f'{label[:200] or url[12:]}\n{url}')
    sample = share_link(message.text) + ('\n' + '\n'.join(entity_records) if entity_records else '')
    if config.recipe:
        result = extract(config.recipe, sample)
    else:
        recipe = ExtractionRecipe.model_validate(PAIR_RECIPE)
        if not config.bare_ids:
            recipe.records = recipe.records.replace('(?:acestream://)?', 'acestream://')
        # Hashes in HTTP paths, query strings and promotional URLs never become IDs.
        safe = re.sub(r'https?://\S+', '', sample, flags=re.I)
        result = extract(recipe, safe)
        seen = {item['channel_id'] for item in result['channels']}
        for match in re.finditer(r'(?<![\w/=?&])acestream://([0-9a-f]{40})(?![a-z0-9/_?=&])', safe, re.I):
            cid = match.group(1).lower()
            if cid not in seen:
                seen.add(cid)
                result['channels'].append({'channel_id': cid, 'name': cid, 'metadata': {}})
                result['record_count'] += 1
    return {'outcome': 'matched' if result['channels'] else 'no match', 'result': result}


# AceStream's share links: acestream:?content_id=<id>[&infohash=...]. An
# infohash alone is a different key and is left alone.
_SHARE_LINK = re.compile(r'acestream:(?://)?\?(?:[^\s?#]*&)?content_id=([0-9a-fA-F]{40})(?:&[^\s#]*)?', re.I)


def share_link(text: str) -> str:
    return _SHARE_LINK.sub(lambda m: 'acestream://' + m.group(1).lower(), text)


def preview_message(config: TelegramSourceConfig, message: Message) -> tuple[str, RecipePreview]:
    from app.services.extraction_service import run_extraction_worker
    result = run_extraction_worker({'telegram': {'source': config.model_dump(mode='json'), 'message': asdict(message)}})
    return result['outcome'], RecipePreview.model_validate(result['result'])
