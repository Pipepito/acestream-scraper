"""
Periodic task for updating channel statuses.
"""
from app.config.database import SessionLocal
from app.services import notification_service
from app.services.channel_status_service import ChannelStatusService
from app.models.models import AcestreamChannel, TVChannel
from sqlalchemy import case
import logging
import asyncio
from datetime import datetime, timezone
from app.services.probe_queue import ProbePriority
from app.services.task_service import task_service
from app.services import viewing

# How often a paused pass looks again whether someone is still watching.
VIEWING_POLL_SECONDS = 5.0
# How long a pass waits in all before it ends. Scheduled jobs share one FIFO
# queue: a paused pass holds the guide refresh and the scraping behind it, so
# it lets them through after this and the next pass tries again.
VIEWING_MAX_PAUSE_SECONDS = 600.0


async def wait_while_watching(logger, max_seconds: float) -> tuple[float, bool]:
    """Hold the pass while someone watches. Returns (seconds waited, gave up).

    It gives up after ``max_seconds`` (VIEWING_MAX_PAUSE_SECONDS in all) so a
    long match does not hold the maintenance queue -- guide refresh and
    scraping wait behind this job. The next pass resumes where this stopped,
    because the check order is least recently checked first.
    """
    reason = viewing.watching()
    if reason is None:
        return 0.0, False
    logger.info("Channel status pass paused: someone is watching (%s)", reason)
    loop = asyncio.get_running_loop()
    started = loop.time()
    while reason is not None and not task_service.shutdown_event.is_set():
        if loop.time() - started >= max_seconds:
            logger.info("Channel status pass stopped after %.0f s paused; the next one resumes", max_seconds)
            return loop.time() - started, True
        await asyncio.sleep(min(VIEWING_POLL_SECONDS, max(0.0, max_seconds - (loop.time() - started))))
        reason = viewing.watching()
    waited = loop.time() - started
    logger.info("Channel status pass resumed after %.0f s paused", waited)
    return waited, False


def channels_in_check_order(db):
    """Active stream ids in the order a status pass should check them.

    The pass used to walk the table in insertion order and rebuild that list
    from row 1 on every start. A machine that is on for an hour or two never
    finished a pass (about 3 h for 1,000 sources), so it kept checking the
    same first rows and never reached the last ones: on a real box 58% were
    checked and the tail never was.

    Now:
      1. never checked            -- the tail that was never reached
      2. streams of favourite TV channels -- the ones the viewer cares about
      3. streams of any other TV channel -- what the playlist can open; on
         one box (0 favourites) they were mixed with 935 loose streams
      4. the rest, least recently checked first

    Ordering by `last_checked` makes a restarted pass resume by itself: what
    was just checked moves to the end. No cursor to store.
    """
    never = case((AcestreamChannel.last_checked.is_(None), 0), else_=1)
    favourite = case((TVChannel.is_favorite.is_(True), 0), else_=1)
    assigned = case((AcestreamChannel.tv_channel_id.is_(None), 1), else_=0)
    rows = (db.query(AcestreamChannel.id)
            .outerjoin(TVChannel, AcestreamChannel.tv_channel_id == TVChannel.id)
            .filter(AcestreamChannel.is_active == True)  # noqa: E712
            .order_by(never, favourite, assigned, AcestreamChannel.last_checked.asc(),
                      AcestreamChannel.id.asc())
            .all())
    return [row[0] for row in rows]


def run_channel_status_task():
    db = SessionLocal()
    logger = logging.getLogger("channel_status_task")
    try:
        service = ChannelStatusService(db)
        if not service._get_engine_url():
            return {"checked": 0, "skipped": 0, "failed": 0, "message": "No engine configured; status checks are disabled."}
        channels = channels_in_check_order(db)
        db.rollback()
        logger.info(f"Starting channel status update for {len(channels)} channels.")

        async def check_all():
            started = datetime.now(timezone.utc)
            skipped = 0
            checked = 0
            failed = 0
            online = 0
            offline = 0
            paused = 0.0
            max_pause = VIEWING_MAX_PAUSE_SECONDS
            stop_reason = None
            for channel_id in channels:
                if task_service.shutdown_event.is_set():
                    stop_reason = "shutdown"
                    break
                # Between sources, never in the middle of one: a probe that
                # started finishes and cleans up as before.
                waited, gave_up = await wait_while_watching(logger, max_pause - paused)
                paused += waited
                if gave_up or task_service.shutdown_event.is_set():
                    stop_reason = "shutdown" if task_service.shutdown_event.is_set() else "viewing"
                    break
                try:
                    channel = db.get(AcestreamChannel, channel_id)
                    if channel is None:
                        skipped += 1
                        continue
                    result = await service.check_channel_status(
                        channel, priority=ProbePriority.BACKGROUND, scan_started_at=started,
                    )
                    if result['status'] == 'skipped':
                        skipped += 1
                    else:
                        checked += 1
                        if result["is_online"]:
                            online += 1
                        else:
                            offline += 1
                except Exception as exc:
                    failed += 1
                    db.rollback()
                    logger.exception("Channel status check failed channel_id=%s error=%s", channel_id, exc)
                finally:
                    db.rollback()
                    task_service.update_task_progress("channel_status", {
                        "processed": checked + skipped + failed, "total": len(channels),
                        "percent": round(100 * (checked + skipped + failed) / len(channels), 1),
                    })
            result = {
                "online": online,
                "offline": offline,
                "checked": checked,
                "skipped": skipped,
                "failed": failed,
            }
            if stop_reason is not None:
                result.update(deferred=len(channels) - checked - skipped - failed, stop_reason=stop_reason)
            return result

        result = asyncio.run(check_all())
        logger.info("Channel status task completed result=%s", result)
        notification_service.channel_status_completed(result)
        return result
    except Exception as exc:
        logger.exception("Channel status task failed error=%s", exc)
        notification_service.task_failed('channel_status', exc)
        raise
    finally:
        db.close()
