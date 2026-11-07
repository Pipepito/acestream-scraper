"""Best-stream-first ordering shared by playlists, the tuner lineup and the
TV-channel API (spec 5.2). Duck-typed: works on ORM rows and DTOs."""
from __future__ import annotations

from typing import Iterable, List, TypeVar

T = TypeVar("T")


def score_acestream(stream) -> int:
    score = 0
    if getattr(stream, "is_online", None):
        score += 10
    if getattr(stream, "logo", None):
        score += 3
    if getattr(stream, "tvg_id", None):
        score += 2
    if getattr(stream, "tvg_name", None):
        score += 1
    return score


def preference_key(stream) -> tuple[bool, int]:
    """Explicit preferences precede automatic ranking; unordered streams follow."""
    order = getattr(stream, "stream_order", None)
    return (order is None, order or 0)


def stream_sort_key(stream):
    order = getattr(stream, "stream_order", None)
    if order is not None:
        return (0, order, getattr(stream, "id", ""))
    return (1, -score_acestream(stream), getattr(stream, "id", ""))


def sort_streams_curated(streams: Iterable[T]) -> List[T]:
    return sorted(streams, key=stream_sort_key)
