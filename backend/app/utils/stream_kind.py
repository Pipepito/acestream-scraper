"""Which input a stored stream ID addresses."""
from typing import Literal

HTTP_PREFIX = 'url:'

StreamKind = Literal['http', 'acestream']


def stream_kind(content_id: str) -> StreamKind:
    """``url:`` IDs are HTTP/broadcaster links; every other ID goes to the engine."""
    return 'http' if content_id.startswith(HTTP_PREFIX) else 'acestream'
