"""DTOs for the sidecar services panel (/api/v1/system)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

ServiceState = Literal["running", "unhealthy", "stopped", "disabled", "external", "not-installed"]


class ServiceStatus(BaseModel):
    name: str = Field(description="Stable identifier: acestream, acexy, ipfs, zeronet, warp")
    label: str
    description: str
    state: ServiceState
    installed: bool = Field(description="Shipped in this image flavor")
    enabled: bool = Field(description="Turned on through its ENABLE_* variable")
    managed: bool = Field(description="Supervised by this container's entrypoint (restart available)")
    running: bool = Field(description="The service answered its health probe")
    endpoint: Optional[str] = Field(default=None, description="Where the app reaches the service")
    version: Optional[str] = None
    distribution: Optional[str] = Field(default=None, description="Package or image that supplied the service")
    distribution_url: Optional[str] = Field(default=None, description="Public attribution page for the distribution")
    message: str
    pid: Optional[int] = None
    uptime_seconds: Optional[int] = None


class ServicesStatusResponse(BaseModel):
    services: List[ServiceStatus]
    supervised: bool = Field(description="True when the app runs under the container entrypoint")
    checked_at: str


class ServiceRestartResponse(BaseModel):
    name: str
    success: bool
    message: str


class PublicUrlResponse(BaseModel):
    """The origin external clients must use to reach this server (spec 4.3)."""
    url: str = Field(description="scheme://host[:port], no trailing slash")
    source: Literal["setting", "forwarded", "request"]
    warnings: List[str] = Field(default_factory=list, description="localhost | docker-internal | unset | proxied")
