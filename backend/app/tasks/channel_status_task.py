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
            for channel_id in channels:
                if task_service.shutdown_event.is_set():
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
            return {
                "online": online,
                "offline": offline,
                "checked": checked,
                "skipped": skipped,
                "failed": failed,
            }

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
