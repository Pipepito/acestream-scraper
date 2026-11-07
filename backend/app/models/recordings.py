"""Durable DVR identity, executions and files; independent of guide row lifetime."""
from uuid import uuid4
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, JSON, String, BigInteger, Float, UniqueConstraint
from app.config.database import Base
from app.models.models import UtcDateTime, _utcnow


class Recording(Base):
    __tablename__ = 'recordings'
    __table_args__ = (CheckConstraint('end_time > start_time', name='recording_interval'),
                      Index('ix_recordings_due', 'state', 'start_time'),)
    id = Column(String(32), primary_key=True, default=lambda: uuid4().hex)
    tv_channel_id = Column(Integer, ForeignKey('tv_channels.id', ondelete='SET NULL'))
    occurrence_key = Column(String(64), index=True)
    snapshot = Column(JSON, nullable=False)
    start_time = Column(UtcDateTime(), nullable=False)
    end_time = Column(UtcDateTime(), nullable=False)
    timezone = Column(String(64), nullable=False)
    state = Column(String(24), nullable=False, default='scheduled')
    revision = Column(Integer, nullable=False, default=1)
    stop_requested = Column(Boolean, nullable=False, default=False)
    protected = Column(Boolean, nullable=False, default=False)
    actual_start = Column(UtcDateTime())
    actual_end = Column(UtcDateTime())
    reason = Column(String(64))
    gaps = Column(JSON, nullable=False, default=list)
    idempotency_key = Column(String(64), nullable=False, unique=True)
    request_hash = Column(String(64), nullable=False)
    created_at = Column(UtcDateTime(), nullable=False, default=_utcnow)
    updated_at = Column(UtcDateTime(), nullable=False, default=_utcnow, onupdate=_utcnow)


class RecordingAttempt(Base):
    __tablename__ = 'recording_attempts'
    __table_args__ = (UniqueConstraint('recording_id', 'ordinal'),)
    id = Column(String(32), primary_key=True, default=lambda: uuid4().hex)
    recording_id = Column(String(32), ForeignKey('recordings.id'), nullable=False, index=True)
    ordinal = Column(Integer, nullable=False)
    source_id = Column(String(255), nullable=False)
    route = Column(String(16), nullable=False)
    started_at = Column(UtcDateTime(), nullable=False, default=_utcnow)
    ended_at = Column(UtcDateTime())
    exit_code = Column(Integer)
    reason = Column(String(64))
    process_identity = Column(JSON)


class RecordingArtifact(Base):
    __tablename__ = 'recording_artifacts'
    id = Column(String(32), primary_key=True, default=lambda: uuid4().hex)
    recording_id = Column(String(32), ForeignKey('recordings.id'), nullable=False, index=True)
    attempt_id = Column(String(32), ForeignKey('recording_attempts.id'))
    root_id = Column(String(32), nullable=False)
    filename = Column(String(80), nullable=False, unique=True)
    kind = Column(String(16), nullable=False, default='original')
    state = Column(String(24), nullable=False, default='writing')
    profile = Column(String(16))
    source_artifact_id = Column(String(32))
    bytes = Column(BigInteger, nullable=False, default=0)
    duration = Column(Float)
    codecs = Column(JSON, nullable=False, default=list)
    reason = Column(String(64))
