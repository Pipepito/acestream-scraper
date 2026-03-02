"""
Periodic task for updating channel statuses.
"""
from app.config.database import SessionLocal
from app.services.channel_status_service import ChannelStatusService
from app.models.models import AcestreamChannel
import logging
import asyncio


def run_channel_status_task():
    db = SessionLocal()
    logger = logging.getLogger("channel_status_task")
    try:
        service = ChannelStatusService(db)
        channels = db.query(AcestreamChannel).filter(AcestreamChannel.is_active == True).all()
        logger.info(f"Starting channel status update for {len(channels)} channels.")

        async def check_all():
            checked = 0
            failed = 0
            for channel in channels:
                try:
                    await service.check_channel_status(channel)
                    checked += 1
                except Exception as exc:
                    failed += 1
                    logger.exception("Channel status check failed channel_id=%s error=%s", channel.id, exc)
            return {
                "checked": checked,
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
