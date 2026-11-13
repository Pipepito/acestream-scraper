"""Which input a stored stream ID addresses, and what a valid stream ID looks like."""
import re
from typing import Literal

HTTP_PREFIX = 'url:'

# The shapes of stored stream IDs. Schemas that need a pydantic ``pattern``
# anchor these with ^...$; code checks them with the helpers below.
ACESTREAM_ID_PATTERN = r'[0-9a-fA-F]{40}'
HTTP_ID_PATTERN = r'url:[0-9a-f]{40}'
STREAM_ID_PATTERN = rf'(?:url:)?{ACESTREAM_ID_PATTERN}'

StreamKind = Literal['http', 'acestream']


def stream_kind(content_id: str) -> StreamKind:
    """``url:`` IDs are HTTP/broadcaster links; every other ID goes to the engine."""
    return 'http' if content_id.startswith(HTTP_PREFIX) else 'acestream'


def is_acestream_id(value: object) -> bool:
    """A 40-hex AceStream content ID or infohash, either case."""
    return isinstance(value, str) and re.fullmatch(ACESTREAM_ID_PATTERN, value) is not None


def is_http_id(value: object) -> bool:
    """A stored HTTP source ID: ``url:`` plus 40 lowercase hex."""
    return isinstance(value, str) and re.fullmatch(HTTP_ID_PATTERN, value) is not None
