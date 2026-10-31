"""Explicit account and playback policy contracts; secrets are input-only."""
from typing import Literal
import ipaddress
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

Permission = Literal['live', 'channels', 'guide', 'events', 'recordings', 'playlists', 'cast', 'cast_server']
PERMISSIONS = ('live', 'channels', 'guide', 'events', 'recordings', 'playlists', 'cast', 'cast_server')


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Credentials(StrictModel):
    username: str = Field(min_length=1, max_length=64, pattern=r'^[a-zA-Z0-9_.-]+$')
    password: SecretStr = Field(min_length=1, max_length=128)


class Bootstrap(Credentials):
    enabled: bool = True
    password_confirmation: SecretStr
    migrate_legacy_token: bool = False


class PasswordChange(StrictModel):
    current_password: SecretStr
    password: SecretStr = Field(min_length=12, max_length=128)
    password_confirmation: SecretStr


class AccountCreate(Credentials):
    administrator: bool = False
    permissions: list[Permission] = Field(default_factory=list, max_length=8)


class AccountUpdate(StrictModel):
    administrator: bool
    enabled: bool
    permissions: list[Permission] = Field(max_length=8)


class AccountView(BaseModel):
    id: str
    username: str
    administrator: bool
    enabled: bool
    permissions: list[Permission]


class AccessPolicy(StrictModel):
    public_features: list[Permission] = Field(default_factory=list, max_length=6)
    public_playlists: bool = False
    local_iptv: bool = False
    local_networks: list[str] = Field(default_factory=list, max_length=16)
    home_networks: list[str] = Field(default_factory=list, max_length=16)
    remote_casting: bool = False
    compatibility_conversion: bool = False
    cast_media_url: str = Field(default='', max_length=2048)

    @field_validator('public_features')
    @classmethod
    def public_permissions(cls, value):
        if set(value) - {'live', 'channels', 'guide', 'events', 'cast'}:
            raise ValueError('Recordings and server devices cannot be public')
        return sorted(set(value))

    @field_validator('home_networks', 'local_networks')
    @classmethod
    def networks(cls, values):
        result = []
        for value in values:
            network = ipaddress.ip_network(value, strict=False)
            if network.prefixlen == 0 or network.is_multicast or network.is_unspecified or network.is_loopback:
                raise ValueError('Use explicit client networks, not wildcard or loopback networks')
            result.append(str(network))
        return sorted(set(result))

    @field_validator('cast_media_url')
    @classmethod
    def media_url(cls, value):
        if not value:
            return value
        parsed = urlsplit(value)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Use an HTTP(S) application base URL without credentials or query parameters')
        return value.rstrip('/')


class AccessStatus(BaseModel):
    mode: Literal['pending', 'open', 'accounts']
    user: AccountView | None = None
    permissions: list[Permission] = Field(default_factory=list)
    csrf: str
    legacy_token: bool = False


class CredentialCreate(StrictModel):
    label: str = Field(min_length=1, max_length=80)
    kind: Literal['admin', 'playback'] = 'playback'


class CredentialView(BaseModel):
    id: str
    label: str
    kind: Literal['admin', 'playback']
    created_at: float


class CredentialIssued(CredentialView):
    token: str


class SessionView(BaseModel):
    id: str
    username: str
    created_at: float
    last_seen: float
    expires_at: float


class DisableAccess(StrictModel):
    current_password: SecretStr
