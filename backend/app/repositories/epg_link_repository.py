"""Inventory queries for repairing EPG links."""
from sqlalchemy.orm import Session
from app.models.models import EPGChannel, EPGSource, TVChannel


class EPGLinkRepository:
    def __init__(self, db: Session):
        self.db = db

    def enabled_channels(self) -> list[EPGChannel]:
        return (self.db.query(EPGChannel).join(EPGSource)
                .filter(EPGSource.enabled.is_(True))
                .order_by(EPGChannel.epg_source_id, EPGChannel.id).all())

    def tv_channels(self) -> list[TVChannel]:
        return self.db.query(TVChannel).all()
