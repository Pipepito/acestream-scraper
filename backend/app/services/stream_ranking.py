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


def sort_streams_curated(streams: Iterable[T]) -> List[T]:
    return sorted(streams, key=lambda s: (-score_acestream(s), getattr(s, "id", "")))
