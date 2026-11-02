"""How each attempt at a source ended when a client played it through the tuner.

One row per attempt, written by the relay's outcome recorder. The per-source
history the tuner ranks with is computed from these rows; nothing else writes
them, and rows past the retention window are pruned."""
from sqlalchemy import Column, Float, Index, Integer, String
from app.config.database import Base
from app.models.models import UtcDateTime, _utcnow


class StreamAttempt(Base):
    __tablename__ = 'stream_attempts'
    __table_args__ = (Index('ix_stream_attempts_content_created', 'content_id', 'created_at'),
                      Index('ix_stream_attempts_created', 'created_at'),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_id = Column(String(255), nullable=False)
    tv_channel_id = Column(Integer)
    outcome = Column(String(24), nullable=False)
    seconds = Column(Float, nullable=False, default=0.0)
    peers = Column(Integer)
    speed_down = Column(Integer)
    # The list the source came from and how many sources its channel had,
    # as they were when it was tried.
    source_url = Column(String(2048))
    channel_sources = Column(Integer)
    created_at = Column(UtcDateTime(), nullable=False, default=_utcnow)
