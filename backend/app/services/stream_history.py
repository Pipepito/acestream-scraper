"""Per-source playback history: what the tuner relay saw when clients played a
source, and the ranking the relay derives from it.

The relay reports how each attempt ended through
``tuner_playback_service.set_outcome_recorder``. Writes go through a single
background thread so a slow SQLite write never delays playback, and a failing
write only loses that row.

Ranking is rule based and deliberately small:

* each attempt counts with a weight that halves every ``HALF_LIFE_DAYS``;
* an attempt that played scores 1 (``ok``), less if the source ended or
  stalled after playing, 0 if it never played; engine outages say nothing
  about the source and are ignored;
* an attempt that played counts as more evidence the longer it played (one
  more attempt's worth per 30 minutes, up to three);
* the list a source came from is the prior: the share of that list's active
  sources the last check found online;
* a source is *demoted* (tried after every other candidate, never dropped)
  when no list has published it for ``STALE_DAYS``, when its own recent
  history is clearly bad, or when it has no history of its own and its list
  is almost entirely offline.
"""
from __future__ import annotations

import logging
import queue
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Iterable, Optional

logger = logging.getLogger(__name__)

HALF_LIFE_DAYS = 7.0
HISTORY_DAYS = 60
RETENTION_DAYS = 180
STALE_DAYS = 14
PRIOR_STRENGTH = 2.0
# A list with at least this many active sources and fewer than this share
# online is "mostly dead".
DEAD_LIST_MIN_SOURCES = 10
DEAD_LIST_SHARE = 0.2
# Own history: at least this much (decayed) evidence and a score below this.
BAD_EVIDENCE = 2.0
BAD_SCORE = 0.25
PRUNE_EVERY = 500
# A row written with a clock that ran ahead (a box switched on before its clock
# synchronised) says nothing reliable about when it happened: it is ignored
# instead of counting as the most recent attempt.
FUTURE_TOLERANCE = timedelta(minutes=5)
# An attempt that played counts as more evidence the longer it played: one more
# attempt's worth per PLAYED_SECONDS_PER_ATTEMPT, up to MAX_PLAYED_WEIGHT.
PLAYED_SECONDS_PER_ATTEMPT = 1800.0
MAX_PLAYED_WEIGHT = 3.0

OUTCOME_VALUE = {
    'ok': 1.0,
    'ended': 0.5,
    'stall': 0.3,
    # Played, but its clock kept going back: the viewer saw the same play
    # again and again. Low, and weighted by how long it was watched.
    'jumpy': 0.1,
    'early_death': 0.0,
    'no_data': 0.0,
    'empty_session': 0.0,
    'engine_refused': 0.0,
    'upstream_error': 0.0,
    # Not about the source.
    'engine_unavailable': None,
    # A GET that handed its opening to a newer one (Kodi's second GET): the
    # viewing is recorded once, by the GET that took over.
    'handover': None,
}


@dataclass(frozen=True)
class SourceScore:
    score: float
    evidence: float
    demoted: bool


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def score_sources(streams: Iterable, attempts, list_health: Dict[str, tuple[int, int]],
                  now: datetime) -> Dict[str, SourceScore]:
    """Pure ranking: ``streams`` are rows with ``id``, ``source_url`` and
    ``last_seen``; ``attempts`` are (content_id, outcome, seconds, created_at)."""
    weighted: Dict[str, list[float]] = {}
    for content_id, outcome, seconds, created_at in attempts:
        value = OUTCOME_VALUE.get(outcome)
        if value is None or _aware(created_at) > now + FUTURE_TOLERANCE:
            continue
        age_days = max(0.0, (now - _aware(created_at)).total_seconds() / 86400)
        weight = 0.5 ** (age_days / HALF_LIFE_DAYS)
        if value > 0:
            weight *= min(MAX_PLAYED_WEIGHT, 1.0 + max(0.0, seconds or 0.0) / PLAYED_SECONDS_PER_ATTEMPT)
        total = weighted.setdefault(content_id.lower(), [0.0, 0.0])
        total[0] += weight * value
        total[1] += weight
    scores: Dict[str, SourceScore] = {}
    for stream in streams:
        cid = stream.id.lower()
        size, online = list_health.get(getattr(stream, 'source_url', None) or '', (0, 0))
        prior = min(0.95, max(0.05, online / size)) if size else 0.5
        good, evidence = weighted.get(cid, (0.0, 0.0))
        score = (PRIOR_STRENGTH * prior + good) / (PRIOR_STRENGTH + evidence)
        last_seen = getattr(stream, 'last_seen', None)
        # A last_seen in the future is unknown, not fresh: it neither demotes nor
        # protects the source.
        stale = (last_seen is not None and _aware(last_seen) <= now + FUTURE_TOLERANCE
                 and now - _aware(last_seen) > timedelta(days=STALE_DAYS))
        bad_history = evidence >= BAD_EVIDENCE and score < BAD_SCORE
        dead_list = (evidence == 0.0 and size >= DEAD_LIST_MIN_SOURCES and online / size < DEAD_LIST_SHARE)
        scores[cid] = SourceScore(score=score, evidence=evidence, demoted=stale or bad_history or dead_list)
    return scores


