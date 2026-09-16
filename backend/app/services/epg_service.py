"""Stable EPG service interface; responsibilities are split into focused modules."""
from sqlalchemy.orm import Session
from app.services.epg_sources import EPGSourceOperations
from app.services.epg_xmltv import XMLTVProcessing
from app.services.epg_channels import EPGChannelOperations
from app.services.epg_export import EPGExportOperations


class EPGService(EPGSourceOperations, XMLTVProcessing, EPGChannelOperations, EPGExportOperations):
    """Share one database session across source, parsing, matching and export operations."""
    def __init__(self, db: Session):
        self.db = db
