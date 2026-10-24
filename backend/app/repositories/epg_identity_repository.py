"""Read the complete guide identity inventory, independent of export filters."""
from sqlalchemy.orm import Session
from app.models.models import EPGChannel


def guide_identities(db: Session):
    return db.query(EPGChannel.epg_source_id, EPGChannel.channel_xml_id).all()
