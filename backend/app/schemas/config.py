from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator


class PlaybackRouting(BaseModel):
    use_acexy: bool = Field(False, description="Route web, tuner and remote-player playback through Acexy")
    acexy_url: str = Field("http://localhost:8080", description="HTTP(S) origin where the backend reaches Acexy in MPEG-TS mode")

    @field_validator("acexy_url")
    @classmethod
    def validate_acexy_url(cls, value: str) -> str:
        from app.services.public_url_service import normalize_public_base_url

        if any(char.isspace() for char in value.strip()):
            raise ValueError("Acexy URL must not contain whitespace")
        try:
            normalized = normalize_public_base_url(value)
        except ValueError as exc:
            raise ValueError("Acexy URL must be an HTTP(S) origin without a path, query or credentials") from exc
        if not normalized:
            raise ValueError("Acexy URL is required")
        return normalized

class BaseUrlUpdate(BaseModel):
    """Schema for updating the base URL for Acestream links"""
    base_url: Optional[str] = Field(None, description="Base URL for Acestream links")
    value: Optional[str] = Field(None, description="Compatibility alias for base_url")

    def resolved_value(self) -> Optional[str]:
        return self.base_url or self.value

class AceEngineUrlUpdate(BaseModel):
    """Schema for updating the Acestream Engine URL"""
    value: str = Field(..., description="Acestream Engine URL")

class RescrapeIntervalUpdate(BaseModel):
    """Schema for updating the rescrape interval"""
    value: Optional[str] = Field(None, description="Hours between automatic rescrapes")
    hours: Optional[int] = Field(None, description="Numeric hours between automatic rescrapes")

    def resolved_value(self) -> Optional[str]:
        if self.value is not None:
            return self.value
        if self.hours is not None:
            return str(self.hours)
        return None

class AddPidUpdate(BaseModel):
    """Schema for updating the addpid setting"""
    value: str = Field(..., description="Whether to add PID to Acestream links")


class AppIdUpdate(BaseModel):
    """Schema for updating appid setting"""
    value: str = Field(..., description="Whether to add appid to Acestream links")


class PublicBaseUrlUpdate(BaseModel):
    """Schema for updating the externally reachable origin (spec 4.3)."""
    value: str = Field("", description="http(s)://host[:port]; empty clears the override")


class DashboardConfigUpdate(BaseModel):
    """Schema for dashboard config updates"""
    retention_days: Optional[int] = None
    auto_refresh_interval: Optional[int] = None


class DashboardConfigResponse(BaseModel):
    """Schema for dashboard config response"""
    retention_days: int
    auto_refresh_interval: int


class ConfigUpdateResponse(BaseModel):
    """Schema for simple config mutation result"""
    message: str
    value: str


class ConfigKeyUpdate(BaseModel):
    """Schema for generic config key update endpoint"""
    value: Optional[str] = Field(None, description="Setting value; channel_status_interval uses whole minutes (1–10080, default 60)")
    base_url: Optional[str] = None
    hours: Optional[int] = None

    def get_value_for_key(self, key: str) -> Optional[str]:
        if key == "base_url":
            return self.base_url or self.value
        if key == "rescrape_interval":
            if self.value is not None:
                return self.value
            if self.hours is not None:
                return str(self.hours)
            return None
        return self.value

class SettingResponse(BaseModel):
    """Schema for a setting response"""
    key: str = Field(..., description="Setting key")
    value: str = Field(..., description="Setting value")

class SettingsResponse(BaseModel):
    """Schema for all settings response"""
    settings: Dict[str, str] = Field(..., description="All settings")

class StatusResponse(BaseModel):
    """Schema for a status check response"""
    status: str = Field(..., description="Status of the component (online, offline, error, etc.)")
    message: str = Field(..., description="Status message")
    details: Optional[str] = Field(None, description="Additional details")

class HealthResponse(BaseModel):
    """Schema for the health check response"""
    status: str = Field(..., description="Overall system status (healthy, degraded, unhealthy)")
    acestream: StatusResponse = Field(..., description="Acestream Engine status")
    database: Dict[str, Any] = Field(..., description="Database connection status")
    settings: Dict[str, Any] = Field(..., description="Application settings")
    version: str = Field(..., description="Application version")
