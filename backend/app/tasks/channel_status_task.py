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
    try:
        logger = logging.getLogger("channel_status_task")
        service = ChannelStatusService(db)
        channels = db.query(AcestreamChannel).filter(AcestreamChannel.is_active == True).all()
        logger.info(f"Starting channel status update for {len(channels)} channels.")
        async def check_all():
            for channel in channels:
                result = await service.check_channel_status(channel)
        asyncio.run(check_all())
    except Exception as e:
        logging.getLogger("channel_status_task").error(f"Channel status task failed: {e}")
    finally:
        db.close()
