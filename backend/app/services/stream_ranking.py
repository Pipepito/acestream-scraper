"""Best-stream-first ordering shared by playlists, the tuner lineup and the
TV-channel API (spec 5.2). Duck-typed: works on ORM rows and DTOs."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Mapping, TypeVar

from app.services.source_health import discarded

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


# A check older than this ranks a source after every fresher one when the
# relay picks what to try first. The status check runs hourly by default.
FRESH_CHECK_HOURS = 6


def _observed_since(when, since: datetime, until: datetime) -> bool:
    if when is None:
        return False
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    # A clock correction must not make an observation fresh indefinitely.
    return since <= when <= until


def checked_since(stream, since: datetime, until: datetime) -> bool:
    return _observed_since(getattr(stream, "last_checked", None), since, until)


def worked_since(stream, since: datetime, until: datetime) -> bool:
    return _observed_since(getattr(stream, "last_worked_at", None), since, until)


def relay_order(streams: Iterable, history: Mapping, now: datetime) -> List[str]:
    """The order in which the relay tries a channel's sources (content IDs).

    Pure: it reads only the streams, their playback ``history`` (content ID
    -> score with ``score`` and ``demoted``, see ``stream_history``) and
    ``now``. Saved preferences first; then online and checked within
    ``FRESH_CHECK_HOURS``; online from an older check; never checked, or
    offline from an older check. A source found offline recently is left
    out, unless it also played within ``FRESH_CHECK_HOURS``: a check right
    after the relay lets a source go can find no media, and that one check
    must not keep the source that just played out of the relay for hours.
    It is tried with the never-checked ones. Within each group a source that
    played before goes first, then the higher bitrate; a demoted source goes
    after every group, and a discarded one (``source_health.discarded``)
    after the demoted; neither is dropped.
    """
    fresh_since = now - timedelta(hours=FRESH_CHECK_HOURS)
    ranked = []
    for stream in streams:
        fresh = checked_since(stream, fresh_since, now)
        if stream.is_online:
            bucket = 0 if fresh else 1
        elif stream.is_online is False and fresh and not worked_since(stream, fresh_since, now):
            continue
        else:
            bucket = 2
        past = history.get(stream.id.lower())
        if past is not None and past.demoted:
            bucket = 3
        if discarded(stream, now):
            bucket = 4
        score = past.score if past is not None else 0.5
        ranked.append((*preference_key(stream), bucket, -score, -(getattr(stream, "bitrate_bps", None) or 0),
                       stream.id.lower()))
    return list(dict.fromkeys(row[-1] for row in sorted(ranked)))