def scores_for(db, streams, now: Optional[datetime] = None) -> Dict[str, SourceScore]:
    from app.repositories.stream_attempt_repository import StreamAttemptRepository
    now = now or datetime.now(timezone.utc)
    streams = list(streams)
    repo = StreamAttemptRepository(db)
    attempts = repo.attempts_since((s.id for s in streams), now - timedelta(days=HISTORY_DAYS))
    health = repo.list_health(getattr(s, 'source_url', None) for s in streams)
    return score_sources(streams, attempts, health, now)


def _latest_list_reading(db, now: datetime) -> datetime:
    """When the lists were last read: the newest ``last_seen`` of any active
    source, never later than ``now``.

    Hiding measures staleness from here, not from the wall clock, so a clock
    that starts ahead (a box switched on before it synchronises) or a box that
    stayed off for weeks hides nothing until the lists have been read again."""
    from sqlalchemy import func

    from app.models.models import AcestreamChannel
    latest = (db.query(func.max(AcestreamChannel.last_seen))
              .filter(AcestreamChannel.is_active.is_(True)).scalar())
    return min(now, _aware(latest)) if latest is not None else now


def unusable_ids(db, streams, now: Optional[datetime] = None) -> set[str]:
    """Sources with no useful prospect: no list has published them for
    ``STALE_DAYS`` before the latest list reading, or their own recent
    playback history is clearly bad.

    Deliberately narrower than ``demoted``: a mostly offline list alone does
    not make a source unusable, because status checks of a box that is only on
    now and then are often hours or days old. Used by the playlist's
    ``hide_unusable`` option; a source becomes usable again as soon as a list
    publishes it or it plays."""
    now = now or datetime.now(timezone.utc)
    streams = list(streams)
    scores = scores_for(db, streams, now)
    reference = _latest_list_reading(db, now)
    unusable = set()
    for stream in streams:
        cid = stream.id.lower()
        last_seen = getattr(stream, 'last_seen', None)
        stale = (last_seen is not None and _aware(last_seen) <= now + FUTURE_TOLERANCE
                 and reference - _aware(last_seen) > timedelta(days=STALE_DAYS))
        past = scores.get(cid)
        bad = past is not None and past.evidence >= BAD_EVIDENCE and past.score < BAD_SCORE
        if stale or bad:
            unusable.add(cid)
    return unusable


class StreamHistoryRecorder:
    """Queues outcomes from the relay and writes them on one daemon thread."""

    def __init__(self, session_factory: Callable, clock: Callable[[], datetime] | None = None):
        self._session_factory = session_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._queue: queue.Queue = queue.Queue(maxsize=10000)
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._written = 0
        # Row written by an attempt's checkpoints, until its final outcome
        # (only touched by the writer thread).
        self._rows: dict = {}

    def record(self, content_id: str, tv_channel_id: int | None, outcome: str, *, seconds: float,
               peers: int | None = None, speed_down: int | None = None, attempt: object = None,
               final: bool = True) -> None:
        self._ensure_started()
        try:
            self._queue.put_nowait((content_id, tv_channel_id, outcome, seconds, peers, speed_down, self._clock(),
                                    attempt, final))
        except queue.Full:
            logger.warning('Stream history queue full; dropped outcome %s for %s', outcome, content_id)

    def flush(self, timeout: float = 5.0) -> None:
        """Wait until every queued outcome is written (tests and shutdown)."""
        done = threading.Event()
        threading.Thread(target=lambda: (self._queue.join(), done.set()), daemon=True).start()
        done.wait(timeout)

    def _ensure_started(self) -> None:
        with self._lock:
            if self._thread is None or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._run, name='stream-history', daemon=True)
                self._thread.start()

    def _run(self) -> None:
        from app.repositories.stream_attempt_repository import StreamAttemptRepository
        while True:
            item = self._queue.get()
            try:
                content_id, tv_channel_id, outcome, seconds, peers, speed_down, at, attempt, final = item
                db = self._session_factory()
                try:
                    repo = StreamAttemptRepository(db)
                    row_id = self._rows.pop(attempt, None) if final else self._rows.get(attempt)
                    if row_id is not None and repo.update(row_id, outcome, seconds=seconds) is not None:
                        continue
                    row = repo.add(content_id, tv_channel_id, outcome, seconds=seconds, peers=peers,
                                   speed_down=speed_down, created_at=at)
                    if attempt is not None and not final:
                        self._rows[attempt] = row.id
                    self._written += 1
                    if self._written % PRUNE_EVERY == 0:
                        repo.prune(at - timedelta(days=RETENTION_DAYS))
                finally:
                    db.close()
            except Exception:  # noqa: BLE001 - history must never affect playback
                logger.exception('Stream history write failed')
            finally:
                self._queue.task_done()


_recorder: StreamHistoryRecorder | None = None


def install() -> StreamHistoryRecorder:
    """Connect the relay's outcome hook to the history store."""
    global _recorder
    from app.config.database import SessionLocal
    from app.services.tuner_playback_service import set_outcome_recorder
    if _recorder is None:
        _recorder = StreamHistoryRecorder(SessionLocal)
    set_outcome_recorder(_recorder.record)
    return _recorder
