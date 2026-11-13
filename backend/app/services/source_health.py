"""What the evidence says about one source, wherever it was found.

A source is the asset; a list is only where it was found, so nothing here
looks at lists. Two kinds of fact reach this module:

- a status check (``apply_check``): media found, or none found;
- a viewing through the relay (``apply_worked``) that played.

From them a source is *working* (it worked recently, or has not failed
enough to say otherwise) or *discarded*: ``DISCARD_FAILED_CHECKS`` real checks
in a row found no media AND it has not worked for ``DISCARD_DAYS`` (counted
from when it began failing if it never worked). Both, because a server that
is on now and then can make a week one check, and five checks can fall in one
afternoon. A discarded source is still checked, after every other source and
at most every ``DISCARDED_RECHECK_DAYS``; the first check with media or the
first viewing brings it back.

The functions take any object with the ``last_worked_at``, ``failed_checks``
and ``failing_since`` attributes (an ``AcestreamChannel`` row or an inventory
row), so the rule is the same for hiding, check order and the API.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

DISCARD_FAILED_CHECKS = 5
DISCARD_DAYS = 7
DISCARDED_RECHECK_DAYS = 7
# Relay outcomes that prove the source plays.
WORKED_OUTCOMES = frozenset({'ok', 'handover'})
# A time this far ahead of now was written by a clock that ran ahead.
FUTURE_TOLERANCE = timedelta(minutes=5)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def is_real_check(online: bool, network_status: Optional[str] = None, *, http: bool = False) -> bool:
    """Whether a check result says something about the source itself.

    An HTTP check always does. An engine check does when it found media or
    when the engine's lookup answered (found or not found); a timeout or an
    engine outage says nothing about the source.
    """
    return http or bool(online) or network_status in ('found', 'not_found')


def apply_worked(stream, at: datetime) -> None:
    """The source played (a check with media, or a viewing): it works."""
    if stream.last_worked_at is None or _aware(stream.last_worked_at) < at:
        stream.last_worked_at = at
    stream.failed_checks = 0
    stream.failing_since = None


def apply_check(stream, online: bool, now: datetime) -> None:
    """Record one real check (see ``is_real_check``)."""
    if online:
        apply_worked(stream, now)
        return
    stream.failed_checks = (stream.failed_checks or 0) + 1
    if stream.failing_since is None:
        stream.failing_since = now


def discarded(stream, now: datetime) -> bool:
    """Failed ``DISCARD_FAILED_CHECKS`` real checks in a row and has not
    worked for ``DISCARD_DAYS``. A time in the future counts as unknown, so it
    never discards."""
    if (getattr(stream, 'failed_checks', 0) or 0) < DISCARD_FAILED_CHECKS:
        return False
    since = getattr(stream, 'last_worked_at', None) or getattr(stream, 'failing_since', None)
    if since is None or _aware(since) > now + FUTURE_TOLERANCE:
        return False
    return now - _aware(since) >= timedelta(days=DISCARD_DAYS)


def due_for_check(stream, last_checked: Optional[datetime], now: datetime) -> bool:
    """A discarded source is checked at most every ``DISCARDED_RECHECK_DAYS``;
    every other source whenever the pass reaches it. A check dated in the
    future counts as never made."""
    if not discarded(stream, now):
        return True
    if last_checked is None or _aware(last_checked) > now + FUTURE_TOLERANCE:
        return True
    return now - _aware(last_checked) >= timedelta(days=DISCARDED_RECHECK_DAYS)


def published_when_only_online(stream) -> bool:
    """Whether "only online" playlists and the tuner lineup keep this source.

    Online at its last check, or an HTTP stream not checked yet: playing it
    checks it, and a dead one fails in the player within seconds while the
    remote stays responsive. An AceStream ID not checked yet is left out,
    because waiting on the engine can block the remote. The M3U and the
    tuner lineup share this rule.
    """
    online = getattr(stream, 'is_online', None)
    return online is True or (online is None and bool(getattr(stream, 'stream_url', None)))


def published_when_only_online_clause():
    """``published_when_only_online`` as an SQL filter on ``AcestreamChannel``."""
    from sqlalchemy import and_, or_

    from app.models.models import AcestreamChannel
    return or_(AcestreamChannel.is_online.is_(True),
               and_(AcestreamChannel.stream_url.isnot(None), AcestreamChannel.is_online.is_(None)))
