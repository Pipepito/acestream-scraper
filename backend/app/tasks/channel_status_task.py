"""
Periodic task for updating channel statuses.
"""
from app.config.database import SessionLocal
from app.services.channel_status_service import ChannelStatusService
from app.models.models import AcestreamChannel
import logging
import asyncio
from datetime import datetime, timezone
from app.services.probe_queue import ProbePriority
from app.services.task_service import task_service


def run_channel_status_task():
    db = SessionLocal()
    logger = logging.getLogger("channel_status_task")
    try:
        service = ChannelStatusService(db)
        if not service._get_engine_url():
            return {"checked": 0, "skipped": 0, "failed": 0, "message": "No engine configured; status checks are disabled."}
        channels = db.query(AcestreamChannel).filter(AcestreamChannel.is_active == True).all()
        logger.info(f"Starting channel status update for {len(channels)} channels.")

        async def check_all():
            started = datetime.now(timezone.utc)
            skipped = 0
            checked = 0
            failed = 0
            for channel in channels:
                if task_service.shutdown_event.is_set():
                    break
                try:
                    result = await service.check_channel_status(
                        channel, priority=ProbePriority.BACKGROUND, scan_started_at=started,
                    )
                    if result['status'] == 'skipped':
                        skipped += 1
                    else:
                        checked += 1
                except Exception as exc:
                    failed += 1
                    logger.exception("Channel status check failed channel_id=%s error=%s", channel.id, exc)
            return {
                "checked": checked,
                "skipped": skipped,
                "failed": failed,
            }

        result = asyncio.run(check_all())
        logger.info("Channel status task completed result=%s", result)
        return result
    except Exception as exc:
        logger.exception("Channel status task failed error=%s", exc)
        raise
    finally:
        db.close()
