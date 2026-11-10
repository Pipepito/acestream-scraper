"""Database-independent startup contracts."""
from typing import Literal
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class StartupEvent(BaseModel):
    time: str
    message: str
    level: Literal['info', 'warning', 'error'] = 'info'


class MigrationProgress(BaseModel):
    status: str
    total: int = 0
    processed: int = 0
    migrated: int = 0
    skipped: int = 0
    stale: int = 0
    percent: float = 0


class StartupStatus(BaseModel):
    server_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    startup_dependency: Literal['warp'] | None = None
    status: Literal['starting', 'ready', 'failed']
    phase: str
    events: list[StartupEvent]
    migration: MigrationProgress | None = None
    recovery_available: bool = False
    recovery_token: str
    guidance: str | None = None


class StartupRecoveryRequest(BaseModel):
    action: Literal['retry', 'salvage', 'fresh']
    recovery_token: str
    confirm: bool = False
