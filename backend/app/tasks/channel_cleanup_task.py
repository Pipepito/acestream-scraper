"""
Periodic task for cleaning up channels.
"""
from app.config.database import SessionLocal
from app.models.models import AcestreamChannel
from app.services.channel_service import ChannelService
import logging

def run_channel_cleanup_task():
    db = SessionLocal()
    try:
        logger = logging.getLogger("channel_cleanup_task")
        # Find all inactive channels
        inactive_channels = db.query(AcestreamChannel).filter(AcestreamChannel.is_active == False).all()
        service = ChannelService(db)
        count = 0
        for channel in inactive_channels:
            if service.delete_channel(channel.id):
                count += 1
        logger.info(f"Channel cleanup task completed: {count} inactive channels deleted.")
    except Exception as e:
        logging.getLogger("channel_cleanup_task").error(f"Channel cleanup task failed: {e}")
    finally:
        db.close()
