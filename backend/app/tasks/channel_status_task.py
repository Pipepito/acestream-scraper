"""
Periodic task for updating channel statuses.
"""
from app.config.database import SessionLocal
from app.services import notification_service
from app.services.channel_status_service import ChannelStatusService, channels_in_check_order
from app.models.models import AcestreamChannel
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
    scraping wait behind this job. The next pass prioritizes older unchecked
    work using the saved interval and age groups.
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
        remaining = max(0.0, max_seconds - (loop.time() - started))
        await asyncio.sleep(min(VIEWING_POLL_SECONDS, remaining))
        reason = viewing.watching()
    waited = loop.time() - started
    logger.info("Channel status pass resumed after %.0f s paused", waited)
    return waited, False


def run_channel_status_task():
    db = SessionLocal()
    logger = logging.getLogger("channel_status_task")
    try:
        service = ChannelStatusService(db)
        channels = channels_in_check_order(db)
        if not service._get_engine_url():
            # Keep age/favorite ordering while checking only engine-free sources.
            http_ids = {row[0] for row in db.query(AcestreamChannel.id).filter(
                AcestreamChannel.is_active == True,
                AcestreamChannel.stream_url.isnot(None),
            ).all()}
            channels = [channel_id for channel_id in channels if channel_id in http_ids]
            if not channels:
                return {"checked": 0, "skipped": 0, "failed": 0, "message": "No engine configured; status checks are disabled."}
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
