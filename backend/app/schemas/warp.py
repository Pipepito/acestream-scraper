"""
Pydantic schemas for WARP-related APIs
"""
from enum import Enum
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

class WarpModeEnum(str, Enum):
    """Available WARP modes for API use"""
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
