"""Explicit stream additions and links share one transaction."""
from app.api.error_handlers import APIError
from sqlalchemy.orm import Session
from app.models.models import AcestreamChannel
from app.repositories.channel_repository import ChannelRepository
from app.schemas.channel import AcestreamChannelCreate
from app.services.import_pipeline import ImportEntry, ImportPipeline, ImportReference


def validate_link_target(db: Session, tv_channel_id: int | None) -> None:
    if tv_channel_id is not None and ChannelRepository(db).get_tv_channel_by_id(tv_channel_id) is None:
        raise APIError('TV_CHANNEL_NOT_FOUND', 'This TV channel no longer exists. Choose another channel.', 404)


def link_imported_stream(db: Session, content_id: str, tv_channel_id: int | None) -> None:
    if tv_channel_id is None:
        return
    validate_link_target(db, tv_channel_id)
    channel = ChannelRepository(db).get_channel_by_id(content_id)
    if channel is None:
        raise APIError('STREAM_NOT_FOUND', 'The stream could not be added.', 409)
    if channel.tv_channel_id not in (None, tv_channel_id):
        raise APIError('STREAM_ALREADY_LINKED', 'This stream is already linked to another TV channel. Change its assignment in Streams.', 409)
    channel.tv_channel_id = tv_channel_id


def create_manual_stream(db: Session, request: AcestreamChannelCreate) -> AcestreamChannel:
    try:
        # ImportPipeline claims the shared import write lock before upsert/link.
        result = ImportPipeline.apply(db, ImportReference(request.source_url, allow_excluded=request.allow_excluded), [
            ImportEntry(request.id, request.name, group=request.group, logo=request.logo,
                        tvg_id=request.tvg_id, tvg_name=request.tvg_name, is_online=request.is_online,
                        updates=request.model_dump(exclude_unset=True, exclude={'allow_excluded', 'tv_channel_id'}))], 'manual')
        link_imported_stream(db, request.id, request.tv_channel_id)
        db.commit()
        channel = result.items[0].channel
        db.refresh(channel)
        return channel
    except Exception:
        db.rollback()
        raise
