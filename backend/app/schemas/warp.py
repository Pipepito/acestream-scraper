"""
Pydantic schemas for WARP-related APIs
"""
from enum import Enum
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

class WarpModeEnum(str, Enum):
    """Available WARP modes for API use"""
    DOH = "doh"
    WARP_DOH = "warp+doh"
    WARP_DOT = "warp+dot"
    TUNNEL_ONLY = "tunnel_only"
    WARP = "warp"
    DOT = "dot"
    PROXY = "proxy"
    OFF = "off"

class WarpLicenseRequest(BaseModel):
    """Request schema for registering a WARP license"""
    license_key: str = Field(
        ...,
        description="The WARP license key to register",
        min_length=8
    )

class WarpModeRequest(BaseModel):
    """Request schema for changing WARP mode"""
    mode: WarpModeEnum = Field(
        ...,
        description="The WARP mode to set"
    )

class WarpStatusResponse(BaseModel):
    """Response schema for WARP status"""
    running: bool = Field(
        default=False,
        description="Whether the WARP daemon is running"
    )
    connected: bool = Field(
        default=False,
        description="Whether WARP is connected"
    )
    mode: Optional[str] = Field(
        default=None,
        description="The current WARP mode"
    )
    account_type: str = Field(
        default="free",
        description="The type of WARP account (free, premium, team)"
    )
    ip: Optional[str] = Field(
        default=None,
        description="The current IP address when connected to WARP"
    )
    location: Optional[str] = Field(default=None, description="Country code reported by Cloudflare's trace")
    colo: Optional[str] = Field(default=None, description="Cloudflare data centre serving the tunnel")
    tunnel: Dict[str, Optional[str]] = Field(default_factory=dict, description="Details from `warp-cli tunnel stats`")
    registration: Dict[str, Optional[str]] = Field(default_factory=dict, description="Account/device ids and masked license")
    cf_trace: Dict[str, str] = Field(
        default_factory=dict,
        description="Cloudflare trace information"
    )

class WarpResponse(BaseModel):
    """Generic response schema for WARP operations"""
    success: bool
    status: str = Field(default="success", description="Operation status (success/error)")
    message: str
    details: Optional[Dict[str, Any]] = None


class WarpExclusionsUpdate(BaseModel):
    """Replace only app-managed exclusions, with optimistic concurrency."""
    hosts: list[str] = Field(max_length=64)
    expected_revision: str = Field(min_length=64, max_length=64)


class WarpExclusionsState(BaseModel):
    hosts: list[str]
    revision: str
    active_hosts: list[str] | None
    applied: bool
    error: str | None = None
