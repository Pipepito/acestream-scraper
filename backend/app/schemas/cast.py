from typing import Literal
from pydantic import BaseModel, Field
from app.schemas.player import PlayerSessionCreate


class CastDevice(BaseModel):
    id: str
    name: str
    model: str


class CastCapabilities(BaseModel):
    server_devices: bool
    compatibility_conversion: bool
    media_url_configured: bool
    message: str = ''
    error_code: str | None = Field(default=None, pattern=r'^[A-Z][A-Z0-9_]{0,99}$')
    home_connection: bool = False
    media_url: str = ''
    # off: open installation without the home gate; deployment: CAST_REQUIRE_HOME_NETWORK; accounts: accounts mode.
    home_check: Literal['off', 'deployment', 'accounts'] = 'off'


class CastStart(PlayerSessionCreate):
    device_id: str | None = Field(default=None, max_length=64)
    compatibility: bool = False
    replace: bool = False


class CastStatus(BaseModel):
    id: str
    device_id: str
    device_name: str
    state: str
    viewer_id: str
    volume: float | None = None


class CastCommand(BaseModel):
    action: Literal['play', 'pause', 'stop', 'volume']
    volume: float | None = Field(default=None, ge=0, le=1)
