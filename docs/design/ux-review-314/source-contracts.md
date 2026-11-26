# Current source contract appendix

Machine-extracted public Pydantic annotations/default expressions from `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`. These are evidence, not a new API, UI or exhaustive validator interpretation. Required inherited validators, model validators and service enforcement remain authoritative. Response/transport-only fields are intentionally not editable controls. Use each linked source to inspect validators and inheritance.

<a id="access-credentials-username"></a>
### `access.Credentials.username`

[backend/app/schemas/access.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L16) · type `str`

```python
Field(min_length=1, max_length=64, pattern='^[a-zA-Z0-9_.-]+$')
```

<a id="access-credentials-password"></a>
### `access.Credentials.password`

[backend/app/schemas/access.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L17) · type `SecretStr`

```python
Field(min_length=1, max_length=128)
```

<a id="access-bootstrap-enabled"></a>
### `access.Bootstrap.enabled`

[backend/app/schemas/access.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L21) · type `bool`

```python
True
```

<a id="access-bootstrap-password_confirmation"></a>
### `access.Bootstrap.password_confirmation`

[backend/app/schemas/access.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L22) · type `SecretStr`

```python
required / inherited validation
```

<a id="access-bootstrap-migrate_legacy_token"></a>
### `access.Bootstrap.migrate_legacy_token`

[backend/app/schemas/access.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L23) · type `bool`

```python
False
```

<a id="access-passwordchange-current_password"></a>
### `access.PasswordChange.current_password`

[backend/app/schemas/access.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L27) · type `SecretStr`

```python
required / inherited validation
```

<a id="access-passwordchange-password"></a>
### `access.PasswordChange.password`

[backend/app/schemas/access.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L28) · type `SecretStr`

```python
Field(min_length=12, max_length=128)
```

<a id="access-passwordchange-password_confirmation"></a>
### `access.PasswordChange.password_confirmation`

[backend/app/schemas/access.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L29) · type `SecretStr`

```python
required / inherited validation
```

<a id="access-accountcreate-administrator"></a>
### `access.AccountCreate.administrator`

[backend/app/schemas/access.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L33) · type `bool`

```python
False
```

<a id="access-accountcreate-permissions"></a>
### `access.AccountCreate.permissions`

[backend/app/schemas/access.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L34) · type `list[Permission]`

```python
Field(default_factory=list, max_length=8)
```

<a id="access-accountupdate-administrator"></a>
### `access.AccountUpdate.administrator`

[backend/app/schemas/access.py:38](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L38) · type `bool`

```python
required / inherited validation
```

<a id="access-accountupdate-enabled"></a>
### `access.AccountUpdate.enabled`

[backend/app/schemas/access.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L39) · type `bool`

```python
required / inherited validation
```

<a id="access-accountupdate-permissions"></a>
### `access.AccountUpdate.permissions`

[backend/app/schemas/access.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L40) · type `list[Permission]`

```python
Field(max_length=8)
```

<a id="access-accountview-id"></a>
### `access.AccountView.id`

[backend/app/schemas/access.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L44) · type `str`

```python
required / inherited validation
```

<a id="access-accountview-username"></a>
### `access.AccountView.username`

[backend/app/schemas/access.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L45) · type `str`

```python
required / inherited validation
```

<a id="access-accountview-administrator"></a>
### `access.AccountView.administrator`

[backend/app/schemas/access.py:46](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L46) · type `bool`

```python
required / inherited validation
```

<a id="access-accountview-enabled"></a>
### `access.AccountView.enabled`

[backend/app/schemas/access.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L47) · type `bool`

```python
required / inherited validation
```

<a id="access-accountview-permissions"></a>
### `access.AccountView.permissions`

[backend/app/schemas/access.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L48) · type `list[Permission]`

```python
required / inherited validation
```

<a id="access-castsettings-home_networks"></a>
### `access.CastSettings.home_networks`

[backend/app/schemas/access.py:52](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L52) · type `list[str]`

```python
Field(default_factory=list, max_length=16)
```

<a id="access-castsettings-remote_casting"></a>
### `access.CastSettings.remote_casting`

[backend/app/schemas/access.py:53](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L53) · type `bool`

```python
False
```

<a id="access-castsettings-compatibility_conversion"></a>
### `access.CastSettings.compatibility_conversion`

[backend/app/schemas/access.py:54](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L54) · type `bool`

```python
False
```

<a id="access-castsettings-cast_media_url"></a>
### `access.CastSettings.cast_media_url`

[backend/app/schemas/access.py:55](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L55) · type `str`

```python
Field(default='', max_length=2048)
```

<a id="access-accesspolicy-public_features"></a>
### `access.AccessPolicy.public_features`

[backend/app/schemas/access.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L80) · type `list[Permission]`

```python
Field(default_factory=list, max_length=6)
```

<a id="access-accesspolicy-public_playlists"></a>
### `access.AccessPolicy.public_playlists`

[backend/app/schemas/access.py:81](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L81) · type `bool`

```python
False
```

<a id="access-accesspolicy-local_iptv"></a>
### `access.AccessPolicy.local_iptv`

[backend/app/schemas/access.py:82](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L82) · type `bool`

```python
False
```

<a id="access-accesspolicy-local_networks"></a>
### `access.AccessPolicy.local_networks`

[backend/app/schemas/access.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L83) · type `list[str]`

```python
Field(default_factory=list, max_length=16)
```

<a id="access-accessstatus-mode"></a>
### `access.AccessStatus.mode`

[backend/app/schemas/access.py:99](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L99) · type `Literal['pending', 'open', 'accounts']`

```python
required / inherited validation
```

<a id="access-accessstatus-user"></a>
### `access.AccessStatus.user`

[backend/app/schemas/access.py:100](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L100) · type `AccountView | None`

```python
None
```

<a id="access-accessstatus-permissions"></a>
### `access.AccessStatus.permissions`

[backend/app/schemas/access.py:101](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L101) · type `list[Permission]`

```python
Field(default_factory=list)
```

<a id="access-accessstatus-csrf"></a>
### `access.AccessStatus.csrf`

[backend/app/schemas/access.py:102](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L102) · type `str`

```python
required / inherited validation
```

<a id="access-accessstatus-legacy_token"></a>
### `access.AccessStatus.legacy_token`

[backend/app/schemas/access.py:103](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L103) · type `bool`

```python
False
```

<a id="access-accessstatus-account_transport"></a>
### `access.AccessStatus.account_transport`

[backend/app/schemas/access.py:104](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L104) · type `Literal['https', 'local_http', 'blocked']`

```python
'blocked'
```

<a id="access-credentialcreate-label"></a>
### `access.CredentialCreate.label`

[backend/app/schemas/access.py:108](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L108) · type `str`

```python
Field(min_length=1, max_length=80)
```

<a id="access-credentialcreate-kind"></a>
### `access.CredentialCreate.kind`

[backend/app/schemas/access.py:109](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L109) · type `Literal['admin', 'playback']`

```python
'playback'
```

<a id="access-credentialview-id"></a>
### `access.CredentialView.id`

[backend/app/schemas/access.py:113](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L113) · type `str`

```python
required / inherited validation
```

<a id="access-credentialview-label"></a>
### `access.CredentialView.label`

[backend/app/schemas/access.py:114](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L114) · type `str`

```python
required / inherited validation
```

<a id="access-credentialview-kind"></a>
### `access.CredentialView.kind`

[backend/app/schemas/access.py:115](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L115) · type `Literal['admin', 'playback']`

```python
required / inherited validation
```

<a id="access-credentialview-created_at"></a>
### `access.CredentialView.created_at`

[backend/app/schemas/access.py:116](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L116) · type `float`

```python
required / inherited validation
```

<a id="access-credentialissued-token"></a>
### `access.CredentialIssued.token`

[backend/app/schemas/access.py:120](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L120) · type `str`

```python
required / inherited validation
```

<a id="access-sessionview-id"></a>
### `access.SessionView.id`

[backend/app/schemas/access.py:124](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L124) · type `str`

```python
required / inherited validation
```

<a id="access-sessionview-username"></a>
### `access.SessionView.username`

[backend/app/schemas/access.py:125](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L125) · type `str`

```python
required / inherited validation
```

<a id="access-sessionview-created_at"></a>
### `access.SessionView.created_at`

[backend/app/schemas/access.py:126](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L126) · type `float`

```python
required / inherited validation
```

<a id="access-sessionview-last_seen"></a>
### `access.SessionView.last_seen`

[backend/app/schemas/access.py:127](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L127) · type `float`

```python
required / inherited validation
```

<a id="access-sessionview-expires_at"></a>
### `access.SessionView.expires_at`

[backend/app/schemas/access.py:128](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L128) · type `float`

```python
required / inherited validation
```

<a id="access-disableaccess-current_password"></a>
### `access.DisableAccess.current_password`

[backend/app/schemas/access.py:132](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/access.py#L132) · type `SecretStr`

```python
required / inherited validation
```

<a id="base_url-baseurlbase-name"></a>
### `base_url.BaseUrlBase.name`

[backend/app/schemas/base_url.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/base_url.py#L24) · type `str`

```python
Field(..., min_length=1, max_length=255)
```

<a id="base_url-baseurlbase-pattern"></a>
### `base_url.BaseUrlBase.pattern`

[backend/app/schemas/base_url.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/base_url.py#L25) · type `str`

```python
Field(..., min_length=1, max_length=1024, description='Prefix, a stream mask using {channel_id} and optionally {pid}, or a TV relay mask using {tv_channel_id}')
```

<a id="base_url-baseurlbase-is_default"></a>
### `base_url.BaseUrlBase.is_default`

[backend/app/schemas/base_url.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/base_url.py#L27) · type `bool`

```python
False
```

<a id="base_url-baseurlupdate-name"></a>
### `base_url.BaseUrlUpdate.name`

[backend/app/schemas/base_url.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/base_url.py#L40) · type `Optional[str]`

```python
Field(None, min_length=1, max_length=255)
```

<a id="base_url-baseurlupdate-pattern"></a>
### `base_url.BaseUrlUpdate.pattern`

[backend/app/schemas/base_url.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/base_url.py#L41) · type `Optional[str]`

```python
Field(None, min_length=1, max_length=1024)
```

<a id="base_url-baseurlupdate-is_default"></a>
### `base_url.BaseUrlUpdate.is_default`

[backend/app/schemas/base_url.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/base_url.py#L42) · type `Optional[bool]`

```python
None
```

<a id="base_url-baseurlresponse-id"></a>
### `base_url.BaseUrlResponse.id`

[backend/app/schemas/base_url.py:53](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/base_url.py#L53) · type `int`

```python
required / inherited validation
```

<a id="cast-castdevice-id"></a>
### `cast.CastDevice.id`

[backend/app/schemas/cast.py:7](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L7) · type `str`

```python
required / inherited validation
```

<a id="cast-castdevice-name"></a>
### `cast.CastDevice.name`

[backend/app/schemas/cast.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L8) · type `str`

```python
required / inherited validation
```

<a id="cast-castdevice-model"></a>
### `cast.CastDevice.model`

[backend/app/schemas/cast.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L9) · type `str`

```python
required / inherited validation
```

<a id="cast-castcapabilities-server_devices"></a>
### `cast.CastCapabilities.server_devices`

[backend/app/schemas/cast.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L13) · type `bool`

```python
required / inherited validation
```

<a id="cast-castcapabilities-compatibility_conversion"></a>
### `cast.CastCapabilities.compatibility_conversion`

[backend/app/schemas/cast.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L14) · type `bool`

```python
required / inherited validation
```

<a id="cast-castcapabilities-media_url_configured"></a>
### `cast.CastCapabilities.media_url_configured`

[backend/app/schemas/cast.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L15) · type `bool`

```python
required / inherited validation
```

<a id="cast-castcapabilities-message"></a>
### `cast.CastCapabilities.message`

[backend/app/schemas/cast.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L16) · type `str`

```python
''
```

<a id="cast-castcapabilities-home_connection"></a>
### `cast.CastCapabilities.home_connection`

[backend/app/schemas/cast.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L17) · type `bool`

```python
False
```

<a id="cast-castcapabilities-media_url"></a>
### `cast.CastCapabilities.media_url`

[backend/app/schemas/cast.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L18) · type `str`

```python
''
```

<a id="cast-castcapabilities-home_check"></a>
### `cast.CastCapabilities.home_check`

[backend/app/schemas/cast.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L20) · type `Literal['off', 'deployment', 'accounts']`

```python
'off'
```

<a id="cast-caststart-device_id"></a>
### `cast.CastStart.device_id`

[backend/app/schemas/cast.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L24) · type `str | None`

```python
Field(default=None, max_length=64)
```

<a id="cast-caststart-compatibility"></a>
### `cast.CastStart.compatibility`

[backend/app/schemas/cast.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L25) · type `bool`

```python
False
```

<a id="cast-caststart-replace"></a>
### `cast.CastStart.replace`

[backend/app/schemas/cast.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L26) · type `bool`

```python
False
```

<a id="cast-caststatus-id"></a>
### `cast.CastStatus.id`

[backend/app/schemas/cast.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L30) · type `str`

```python
required / inherited validation
```

<a id="cast-caststatus-device_id"></a>
### `cast.CastStatus.device_id`

[backend/app/schemas/cast.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L31) · type `str`

```python
required / inherited validation
```

<a id="cast-caststatus-device_name"></a>
### `cast.CastStatus.device_name`

[backend/app/schemas/cast.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L32) · type `str`

```python
required / inherited validation
```

<a id="cast-caststatus-state"></a>
### `cast.CastStatus.state`

[backend/app/schemas/cast.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L33) · type `str`

```python
required / inherited validation
```

<a id="cast-caststatus-viewer_id"></a>
### `cast.CastStatus.viewer_id`

[backend/app/schemas/cast.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L34) · type `str`

```python
required / inherited validation
```

<a id="cast-caststatus-volume"></a>
### `cast.CastStatus.volume`

[backend/app/schemas/cast.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L35) · type `float | None`

```python
None
```

<a id="cast-castcommand-action"></a>
### `cast.CastCommand.action`

[backend/app/schemas/cast.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L39) · type `Literal['play', 'pause', 'stop', 'volume']`

```python
required / inherited validation
```

<a id="cast-castcommand-volume"></a>
### `cast.CastCommand.volume`

[backend/app/schemas/cast.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/cast.py#L40) · type `float | None`

```python
Field(default=None, ge=0, le=1)
```

<a id="catalogue-cataloguepreviewrequest-url"></a>
### `catalogue.CataloguePreviewRequest.url`

[backend/app/schemas/catalogue.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L8) · type `str | None`

```python
Field(default=None, max_length=2048)
```

<a id="catalogue-cataloguepreviewrequest-sample"></a>
### `catalogue.CataloguePreviewRequest.sample`

[backend/app/schemas/catalogue.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L9) · type `str | None`

```python
Field(default=None, max_length=4 * 1024 * 1024)
```

<a id="catalogue-cataloguepreviewrequest-catalogue_id"></a>
### `catalogue.CataloguePreviewRequest.catalogue_id`

[backend/app/schemas/catalogue.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L10) · type `int | None`

```python
Field(default=None, ge=1)
```

<a id="catalogue-catalogueentry-id"></a>
### `catalogue.CatalogueEntry.id`

[backend/app/schemas/catalogue.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L20) · type `str`

```python
required / inherited validation
```

<a id="catalogue-catalogueentry-parent_id"></a>
### `catalogue.CatalogueEntry.parent_id`

[backend/app/schemas/catalogue.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L21) · type `str | None`

```python
None
```

<a id="catalogue-catalogueentry-name"></a>
### `catalogue.CatalogueEntry.name`

[backend/app/schemas/catalogue.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L22) · type `str`

```python
required / inherited validation
```

<a id="catalogue-catalogueentry-kind"></a>
### `catalogue.CatalogueEntry.kind`

[backend/app/schemas/catalogue.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L23) · type `Literal['folder', 'acestream', 'hls', 'mpegts', 'resolver', 'vod', 'unsupported', 'invalid']`

```python
required / inherited validation
```

<a id="catalogue-catalogueentry-content_type"></a>
### `catalogue.CatalogueEntry.content_type`

[backend/app/schemas/catalogue.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L24) · type `Literal['live', 'event', 'vod', 'unknown']`

```python
'unknown'
```

<a id="catalogue-catalogueentry-reason"></a>
### `catalogue.CatalogueEntry.reason`

[backend/app/schemas/catalogue.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L25) · type `str`

```python
''
```

<a id="catalogue-catalogueentry-description"></a>
### `catalogue.CatalogueEntry.description`

[backend/app/schemas/catalogue.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L26) · type `str`

```python
''
```

<a id="catalogue-catalogueentry-image"></a>
### `catalogue.CatalogueEntry.image`

[backend/app/schemas/catalogue.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L27) · type `str | None`

```python
None
```

<a id="catalogue-catalogueentry-guide_id"></a>
### `catalogue.CatalogueEntry.guide_id`

[backend/app/schemas/catalogue.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L28) · type `str | None`

```python
None
```

<a id="catalogue-catalogueentry-number"></a>
### `catalogue.CatalogueEntry.number`

[backend/app/schemas/catalogue.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L29) · type `int | None`

```python
None
```

<a id="catalogue-catalogueentry-origin"></a>
### `catalogue.CatalogueEntry.origin`

[backend/app/schemas/catalogue.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L30) · type `str`

```python
''
```

<a id="catalogue-catalogueentry-header_names"></a>
### `catalogue.CatalogueEntry.header_names`

[backend/app/schemas/catalogue.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L31) · type `list[str]`

```python
Field(default_factory=list)
```

<a id="catalogue-catalogueentry-channel_id"></a>
### `catalogue.CatalogueEntry.channel_id`

[backend/app/schemas/catalogue.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L32) · type `str | None`

```python
None
```

<a id="catalogue-catalogueentry-duplicate"></a>
### `catalogue.CatalogueEntry.duplicate`

[backend/app/schemas/catalogue.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L33) · type `bool`

```python
False
```

<a id="catalogue-catalogueentry-retained"></a>
### `catalogue.CatalogueEntry.retained`

[backend/app/schemas/catalogue.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L34) · type `bool`

```python
False
```

<a id="catalogue-catalogueentry-imported"></a>
### `catalogue.CatalogueEntry.imported`

[backend/app/schemas/catalogue.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L35) · type `bool`

```python
False
```

<a id="catalogue-catalogueentry-excluded_rule_ids"></a>
### `catalogue.CatalogueEntry.excluded_rule_ids`

[backend/app/schemas/catalogue.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L36) · type `list[int]`

```python
Field(default_factory=list)
```

<a id="catalogue-cataloguecounts-excluded"></a>
### `catalogue.CatalogueCounts.excluded`

[backend/app/schemas/catalogue.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L40) · type `int`

```python
0
```

<a id="catalogue-cataloguecounts-accepted"></a>
### `catalogue.CatalogueCounts.accepted`

[backend/app/schemas/catalogue.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L41) · type `int`

```python
0
```

<a id="catalogue-cataloguecounts-duplicates"></a>
### `catalogue.CatalogueCounts.duplicates`

[backend/app/schemas/catalogue.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L42) · type `int`

```python
0
```

<a id="catalogue-cataloguecounts-invalid"></a>
### `catalogue.CatalogueCounts.invalid`

[backend/app/schemas/catalogue.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L43) · type `int`

```python
0
```

<a id="catalogue-cataloguecounts-unsupported"></a>
### `catalogue.CatalogueCounts.unsupported`

[backend/app/schemas/catalogue.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L44) · type `int`

```python
0
```

<a id="catalogue-cataloguecounts-failed_fetches"></a>
### `catalogue.CatalogueCounts.failed_fetches`

[backend/app/schemas/catalogue.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L45) · type `int`

```python
0
```

<a id="catalogue-cataloguecounts-requests"></a>
### `catalogue.CatalogueCounts.requests`

[backend/app/schemas/catalogue.py:46](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L46) · type `int`

```python
0
```

<a id="catalogue-cataloguecounts-bytes_read"></a>
### `catalogue.CatalogueCounts.bytes_read`

[backend/app/schemas/catalogue.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L47) · type `int`

```python
Field(default=0, description='Traversal byte budget used, including cached input and failed-read reservations')
```

<a id="catalogue-cataloguecounts-cached_documents"></a>
### `catalogue.CatalogueCounts.cached_documents`

[backend/app/schemas/catalogue.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L48) · type `int`

```python
0
```

<a id="catalogue-catalogueview-policy_revision"></a>
### `catalogue.CatalogueView.policy_revision`

[backend/app/schemas/catalogue.py:52](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L52) · type `int`

```python
0
```

<a id="catalogue-catalogueview-id"></a>
### `catalogue.CatalogueView.id`

[backend/app/schemas/catalogue.py:53](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L53) · type `int | None`

```python
None
```

<a id="catalogue-catalogueview-revision"></a>
### `catalogue.CatalogueView.revision`

[backend/app/schemas/catalogue.py:54](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L54) · type `int`

```python
0
```

<a id="catalogue-catalogueview-name"></a>
### `catalogue.CatalogueView.name`

[backend/app/schemas/catalogue.py:55](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L55) · type `str`

```python
required / inherited validation
```

<a id="catalogue-catalogueview-origin"></a>
### `catalogue.CatalogueView.origin`

[backend/app/schemas/catalogue.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L56) · type `str`

```python
required / inherited validation
```

<a id="catalogue-catalogueview-entries"></a>
### `catalogue.CatalogueView.entries`

[backend/app/schemas/catalogue.py:57](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L57) · type `list[CatalogueEntry]`

```python
required / inherited validation
```

<a id="catalogue-catalogueview-counts"></a>
### `catalogue.CatalogueView.counts`

[backend/app/schemas/catalogue.py:58](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L58) · type `CatalogueCounts`

```python
required / inherited validation
```

<a id="catalogue-catalogueview-partial"></a>
### `catalogue.CatalogueView.partial`

[backend/app/schemas/catalogue.py:59](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L59) · type `bool`

```python
False
```

<a id="catalogue-catalogueview-warnings"></a>
### `catalogue.CatalogueView.warnings`

[backend/app/schemas/catalogue.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L60) · type `list[str]`

```python
Field(default_factory=list)
```

<a id="catalogue-catalogueview-selected_branches"></a>
### `catalogue.CatalogueView.selected_branches`

[backend/app/schemas/catalogue.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L61) · type `list[str]`

```python
Field(default_factory=lambda: ['root'])
```

<a id="catalogue-catalogueview-mode"></a>
### `catalogue.CatalogueView.mode`

[backend/app/schemas/catalogue.py:62](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L62) · type `Literal['compatible', 'acestream']`

```python
'compatible'
```

<a id="catalogue-catalogueview-refresh_enabled"></a>
### `catalogue.CatalogueView.refresh_enabled`

[backend/app/schemas/catalogue.py:63](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L63) · type `bool`

```python
False
```

<a id="catalogue-catalogueview-can_refresh"></a>
### `catalogue.CatalogueView.can_refresh`

[backend/app/schemas/catalogue.py:64](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L64) · type `bool`

```python
False
```

<a id="catalogue-catalogueview-updated_at"></a>
### `catalogue.CatalogueView.updated_at`

[backend/app/schemas/catalogue.py:65](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L65) · type `datetime | None`

```python
None
```

<a id="catalogue-catalogueview-preview_token"></a>
### `catalogue.CatalogueView.preview_token`

[backend/app/schemas/catalogue.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L66) · type `str | None`

```python
None
```

<a id="catalogue-cataloguesaverequest-confirm_live"></a>
### `catalogue.CatalogueSaveRequest.confirm_live`

[backend/app/schemas/catalogue.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L70) · type `bool`

```python
False
```

<a id="catalogue-cataloguesaverequest-preview_token"></a>
### `catalogue.CatalogueSaveRequest.preview_token`

[backend/app/schemas/catalogue.py:71](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L71) · type `str`

```python
Field(min_length=1, max_length=100)
```

<a id="catalogue-cataloguesaverequest-name"></a>
### `catalogue.CatalogueSaveRequest.name`

[backend/app/schemas/catalogue.py:72](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L72) · type `str`

```python
Field(min_length=1, max_length=255)
```

<a id="catalogue-cataloguesaverequest-selected_branches"></a>
### `catalogue.CatalogueSaveRequest.selected_branches`

[backend/app/schemas/catalogue.py:73](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L73) · type `list[str]`

```python
Field(max_length=10000)
```

<a id="catalogue-cataloguesaverequest-mode"></a>
### `catalogue.CatalogueSaveRequest.mode`

[backend/app/schemas/catalogue.py:74](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L74) · type `Literal['compatible', 'acestream']`

```python
'compatible'
```

<a id="catalogue-cataloguesaverequest-refresh_enabled"></a>
### `catalogue.CatalogueSaveRequest.refresh_enabled`

[backend/app/schemas/catalogue.py:75](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L75) · type `bool`

```python
False
```

<a id="catalogue-tvchannelref-id"></a>
### `catalogue.TVChannelRef.id`

[backend/app/schemas/catalogue.py:79](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L79) · type `int`

```python
required / inherited validation
```

<a id="catalogue-tvchannelref-name"></a>
### `catalogue.TVChannelRef.name`

[backend/app/schemas/catalogue.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L80) · type `str`

```python
required / inherited validation
```

<a id="catalogue-folderassignrequest-tv_channel_id"></a>
### `catalogue.FolderAssignRequest.tv_channel_id`

[backend/app/schemas/catalogue.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L85) · type `int | None`

```python
Field(default=None, ge=1)
```

<a id="catalogue-folderassignrequest-create_name"></a>
### `catalogue.FolderAssignRequest.create_name`

[backend/app/schemas/catalogue.py:86](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L86) · type `str | None`

```python
Field(default=None, min_length=1, max_length=255)
```

<a id="catalogue-folderassignrequest-reassign"></a>
### `catalogue.FolderAssignRequest.reassign`

[backend/app/schemas/catalogue.py:87](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L87) · type `bool`

```python
False
```

<a id="catalogue-folderassignresult-tv_channel"></a>
### `catalogue.FolderAssignResult.tv_channel`

[backend/app/schemas/catalogue.py:97](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L97) · type `TVChannelRef`

```python
required / inherited validation
```

<a id="catalogue-folderassignresult-assigned"></a>
### `catalogue.FolderAssignResult.assigned`

[backend/app/schemas/catalogue.py:98](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L98) · type `int`

```python
0
```

<a id="catalogue-folderassignresult-already"></a>
### `catalogue.FolderAssignResult.already`

[backend/app/schemas/catalogue.py:99](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L99) · type `int`

```python
0
```

<a id="catalogue-folderassignresult-moved"></a>
### `catalogue.FolderAssignResult.moved`

[backend/app/schemas/catalogue.py:100](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L100) · type `int`

```python
0
```

<a id="catalogue-folderassignresult-skipped_other_channel"></a>
### `catalogue.FolderAssignResult.skipped_other_channel`

[backend/app/schemas/catalogue.py:101](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L101) · type `int`

```python
0
```

<a id="catalogue-folderassignresult-skipped_not_imported"></a>
### `catalogue.FolderAssignResult.skipped_not_imported`

[backend/app/schemas/catalogue.py:102](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L102) · type `int`

```python
0
```

<a id="catalogue-foldermatchrow-folder_id"></a>
### `catalogue.FolderMatchRow.folder_id`

[backend/app/schemas/catalogue.py:106](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L106) · type `str`

```python
required / inherited validation
```

<a id="catalogue-foldermatchrow-name"></a>
### `catalogue.FolderMatchRow.name`

[backend/app/schemas/catalogue.py:107](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L107) · type `str`

```python
required / inherited validation
```

<a id="catalogue-foldermatchrow-path"></a>
### `catalogue.FolderMatchRow.path`

[backend/app/schemas/catalogue.py:108](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L108) · type `str`

```python
required / inherited validation
```

<a id="catalogue-foldermatchrow-stream_count"></a>
### `catalogue.FolderMatchRow.stream_count`

[backend/app/schemas/catalogue.py:109](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L109) · type `int`

```python
required / inherited validation
```

<a id="catalogue-foldermatchrow-candidate"></a>
### `catalogue.FolderMatchRow.candidate`

[backend/app/schemas/catalogue.py:110](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L110) · type `TVChannelRef | None`

```python
None
```

<a id="catalogue-foldermatchrow-current"></a>
### `catalogue.FolderMatchRow.current`

[backend/app/schemas/catalogue.py:111](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L111) · type `TVChannelRef | None`

```python
None
```

<a id="catalogue-foldermatchrow-status"></a>
### `catalogue.FolderMatchRow.status`

[backend/app/schemas/catalogue.py:112](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L112) · type `Literal['match', 'ambiguous', 'none', 'assigned']`

```python
required / inherited validation
```

<a id="catalogue-foldermatchpreview-rows"></a>
### `catalogue.FolderMatchPreview.rows`

[backend/app/schemas/catalogue.py:116](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L116) · type `list[FolderMatchRow]`

```python
required / inherited validation
```

<a id="catalogue-foldermatchassignment-folder_id"></a>
### `catalogue.FolderMatchAssignment.folder_id`

[backend/app/schemas/catalogue.py:120](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L120) · type `str`

```python
Field(min_length=1, max_length=200)
```

<a id="catalogue-foldermatchassignment-tv_channel_id"></a>
### `catalogue.FolderMatchAssignment.tv_channel_id`

[backend/app/schemas/catalogue.py:121](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L121) · type `int | None`

```python
Field(default=None, ge=1)
```

<a id="catalogue-foldermatchassignment-create"></a>
### `catalogue.FolderMatchAssignment.create`

[backend/app/schemas/catalogue.py:122](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L122) · type `bool`

```python
False
```

<a id="catalogue-foldermatchapplyrequest-assignments"></a>
### `catalogue.FolderMatchApplyRequest.assignments`

[backend/app/schemas/catalogue.py:132](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L132) · type `list[FolderMatchAssignment]`

```python
Field(min_length=1, max_length=2000)
```

<a id="catalogue-foldermatchapplyrequest-reassign"></a>
### `catalogue.FolderMatchApplyRequest.reassign`

[backend/app/schemas/catalogue.py:133](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L133) · type `bool`

```python
False
```

<a id="catalogue-folderapplyrow-folder_id"></a>
### `catalogue.FolderApplyRow.folder_id`

[backend/app/schemas/catalogue.py:137](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L137) · type `str`

```python
required / inherited validation
```

<a id="catalogue-folderapplyrow-tv_channel"></a>
### `catalogue.FolderApplyRow.tv_channel`

[backend/app/schemas/catalogue.py:138](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L138) · type `TVChannelRef | None`

```python
None
```

<a id="catalogue-folderapplyrow-assigned"></a>
### `catalogue.FolderApplyRow.assigned`

[backend/app/schemas/catalogue.py:139](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L139) · type `int`

```python
0
```

<a id="catalogue-folderapplyrow-already"></a>
### `catalogue.FolderApplyRow.already`

[backend/app/schemas/catalogue.py:140](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L140) · type `int`

```python
0
```

<a id="catalogue-folderapplyrow-moved"></a>
### `catalogue.FolderApplyRow.moved`

[backend/app/schemas/catalogue.py:141](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L141) · type `int`

```python
0
```

<a id="catalogue-folderapplyrow-skipped_other_channel"></a>
### `catalogue.FolderApplyRow.skipped_other_channel`

[backend/app/schemas/catalogue.py:142](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L142) · type `int`

```python
0
```

<a id="catalogue-folderapplyrow-skipped_not_imported"></a>
### `catalogue.FolderApplyRow.skipped_not_imported`

[backend/app/schemas/catalogue.py:143](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L143) · type `int`

```python
0
```

<a id="catalogue-folderapplyrow-note"></a>
### `catalogue.FolderApplyRow.note`

[backend/app/schemas/catalogue.py:144](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L144) · type `str`

```python
''
```

<a id="catalogue-foldermatchapplyresult-results"></a>
### `catalogue.FolderMatchApplyResult.results`

[backend/app/schemas/catalogue.py:148](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L148) · type `list[FolderApplyRow]`

```python
required / inherited validation
```

<a id="catalogue-cataloguesummary-id"></a>
### `catalogue.CatalogueSummary.id`

[backend/app/schemas/catalogue.py:152](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L152) · type `int`

```python
required / inherited validation
```

<a id="catalogue-cataloguesummary-name"></a>
### `catalogue.CatalogueSummary.name`

[backend/app/schemas/catalogue.py:153](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L153) · type `str`

```python
required / inherited validation
```

<a id="catalogue-cataloguesummary-revision"></a>
### `catalogue.CatalogueSummary.revision`

[backend/app/schemas/catalogue.py:154](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L154) · type `int`

```python
required / inherited validation
```

<a id="catalogue-cataloguesummary-origin"></a>
### `catalogue.CatalogueSummary.origin`

[backend/app/schemas/catalogue.py:155](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L155) · type `str`

```python
required / inherited validation
```

<a id="catalogue-cataloguesummary-partial"></a>
### `catalogue.CatalogueSummary.partial`

[backend/app/schemas/catalogue.py:156](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L156) · type `bool`

```python
required / inherited validation
```

<a id="catalogue-cataloguesummary-refresh_enabled"></a>
### `catalogue.CatalogueSummary.refresh_enabled`

[backend/app/schemas/catalogue.py:157](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L157) · type `bool`

```python
required / inherited validation
```

<a id="catalogue-cataloguesummary-updated_at"></a>
### `catalogue.CatalogueSummary.updated_at`

[backend/app/schemas/catalogue.py:158](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L158) · type `datetime`

```python
required / inherited validation
```

<a id="catalogue-catalogueeventpreviewrequest-revision"></a>
### `catalogue.CatalogueEventPreviewRequest.revision`

[backend/app/schemas/catalogue.py:165](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L165) · type `int`

```python
Field(ge=1)
```

<a id="catalogue-catalogueeventpreviewrequest-entry_ids"></a>
### `catalogue.CatalogueEventPreviewRequest.entry_ids`

[backend/app/schemas/catalogue.py:166](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L166) · type `list[str]`

```python
Field(min_length=1, max_length=50)
```

<a id="catalogue-catalogueeventpreviewrequest-event_id"></a>
### `catalogue.CatalogueEventPreviewRequest.event_id`

[backend/app/schemas/catalogue.py:167](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/catalogue.py#L167) · type `str | None`

```python
Field(default=None, pattern='^[0-9a-f]{32}$')
```

<a id="channel-channelsourcefilter-value"></a>
### `channel.ChannelSourceFilter.value`

[backend/app/schemas/channel.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L14) · type `str`

```python
required / inherited validation
```

<a id="channel-channelsourcefilter-label"></a>
### `channel.ChannelSourceFilter.label`

[backend/app/schemas/channel.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L15) · type `str`

```python
required / inherited validation
```

<a id="channel-channelsourcefilter-kind"></a>
### `channel.ChannelSourceFilter.kind`

[backend/app/schemas/channel.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L16) · type `Literal['scrape', 'broadcaster', 'catalogue', 'import']`

```python
required / inherited validation
```

<a id="channel-acestreamchannelbase-id"></a>
### `channel.AcestreamChannelBase.id`

[backend/app/schemas/channel.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L21) · type `str`

```python
Field(..., description='Acestream channel ID (required, GUID string)')
```

<a id="channel-acestreamchannelbase-name"></a>
### `channel.AcestreamChannelBase.name`

[backend/app/schemas/channel.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L22) · type `str`

```python
Field(..., min_length=1)
```

<a id="channel-acestreamchannelcreate-allow_excluded"></a>
### `channel.AcestreamChannelCreate.allow_excluded`

[backend/app/schemas/channel.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L28) · type `bool`

```python
False
```

<a id="channel-acestreamchannelcreate-tv_channel_id"></a>
### `channel.AcestreamChannelCreate.tv_channel_id`

[backend/app/schemas/channel.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L29) · type `Optional[int]`

```python
Field(None, gt=0, description='Optionally link the stream to an existing TV channel in the same transaction.')
```

<a id="channel-acestreamchannelcreate-source_url"></a>
### `channel.AcestreamChannelCreate.source_url`

[backend/app/schemas/channel.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L30) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelcreate-group"></a>
### `channel.AcestreamChannelCreate.group`

[backend/app/schemas/channel.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L31) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelcreate-logo"></a>
### `channel.AcestreamChannelCreate.logo`

[backend/app/schemas/channel.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L32) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelcreate-tvg_id"></a>
### `channel.AcestreamChannelCreate.tvg_id`

[backend/app/schemas/channel.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L33) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelcreate-tvg_name"></a>
### `channel.AcestreamChannelCreate.tvg_name`

[backend/app/schemas/channel.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L34) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelcreate-is_online"></a>
### `channel.AcestreamChannelCreate.is_online`

[backend/app/schemas/channel.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L35) · type `Optional[bool]`

```python
None
```

<a id="channel-acestreamchannelupdate-name"></a>
### `channel.AcestreamChannelUpdate.name`

[backend/app/schemas/channel.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L41) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelupdate-group"></a>
### `channel.AcestreamChannelUpdate.group`

[backend/app/schemas/channel.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L42) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelupdate-logo"></a>
### `channel.AcestreamChannelUpdate.logo`

[backend/app/schemas/channel.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L43) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelupdate-tvg_id"></a>
### `channel.AcestreamChannelUpdate.tvg_id`

[backend/app/schemas/channel.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L44) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelupdate-tvg_name"></a>
### `channel.AcestreamChannelUpdate.tvg_name`

[backend/app/schemas/channel.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L45) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelupdate-source_url"></a>
### `channel.AcestreamChannelUpdate.source_url`

[backend/app/schemas/channel.py:46](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L46) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelupdate-is_active"></a>
### `channel.AcestreamChannelUpdate.is_active`

[backend/app/schemas/channel.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L47) · type `Optional[bool]`

```python
None
```

<a id="channel-acestreamchannelupdate-is_online"></a>
### `channel.AcestreamChannelUpdate.is_online`

[backend/app/schemas/channel.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L48) · type `Optional[bool]`

```python
None
```

<a id="channel-acestreamchannelupdate-tv_channel_id"></a>
### `channel.AcestreamChannelUpdate.tv_channel_id`

[backend/app/schemas/channel.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L49) · type `Optional[int]`

```python
None
```

<a id="channel-acestreamchannelupdate-epg_update_protected"></a>
### `channel.AcestreamChannelUpdate.epg_update_protected`

[backend/app/schemas/channel.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L50) · type `Optional[bool]`

```python
None
```

<a id="channel-acestreamchannelresponse-source_url"></a>
### `channel.AcestreamChannelResponse.source_url`

[backend/app/schemas/channel.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L56) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelresponse-group"></a>
### `channel.AcestreamChannelResponse.group`

[backend/app/schemas/channel.py:57](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L57) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelresponse-logo"></a>
### `channel.AcestreamChannelResponse.logo`

[backend/app/schemas/channel.py:58](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L58) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelresponse-tvg_id"></a>
### `channel.AcestreamChannelResponse.tvg_id`

[backend/app/schemas/channel.py:59](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L59) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelresponse-tvg_name"></a>
### `channel.AcestreamChannelResponse.tvg_name`

[backend/app/schemas/channel.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L60) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelresponse-last_seen"></a>
### `channel.AcestreamChannelResponse.last_seen`

[backend/app/schemas/channel.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L61) · type `datetime`

```python
required / inherited validation
```

<a id="channel-acestreamchannelresponse-is_active"></a>
### `channel.AcestreamChannelResponse.is_active`

[backend/app/schemas/channel.py:62](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L62) · type `bool`

```python
required / inherited validation
```

<a id="channel-acestreamchannelresponse-is_online"></a>
### `channel.AcestreamChannelResponse.is_online`

[backend/app/schemas/channel.py:63](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L63) · type `Optional[bool]`

```python
None
```

<a id="channel-acestreamchannelresponse-network_status"></a>
### `channel.AcestreamChannelResponse.network_status`

[backend/app/schemas/channel.py:64](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L64) · type `Optional[Literal['found', 'not_found', 'unknown']]`

```python
Field(None, description='Last engine ID lookup: found, explicitly not found, or inconclusive; not proof of permanent network existence')
```

<a id="channel-acestreamchannelresponse-id_kind"></a>
### `channel.AcestreamChannelResponse.id_kind`

[backend/app/schemas/channel.py:65](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L65) · type `Optional[Literal['id', 'infohash']]`

```python
Field(None, description='Which getstream parameter the engine accepted for this id; null means it has not been confirmed yet')
```

<a id="channel-acestreamchannelresponse-last_checked"></a>
### `channel.AcestreamChannelResponse.last_checked`

[backend/app/schemas/channel.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L66) · type `Optional[datetime]`

```python
None
```

<a id="channel-acestreamchannelresponse-offline_since"></a>
### `channel.AcestreamChannelResponse.offline_since`

[backend/app/schemas/channel.py:67](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L67) · type `Optional[datetime]`

```python
None
```

<a id="channel-acestreamchannelresponse-check_error"></a>
### `channel.AcestreamChannelResponse.check_error`

[backend/app/schemas/channel.py:68](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L68) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelresponse-stream_stats"></a>
### `channel.AcestreamChannelResponse.stream_stats`

[backend/app/schemas/channel.py:69](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L69) · type `Optional[StreamStats]`

```python
None
```

<a id="channel-acestreamchannelresponse-audio_tracks"></a>
### `channel.AcestreamChannelResponse.audio_tracks`

[backend/app/schemas/channel.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L70) · type `Optional[List[AudioTrack]]`

```python
Field(None, description='Audio tracks found at the last successful media probe; null means unknown')
```

<a id="channel-acestreamchannelresponse-bitrate_bps"></a>
### `channel.AcestreamChannelResponse.bitrate_bps`

[backend/app/schemas/channel.py:71](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L71) · type `Optional[int]`

```python
Field(None, ge=1, description='Last measured encoded media bitrate in bits per second; not P2P download speed')
```

<a id="channel-acestreamchannelresponse-bitrate_checked_at"></a>
### `channel.AcestreamChannelResponse.bitrate_checked_at`

[backend/app/schemas/channel.py:72](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L72) · type `Optional[datetime]`

```python
None
```

<a id="channel-acestreamchannelresponse-stream_order"></a>
### `channel.AcestreamChannelResponse.stream_order`

[backend/app/schemas/channel.py:73](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L73) · type `Optional[int]`

```python
Field(None, ge=1, description='Priority preference order among streams for this channel; 1 is highest priority.')
```

<a id="channel-acestreamchannelresponse-tv_channel_id"></a>
### `channel.AcestreamChannelResponse.tv_channel_id`

[backend/app/schemas/channel.py:74](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L74) · type `Optional[int]`

```python
None
```

<a id="channel-acestreamchannelresponse-tv_channel_name"></a>
### `channel.AcestreamChannelResponse.tv_channel_name`

[backend/app/schemas/channel.py:75](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L75) · type `Optional[str]`

```python
None
```

<a id="channel-acestreamchannelresponse-tv_channel_is_favorite"></a>
### `channel.AcestreamChannelResponse.tv_channel_is_favorite`

[backend/app/schemas/channel.py:76](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L76) · type `Optional[bool]`

```python
None
```

<a id="channel-acestreamchannelresponse-epg_update_protected"></a>
### `channel.AcestreamChannelResponse.epg_update_protected`

[backend/app/schemas/channel.py:77](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L77) · type `Optional[bool]`

```python
False
```

<a id="channel-tvchannelbase-name"></a>
### `channel.TVChannelBase.name`

[backend/app/schemas/channel.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L84) · type `str`

```python
required / inherited validation
```

<a id="channel-tvchannelbase-logo_url"></a>
### `channel.TVChannelBase.logo_url`

[backend/app/schemas/channel.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L85) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbase-description"></a>
### `channel.TVChannelBase.description`

[backend/app/schemas/channel.py:86](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L86) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbase-category"></a>
### `channel.TVChannelBase.category`

[backend/app/schemas/channel.py:87](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L87) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbase-country"></a>
### `channel.TVChannelBase.country`

[backend/app/schemas/channel.py:88](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L88) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbase-language"></a>
### `channel.TVChannelBase.language`

[backend/app/schemas/channel.py:89](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L89) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbase-website"></a>
### `channel.TVChannelBase.website`

[backend/app/schemas/channel.py:90](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L90) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbase-epg_id"></a>
### `channel.TVChannelBase.epg_id`

[backend/app/schemas/channel.py:91](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L91) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbase-channel_number"></a>
### `channel.TVChannelBase.channel_number`

[backend/app/schemas/channel.py:92](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L92) · type `Optional[int]`

```python
None
```

<a id="channel-tvchannelcreate-is_active"></a>
### `channel.TVChannelCreate.is_active`

[backend/app/schemas/channel.py:97](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L97) · type `Optional[bool]`

```python
True
```

<a id="channel-tvchannelcreate-is_favorite"></a>
### `channel.TVChannelCreate.is_favorite`

[backend/app/schemas/channel.py:98](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L98) · type `Optional[bool]`

```python
False
```

<a id="channel-tvchannelcreate-epg_source_id"></a>
### `channel.TVChannelCreate.epg_source_id`

[backend/app/schemas/channel.py:99](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L99) · type `Optional[int]`

```python
None
```

<a id="channel-tvchannelupdate-name"></a>
### `channel.TVChannelUpdate.name`

[backend/app/schemas/channel.py:104](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L104) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelupdate-logo_url"></a>
### `channel.TVChannelUpdate.logo_url`

[backend/app/schemas/channel.py:105](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L105) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelupdate-description"></a>
### `channel.TVChannelUpdate.description`

[backend/app/schemas/channel.py:106](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L106) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelupdate-category"></a>
### `channel.TVChannelUpdate.category`

[backend/app/schemas/channel.py:107](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L107) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelupdate-country"></a>
### `channel.TVChannelUpdate.country`

[backend/app/schemas/channel.py:108](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L108) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelupdate-language"></a>
### `channel.TVChannelUpdate.language`

[backend/app/schemas/channel.py:109](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L109) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelupdate-website"></a>
### `channel.TVChannelUpdate.website`

[backend/app/schemas/channel.py:110](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L110) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelupdate-epg_id"></a>
### `channel.TVChannelUpdate.epg_id`

[backend/app/schemas/channel.py:111](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L111) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelupdate-is_active"></a>
### `channel.TVChannelUpdate.is_active`

[backend/app/schemas/channel.py:112](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L112) · type `Optional[bool]`

```python
None
```

<a id="channel-tvchannelupdate-is_favorite"></a>
### `channel.TVChannelUpdate.is_favorite`

[backend/app/schemas/channel.py:113](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L113) · type `Optional[bool]`

```python
None
```

<a id="channel-tvchannelupdate-channel_number"></a>
### `channel.TVChannelUpdate.channel_number`

[backend/app/schemas/channel.py:114](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L114) · type `Optional[int]`

```python
None
```

<a id="channel-tvchannelupdate-epg_source_id"></a>
### `channel.TVChannelUpdate.epg_source_id`

[backend/app/schemas/channel.py:115](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L115) · type `Optional[int]`

```python
None
```

<a id="channel-tvchannelresponse-id"></a>
### `channel.TVChannelResponse.id`

[backend/app/schemas/channel.py:121](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L121) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelresponse-epg_source_id"></a>
### `channel.TVChannelResponse.epg_source_id`

[backend/app/schemas/channel.py:122](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L122) · type `Optional[int]`

```python
None
```

<a id="channel-tvchannelresponse-created_at"></a>
### `channel.TVChannelResponse.created_at`

[backend/app/schemas/channel.py:123](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L123) · type `datetime`

```python
required / inherited validation
```

<a id="channel-tvchannelresponse-updated_at"></a>
### `channel.TVChannelResponse.updated_at`

[backend/app/schemas/channel.py:124](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L124) · type `datetime`

```python
required / inherited validation
```

<a id="channel-tvchannelresponse-is_active"></a>
### `channel.TVChannelResponse.is_active`

[backend/app/schemas/channel.py:125](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L125) · type `bool`

```python
required / inherited validation
```

<a id="channel-tvchannelresponse-is_favorite"></a>
### `channel.TVChannelResponse.is_favorite`

[backend/app/schemas/channel.py:126](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L126) · type `bool`

```python
required / inherited validation
```

<a id="channel-tvchannelresponse-acestream_channels"></a>
### `channel.TVChannelResponse.acestream_channels`

[backend/app/schemas/channel.py:127](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L127) · type `List[AcestreamChannelResponse]`

```python
[]
```

<a id="channel-channelstatuscheck-total_channels"></a>
### `channel.ChannelStatusCheck.total_channels`

[backend/app/schemas/channel.py:139](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L139) · type `int`

```python
required / inherited validation
```

<a id="channel-channelstatuscheck-online_count"></a>
### `channel.ChannelStatusCheck.online_count`

[backend/app/schemas/channel.py:140](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L140) · type `int`

```python
required / inherited validation
```

<a id="channel-channelstatuscheck-offline_count"></a>
### `channel.ChannelStatusCheck.offline_count`

[backend/app/schemas/channel.py:141](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L141) · type `int`

```python
required / inherited validation
```

<a id="channel-channelstatuscheck-status_details"></a>
### `channel.ChannelStatusCheck.status_details`

[backend/app/schemas/channel.py:142](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L142) · type `Dict[str, Any]`

```python
required / inherited validation
```

<a id="channel-acestreamchannellistresponse-items"></a>
### `channel.AcestreamChannelListResponse.items`

[backend/app/schemas/channel.py:148](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L148) · type `List[AcestreamChannelResponse]`

```python
required / inherited validation
```

<a id="channel-acestreamchannellistresponse-total"></a>
### `channel.AcestreamChannelListResponse.total`

[backend/app/schemas/channel.py:149](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L149) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannellistresponse-items"></a>
### `channel.TVChannelListResponse.items`

[backend/app/schemas/channel.py:154](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L154) · type `List[TVChannelResponse]`

```python
required / inherited validation
```

<a id="channel-tvchannellistresponse-total"></a>
### `channel.TVChannelListResponse.total`

[backend/app/schemas/channel.py:155](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L155) · type `int`

```python
required / inherited validation
```

<a id="channel-bulkchanneleditrequest-acestreamchannel_ids"></a>
### `channel.BulkChannelEditRequest.acestreamchannel_ids`

[backend/app/schemas/channel.py:160](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L160) · type `List[str]`

```python
required / inherited validation
```

<a id="channel-bulkchanneleditrequest-fields"></a>
### `channel.BulkChannelEditRequest.fields`

[backend/app/schemas/channel.py:161](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L161) · type `AcestreamChannelUpdate`

```python
required / inherited validation
```

<a id="channel-bulkchannelactivaterequest-acestreamchannel_ids"></a>
### `channel.BulkChannelActivateRequest.acestreamchannel_ids`

[backend/app/schemas/channel.py:166](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L166) · type `List[str]`

```python
required / inherited validation
```

<a id="channel-bulkchannelactivaterequest-active"></a>
### `channel.BulkChannelActivateRequest.active`

[backend/app/schemas/channel.py:167](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L167) · type `bool`

```python
True
```

<a id="channel-tvchannelassociationrequest-acestream_channel_id"></a>
### `channel.TVChannelAssociationRequest.acestream_channel_id`

[backend/app/schemas/channel.py:172](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L172) · type `str`

```python
required / inherited validation
```

<a id="channel-tvchannelbatchassignmentitem-tv_channel_id"></a>
### `channel.TVChannelBatchAssignmentItem.tv_channel_id`

[backend/app/schemas/channel.py:177](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L177) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelbatchassignmentitem-acestream_channel_id"></a>
### `channel.TVChannelBatchAssignmentItem.acestream_channel_id`

[backend/app/schemas/channel.py:178](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L178) · type `str`

```python
required / inherited validation
```

<a id="channel-tvchannelbatchassignrequest-assignments"></a>
### `channel.TVChannelBatchAssignRequest.assignments`

[backend/app/schemas/channel.py:183](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L183) · type `List[TVChannelBatchAssignmentItem]`

```python
required / inherited validation
```

<a id="channel-tvchannelbatchassignresponse-success_count"></a>
### `channel.TVChannelBatchAssignResponse.success_count`

[backend/app/schemas/channel.py:188](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L188) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelbatchassignresponse-failure_count"></a>
### `channel.TVChannelBatchAssignResponse.failure_count`

[backend/app/schemas/channel.py:189](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L189) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelbatchassignresponse-details"></a>
### `channel.TVChannelBatchAssignResponse.details`

[backend/app/schemas/channel.py:190](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L190) · type `Dict[str, Dict[str, List[str]]]`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepgrequest-epg_channel_ids"></a>
### `channel.TVChannelCreateFromEPGRequest.epg_channel_ids`

[backend/app/schemas/channel.py:194](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L194) · type `List[int]`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepgresponse-created_count"></a>
### `channel.TVChannelCreateFromEPGResponse.created_count`

[backend/app/schemas/channel.py:198](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L198) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepgresponse-skipped_count"></a>
### `channel.TVChannelCreateFromEPGResponse.skipped_count`

[backend/app/schemas/channel.py:199](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L199) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepgresponse-associated_count"></a>
### `channel.TVChannelCreateFromEPGResponse.associated_count`

[backend/app/schemas/channel.py:200](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L200) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepgresponse-items"></a>
### `channel.TVChannelCreateFromEPGResponse.items`

[backend/app/schemas/channel.py:201](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L201) · type `List[TVChannelResponse]`

```python
required / inherited validation
```

<a id="channel-epgmatchanalysisrequest-strictness"></a>
### `channel.EPGMatchAnalysisRequest.strictness`

[backend/app/schemas/channel.py:208](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L208) · type `MatchStrictness`

```python
required / inherited validation
```

<a id="channel-epgmatchanalysisrequest-source_id"></a>
### `channel.EPGMatchAnalysisRequest.source_id`

[backend/app/schemas/channel.py:209](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L209) · type `Optional[int]`

```python
None
```

<a id="channel-epgmatchcandidateresponse-acestream_channel_id"></a>
### `channel.EPGMatchCandidateResponse.acestream_channel_id`

[backend/app/schemas/channel.py:213](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L213) · type `str`

```python
required / inherited validation
```

<a id="channel-epgmatchcandidateresponse-name"></a>
### `channel.EPGMatchCandidateResponse.name`

[backend/app/schemas/channel.py:214](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L214) · type `str`

```python
required / inherited validation
```

<a id="channel-epgmatchcandidateresponse-tvg_id"></a>
### `channel.EPGMatchCandidateResponse.tvg_id`

[backend/app/schemas/channel.py:215](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L215) · type `Optional[str]`

```python
None
```

<a id="channel-epgmatchcandidateresponse-tvg_name"></a>
### `channel.EPGMatchCandidateResponse.tvg_name`

[backend/app/schemas/channel.py:216](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L216) · type `Optional[str]`

```python
None
```

<a id="channel-epgmatchcandidateresponse-score"></a>
### `channel.EPGMatchCandidateResponse.score`

[backend/app/schemas/channel.py:217](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L217) · type `float`

```python
required / inherited validation
```

<a id="channel-epgmatchcandidateresponse-match_stage"></a>
### `channel.EPGMatchCandidateResponse.match_stage`

[backend/app/schemas/channel.py:218](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L218) · type `str`

```python
required / inherited validation
```

<a id="channel-epgmatchrowresponse-epg_channel_id"></a>
### `channel.EPGMatchRowResponse.epg_channel_id`

[backend/app/schemas/channel.py:222](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L222) · type `int`

```python
required / inherited validation
```

<a id="channel-epgmatchrowresponse-epg_channel_xml_id"></a>
### `channel.EPGMatchRowResponse.epg_channel_xml_id`

[backend/app/schemas/channel.py:223](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L223) · type `str`

```python
required / inherited validation
```

<a id="channel-epgmatchrowresponse-epg_channel_name"></a>
### `channel.EPGMatchRowResponse.epg_channel_name`

[backend/app/schemas/channel.py:224](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L224) · type `str`

```python
required / inherited validation
```

<a id="channel-epgmatchrowresponse-epg_source_id"></a>
### `channel.EPGMatchRowResponse.epg_source_id`

[backend/app/schemas/channel.py:225](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L225) · type `int`

```python
required / inherited validation
```

<a id="channel-epgmatchrowresponse-epg_source_name"></a>
### `channel.EPGMatchRowResponse.epg_source_name`

[backend/app/schemas/channel.py:226](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L226) · type `Optional[str]`

```python
None
```

<a id="channel-epgmatchrowresponse-existing_tv_channel_id"></a>
### `channel.EPGMatchRowResponse.existing_tv_channel_id`

[backend/app/schemas/channel.py:227](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L227) · type `Optional[int]`

```python
None
```

<a id="channel-epgmatchrowresponse-existing_tv_channel_count"></a>
### `channel.EPGMatchRowResponse.existing_tv_channel_count`

[backend/app/schemas/channel.py:228](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L228) · type `int`

```python
0
```

<a id="channel-epgmatchrowresponse-has_duplicate_existing_conflict"></a>
### `channel.EPGMatchRowResponse.has_duplicate_existing_conflict`

[backend/app/schemas/channel.py:229](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L229) · type `bool`

```python
False
```

<a id="channel-epgmatchrowresponse-candidate_count"></a>
### `channel.EPGMatchRowResponse.candidate_count`

[backend/app/schemas/channel.py:230](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L230) · type `int`

```python
required / inherited validation
```

<a id="channel-epgmatchrowresponse-candidates"></a>
### `channel.EPGMatchRowResponse.candidates`

[backend/app/schemas/channel.py:231](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L231) · type `List[EPGMatchCandidateResponse]`

```python
required / inherited validation
```

<a id="channel-epgmatchrowresponse-best_match_type"></a>
### `channel.EPGMatchRowResponse.best_match_type`

[backend/app/schemas/channel.py:232](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L232) · type `Optional[str]`

```python
None
```

<a id="channel-epgmatchrowresponse-best_match_confidence"></a>
### `channel.EPGMatchRowResponse.best_match_confidence`

[backend/app/schemas/channel.py:233](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L233) · type `Optional[str]`

```python
None
```

<a id="channel-epgmatchrowresponse-is_creatable"></a>
### `channel.EPGMatchRowResponse.is_creatable`

[backend/app/schemas/channel.py:234](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L234) · type `bool`

```python
required / inherited validation
```

<a id="channel-epgmatchrowresponse-can_apply"></a>
### `channel.EPGMatchRowResponse.can_apply`

[backend/app/schemas/channel.py:235](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L235) · type `bool`

```python
False
```

<a id="channel-epgmatchrowresponse-automation_safe"></a>
### `channel.EPGMatchRowResponse.automation_safe`

[backend/app/schemas/channel.py:236](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L236) · type `bool`

```python
False
```

<a id="channel-epgmatchrowresponse-ambiguous_count"></a>
### `channel.EPGMatchRowResponse.ambiguous_count`

[backend/app/schemas/channel.py:237](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L237) · type `int`

```python
0
```

<a id="channel-epgmatchrowresponse-review_token"></a>
### `channel.EPGMatchRowResponse.review_token`

[backend/app/schemas/channel.py:238](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L238) · type `str`

```python
''
```

<a id="channel-epgmatchanalysissummaryresponse-epg_channels_analyzed"></a>
### `channel.EPGMatchAnalysisSummaryResponse.epg_channels_analyzed`

[backend/app/schemas/channel.py:242](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L242) · type `int`

```python
required / inherited validation
```

<a id="channel-epgmatchanalysissummaryresponse-matched_epg_channels"></a>
### `channel.EPGMatchAnalysisSummaryResponse.matched_epg_channels`

[backend/app/schemas/channel.py:243](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L243) · type `int`

```python
required / inherited validation
```

<a id="channel-epgmatchanalysissummaryresponse-matched_acestream_channels"></a>
### `channel.EPGMatchAnalysisSummaryResponse.matched_acestream_channels`

[backend/app/schemas/channel.py:244](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L244) · type `int`

```python
required / inherited validation
```

<a id="channel-epgmatchanalysissummaryresponse-creatable_rows"></a>
### `channel.EPGMatchAnalysisSummaryResponse.creatable_rows`

[backend/app/schemas/channel.py:245](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L245) · type `int`

```python
required / inherited validation
```

<a id="channel-epgmatchanalysissummaryresponse-skipped_existing_tv_channels"></a>
### `channel.EPGMatchAnalysisSummaryResponse.skipped_existing_tv_channels`

[backend/app/schemas/channel.py:246](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L246) · type `int`

```python
required / inherited validation
```

<a id="channel-epgmatchanalysisresponse-summary"></a>
### `channel.EPGMatchAnalysisResponse.summary`

[backend/app/schemas/channel.py:250](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L250) · type `EPGMatchAnalysisSummaryResponse`

```python
required / inherited validation
```

<a id="channel-epgmatchanalysisresponse-rows"></a>
### `channel.EPGMatchAnalysisResponse.rows`

[backend/app/schemas/channel.py:251](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L251) · type `List[EPGMatchRowResponse]`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepganalysisrowoutcome-epg_channel_id"></a>
### `channel.TVChannelCreateFromEPGAnalysisRowOutcome.epg_channel_id`

[backend/app/schemas/channel.py:255](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L255) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepganalysisrowoutcome-status"></a>
### `channel.TVChannelCreateFromEPGAnalysisRowOutcome.status`

[backend/app/schemas/channel.py:256](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L256) · type `str`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepganalysisrowoutcome-reason"></a>
### `channel.TVChannelCreateFromEPGAnalysisRowOutcome.reason`

[backend/app/schemas/channel.py:257](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L257) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelcreatefromepganalysisrowoutcome-tv_channel_id"></a>
### `channel.TVChannelCreateFromEPGAnalysisRowOutcome.tv_channel_id`

[backend/app/schemas/channel.py:258](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L258) · type `Optional[int]`

```python
None
```

<a id="channel-tvchannelcreatefromepganalysisrowoutcome-associated_count"></a>
### `channel.TVChannelCreateFromEPGAnalysisRowOutcome.associated_count`

[backend/app/schemas/channel.py:259](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L259) · type `int`

```python
0
```

<a id="channel-tvchannelcreatefromepganalysisrequest-strictness"></a>
### `channel.TVChannelCreateFromEPGAnalysisRequest.strictness`

[backend/app/schemas/channel.py:265](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L265) · type `MatchStrictness`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepganalysisrequest-epg_channel_ids"></a>
### `channel.TVChannelCreateFromEPGAnalysisRequest.epg_channel_ids`

[backend/app/schemas/channel.py:266](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L266) · type `List[int]`

```python
Field(..., min_length=1, max_length=1000)
```

<a id="channel-tvchannelcreatefromepganalysisrequest-source_id"></a>
### `channel.TVChannelCreateFromEPGAnalysisRequest.source_id`

[backend/app/schemas/channel.py:267](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L267) · type `Optional[int]`

```python
None
```

<a id="channel-tvchannelcreatefromepganalysisrequest-expected_previews"></a>
### `channel.TVChannelCreateFromEPGAnalysisRequest.expected_previews`

[backend/app/schemas/channel.py:268](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L268) · type `Optional[Dict[int, str]]`

```python
None
```

<a id="channel-tvchannelcreatefromepganalysisresponse-created_count"></a>
### `channel.TVChannelCreateFromEPGAnalysisResponse.created_count`

[backend/app/schemas/channel.py:272](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L272) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepganalysisresponse-skipped_count"></a>
### `channel.TVChannelCreateFromEPGAnalysisResponse.skipped_count`

[backend/app/schemas/channel.py:273](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L273) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepganalysisresponse-associated_count"></a>
### `channel.TVChannelCreateFromEPGAnalysisResponse.associated_count`

[backend/app/schemas/channel.py:274](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L274) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepganalysisresponse-failure_count"></a>
### `channel.TVChannelCreateFromEPGAnalysisResponse.failure_count`

[backend/app/schemas/channel.py:275](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L275) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelcreatefromepganalysisresponse-row_outcomes"></a>
### `channel.TVChannelCreateFromEPGAnalysisResponse.row_outcomes`

[backend/app/schemas/channel.py:276](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L276) · type `List[TVChannelCreateFromEPGAnalysisRowOutcome]`

```python
required / inherited validation
```

<a id="channel-tvchannelbulkepgupdateitem-tv_channel_id"></a>
### `channel.TVChannelBulkEPGUpdateItem.tv_channel_id`

[backend/app/schemas/channel.py:281](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L281) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelbulkepgupdateitem-epg_id"></a>
### `channel.TVChannelBulkEPGUpdateItem.epg_id`

[backend/app/schemas/channel.py:282](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L282) · type `str`

```python
required / inherited validation
```

<a id="channel-tvchannelbulkepgupdaterequest-updates"></a>
### `channel.TVChannelBulkEPGUpdateRequest.updates`

[backend/app/schemas/channel.py:287](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L287) · type `List[TVChannelBulkEPGUpdateItem]`

```python
required / inherited validation
```

<a id="channel-tvchannelbulkepgupdatedetail-tv_channel_id"></a>
### `channel.TVChannelBulkEPGUpdateDetail.tv_channel_id`

[backend/app/schemas/channel.py:292](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L292) · type `int | str`

```python
required / inherited validation
```

<a id="channel-tvchannelbulkepgupdatedetail-status"></a>
### `channel.TVChannelBulkEPGUpdateDetail.status`

[backend/app/schemas/channel.py:293](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L293) · type `str`

```python
required / inherited validation
```

<a id="channel-tvchannelbulkepgupdatedetail-reason"></a>
### `channel.TVChannelBulkEPGUpdateDetail.reason`

[backend/app/schemas/channel.py:294](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L294) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbulkepgupdatedetail-old_epg_id"></a>
### `channel.TVChannelBulkEPGUpdateDetail.old_epg_id`

[backend/app/schemas/channel.py:295](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L295) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbulkepgupdatedetail-new_epg_id"></a>
### `channel.TVChannelBulkEPGUpdateDetail.new_epg_id`

[backend/app/schemas/channel.py:296](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L296) · type `Optional[str]`

```python
None
```

<a id="channel-tvchannelbulkepgupdateresponse-success_count"></a>
### `channel.TVChannelBulkEPGUpdateResponse.success_count`

[backend/app/schemas/channel.py:301](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L301) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelbulkepgupdateresponse-failure_count"></a>
### `channel.TVChannelBulkEPGUpdateResponse.failure_count`

[backend/app/schemas/channel.py:302](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L302) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelbulkepgupdateresponse-details"></a>
### `channel.TVChannelBulkEPGUpdateResponse.details`

[backend/app/schemas/channel.py:303](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L303) · type `List[TVChannelBulkEPGUpdateDetail]`

```python
required / inherited validation
```

<a id="channel-messageresponse-message"></a>
### `channel.MessageResponse.message`

[backend/app/schemas/channel.py:308](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L308) · type `str`

```python
required / inherited validation
```

<a id="channel-tvchannelreorderrequest-channel_ids"></a>
### `channel.TVChannelReorderRequest.channel_ids`

[backend/app/schemas/channel.py:313](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L313) · type `List[int]`

```python
Field(..., min_length=1)
```

<a id="channel-tvchannelreorderrequest-expected_order"></a>
### `channel.TVChannelReorderRequest.expected_order`

[backend/app/schemas/channel.py:314](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L314) · type `List[int]`

```python
Field(..., min_length=1, description='Original inventory order; rejects stale reorder edits.')
```

<a id="channel-tvchannelstreamreorderrequest-stream_ids"></a>
### `channel.TVChannelStreamReorderRequest.stream_ids`

[backend/app/schemas/channel.py:326](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L326) · type `List[str]`

```python
Field(..., min_length=1, description='Desired complete acestream ID ordering for this TV channel.')
```

<a id="channel-tvchannelstreamreorderrequest-expected_order"></a>
### `channel.TVChannelStreamReorderRequest.expected_order`

[backend/app/schemas/channel.py:327](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L327) · type `List[str]`

```python
Field(..., min_length=1, description='Original complete acestream ID ordering; rejects stale reorder edits.')
```

<a id="channel-guideslot-title"></a>
### `channel.GuideSlot.title`

[backend/app/schemas/channel.py:338](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L338) · type `str`

```python
required / inherited validation
```

<a id="channel-guideslot-start"></a>
### `channel.GuideSlot.start`

[backend/app/schemas/channel.py:339](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L339) · type `datetime`

```python
required / inherited validation
```

<a id="channel-guideslot-end"></a>
### `channel.GuideSlot.end`

[backend/app/schemas/channel.py:340](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L340) · type `datetime`

```python
required / inherited validation
```

<a id="channel-tvchannelnownext-tv_channel_id"></a>
### `channel.TVChannelNowNext.tv_channel_id`

[backend/app/schemas/channel.py:345](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L345) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelnownext-epg_channel_id"></a>
### `channel.TVChannelNowNext.epg_channel_id`

[backend/app/schemas/channel.py:346](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L346) · type `int`

```python
required / inherited validation
```

<a id="channel-tvchannelnownext-now"></a>
### `channel.TVChannelNowNext.now`

[backend/app/schemas/channel.py:347](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L347) · type `Optional[GuideSlot]`

```python
None
```

<a id="channel-tvchannelnownext-next"></a>
### `channel.TVChannelNowNext.next`

[backend/app/schemas/channel.py:348](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L348) · type `Optional[GuideSlot]`

```python
None
```

<a id="channel-playlistguidecoverage-streams"></a>
### `channel.PlaylistGuideCoverage.streams`

[backend/app/schemas/channel.py:352](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L352) · type `int`

```python
required / inherited validation
```

<a id="channel-playlistguidecoverage-linked_streams"></a>
### `channel.PlaylistGuideCoverage.linked_streams`

[backend/app/schemas/channel.py:353](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L353) · type `int`

```python
required / inherited validation
```

<a id="channel-playlistguidecoverage-guide_channels"></a>
### `channel.PlaylistGuideCoverage.guide_channels`

[backend/app/schemas/channel.py:354](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L354) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatusresponse-channel_id"></a>
### `channel_status.ChannelStatusResponse.channel_id`

[backend/app/schemas/channel_status.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L12) · type `str`

```python
required / inherited validation
```

<a id="channel_status-channelstatusresponse-network_status"></a>
### `channel_status.ChannelStatusResponse.network_status`

[backend/app/schemas/channel_status.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L13) · type `Optional[Literal['found', 'not_found', 'unknown']]`

```python
None
```

<a id="channel_status-channelstatusresponse-is_online"></a>
### `channel_status.ChannelStatusResponse.is_online`

[backend/app/schemas/channel_status.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L14) · type `bool`

```python
required / inherited validation
```

<a id="channel_status-channelstatusresponse-status"></a>
### `channel_status.ChannelStatusResponse.status`

[backend/app/schemas/channel_status.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L15) · type `str`

```python
required / inherited validation
```

<a id="channel_status-channelstatusresponse-message"></a>
### `channel_status.ChannelStatusResponse.message`

[backend/app/schemas/channel_status.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L16) · type `str`

```python
required / inherited validation
```

<a id="channel_status-channelstatusresponse-last_checked"></a>
### `channel_status.ChannelStatusResponse.last_checked`

[backend/app/schemas/channel_status.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L17) · type `datetime`

```python
required / inherited validation
```

<a id="channel_status-channelstatusresponse-error"></a>
### `channel_status.ChannelStatusResponse.error`

[backend/app/schemas/channel_status.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L18) · type `Optional[str]`

```python
None
```

<a id="channel_status-channelstatusresponse-stream_stats"></a>
### `channel_status.ChannelStatusResponse.stream_stats`

[backend/app/schemas/channel_status.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L19) · type `Optional[StreamStats]`

```python
None
```

<a id="channel_status-channelstatussummary-total_channels"></a>
### `channel_status.ChannelStatusSummary.total_channels`

[backend/app/schemas/channel_status.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L26) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-active_channels"></a>
### `channel_status.ChannelStatusSummary.active_channels`

[backend/app/schemas/channel_status.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L27) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-online"></a>
### `channel_status.ChannelStatusSummary.online`

[backend/app/schemas/channel_status.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L28) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-online_channels"></a>
### `channel_status.ChannelStatusSummary.online_channels`

[backend/app/schemas/channel_status.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L29) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-offline"></a>
### `channel_status.ChannelStatusSummary.offline`

[backend/app/schemas/channel_status.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L30) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-offline_channels"></a>
### `channel_status.ChannelStatusSummary.offline_channels`

[backend/app/schemas/channel_status.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L31) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-unknown"></a>
### `channel_status.ChannelStatusSummary.unknown`

[backend/app/schemas/channel_status.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L32) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-recent_checks"></a>
### `channel_status.ChannelStatusSummary.recent_checks`

[backend/app/schemas/channel_status.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L33) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-last_checked_channels"></a>
### `channel_status.ChannelStatusSummary.last_checked_channels`

[backend/app/schemas/channel_status.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L34) · type `int`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-online_percentage"></a>
### `channel_status.ChannelStatusSummary.online_percentage`

[backend/app/schemas/channel_status.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L35) · type `float`

```python
required / inherited validation
```

<a id="channel_status-channelstatussummary-checked_percentage"></a>
### `channel_status.ChannelStatusSummary.checked_percentage`

[backend/app/schemas/channel_status.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L36) · type `float`

```python
required / inherited validation
```

<a id="channel_status-channelstatusjobrunresponse-status"></a>
### `channel_status.ChannelStatusJobRunResponse.status`

[backend/app/schemas/channel_status.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L42) · type `Literal['triggered', 'already_running', 'disabled']`

```python
required / inherited validation
```

<a id="channel_status-channelstatusjobrunresponse-message"></a>
### `channel_status.ChannelStatusJobRunResponse.message`

[backend/app/schemas/channel_status.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel_status.py#L43) · type `str`

```python
required / inherited validation
```

<a id="config-streamcheckscope-scope"></a>
### `config.StreamCheckScope.scope`

[backend/app/schemas/config.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L8) · type `Literal['all', 'assigned', 'favorites']`

```python
required / inherited validation
```

<a id="config-playbackrouting-use_acexy"></a>
### `config.PlaybackRouting.use_acexy`

[backend/app/schemas/config.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L12) · type `bool`

```python
Field(False, description='Route web, tuner and remote-player playback through Acexy')
```

<a id="config-playbackrouting-acexy_url"></a>
### `config.PlaybackRouting.acexy_url`

[backend/app/schemas/config.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L13) · type `str`

```python
Field('http://localhost:8080', description='HTTP(S) origin where the backend reaches Acexy in MPEG-TS mode')
```

<a id="config-baseurlupdate-base_url"></a>
### `config.BaseUrlUpdate.base_url`

[backend/app/schemas/config.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L32) · type `Optional[str]`

```python
Field(None, description='Base URL for Acestream links')
```

<a id="config-baseurlupdate-value"></a>
### `config.BaseUrlUpdate.value`

[backend/app/schemas/config.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L33) · type `Optional[str]`

```python
Field(None, description='Compatibility alias for base_url')
```

<a id="config-aceengineurlupdate-value"></a>
### `config.AceEngineUrlUpdate.value`

[backend/app/schemas/config.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L40) · type `str`

```python
Field(..., description='Acestream Engine URL')
```

<a id="config-rescrapeintervalupdate-value"></a>
### `config.RescrapeIntervalUpdate.value`

[backend/app/schemas/config.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L44) · type `Optional[str]`

```python
Field(None, description='Hours between automatic rescrapes')
```

<a id="config-rescrapeintervalupdate-hours"></a>
### `config.RescrapeIntervalUpdate.hours`

[backend/app/schemas/config.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L45) · type `Optional[int]`

```python
Field(None, description='Numeric hours between automatic rescrapes')
```

<a id="config-addpidupdate-value"></a>
### `config.AddPidUpdate.value`

[backend/app/schemas/config.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L56) · type `str`

```python
Field(..., description='Whether to add PID to Acestream links')
```

<a id="config-appidupdate-value"></a>
### `config.AppIdUpdate.value`

[backend/app/schemas/config.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L61) · type `str`

```python
Field(..., description='Whether to add appid to Acestream links')
```

<a id="config-publicbaseurlupdate-value"></a>
### `config.PublicBaseUrlUpdate.value`

[backend/app/schemas/config.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L66) · type `str`

```python
Field('', description='http(s)://host[:port]; empty clears the override')
```

<a id="config-notificationwebhookupdate-value"></a>
### `config.NotificationWebhookUpdate.value`

[backend/app/schemas/config.py:71](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L71) · type `str`

```python
Field('', description='HTTP(S) webhook URL with a valid host and port, without whitespace or fragments; empty turns notifications off')
```

<a id="config-dashboardconfigupdate-retention_days"></a>
### `config.DashboardConfigUpdate.retention_days`

[backend/app/schemas/config.py:76](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L76) · type `Optional[int]`

```python
None
```

<a id="config-dashboardconfigupdate-auto_refresh_interval"></a>
### `config.DashboardConfigUpdate.auto_refresh_interval`

[backend/app/schemas/config.py:77](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L77) · type `Optional[int]`

```python
None
```

<a id="config-dashboardconfigresponse-retention_days"></a>
### `config.DashboardConfigResponse.retention_days`

[backend/app/schemas/config.py:82](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L82) · type `int`

```python
required / inherited validation
```

<a id="config-dashboardconfigresponse-auto_refresh_interval"></a>
### `config.DashboardConfigResponse.auto_refresh_interval`

[backend/app/schemas/config.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L83) · type `int`

```python
required / inherited validation
```

<a id="config-configupdateresponse-message"></a>
### `config.ConfigUpdateResponse.message`

[backend/app/schemas/config.py:88](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L88) · type `str`

```python
required / inherited validation
```

<a id="config-configupdateresponse-value"></a>
### `config.ConfigUpdateResponse.value`

[backend/app/schemas/config.py:89](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L89) · type `str`

```python
required / inherited validation
```

<a id="config-configkeyupdate-value"></a>
### `config.ConfigKeyUpdate.value`

[backend/app/schemas/config.py:94](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L94) · type `Optional[str]`

```python
Field(None, description='Setting value; channel_status_interval uses whole minutes (1–10080, default 60)')
```

<a id="config-configkeyupdate-base_url"></a>
### `config.ConfigKeyUpdate.base_url`

[backend/app/schemas/config.py:95](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L95) · type `Optional[str]`

```python
None
```

<a id="config-configkeyupdate-hours"></a>
### `config.ConfigKeyUpdate.hours`

[backend/app/schemas/config.py:96](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L96) · type `Optional[int]`

```python
None
```

<a id="config-settingresponse-key"></a>
### `config.SettingResponse.key`

[backend/app/schemas/config.py:111](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L111) · type `str`

```python
Field(..., description='Setting key')
```

<a id="config-settingresponse-value"></a>
### `config.SettingResponse.value`

[backend/app/schemas/config.py:112](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L112) · type `str`

```python
Field(..., description='Setting value')
```

<a id="config-settingsresponse-settings"></a>
### `config.SettingsResponse.settings`

[backend/app/schemas/config.py:116](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L116) · type `Dict[str, str]`

```python
Field(..., description='All settings')
```

<a id="config-statusresponse-status"></a>
### `config.StatusResponse.status`

[backend/app/schemas/config.py:120](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L120) · type `str`

```python
Field(..., description='Status of the component (online, offline, error, etc.)')
```

<a id="config-statusresponse-message"></a>
### `config.StatusResponse.message`

[backend/app/schemas/config.py:121](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L121) · type `str`

```python
Field(..., description='Status message')
```

<a id="config-statusresponse-details"></a>
### `config.StatusResponse.details`

[backend/app/schemas/config.py:122](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L122) · type `Optional[str]`

```python
Field(None, description='Additional details')
```

<a id="config-healthresponse-status"></a>
### `config.HealthResponse.status`

[backend/app/schemas/config.py:126](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L126) · type `str`

```python
Field(..., description='Overall system status (healthy, degraded, unhealthy)')
```

<a id="config-healthresponse-acestream"></a>
### `config.HealthResponse.acestream`

[backend/app/schemas/config.py:127](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L127) · type `StatusResponse`

```python
Field(..., description='Acestream Engine status')
```

<a id="config-healthresponse-database"></a>
### `config.HealthResponse.database`

[backend/app/schemas/config.py:128](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L128) · type `Dict[str, Any]`

```python
Field(..., description='Database connection status')
```

<a id="config-healthresponse-settings"></a>
### `config.HealthResponse.settings`

[backend/app/schemas/config.py:129](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L129) · type `Dict[str, Any]`

```python
Field(..., description='Application settings')
```

<a id="config-healthresponse-version"></a>
### `config.HealthResponse.version`

[backend/app/schemas/config.py:130](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L130) · type `str`

```python
Field(..., description='Application version')
```

<a id="config-checkengineconfig-use_dedicated"></a>
### `config.CheckEngineConfig.use_dedicated`

[backend/app/schemas/config.py:134](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L134) · type `bool`

```python
False
```

<a id="config-checkengineconfig-url"></a>
### `config.CheckEngineConfig.url`

[backend/app/schemas/config.py:135](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L135) · type `str`

```python
''
```

<a id="config-checkengineconfigresponse-managed"></a>
### `config.CheckEngineConfigResponse.managed`

[backend/app/schemas/config.py:153](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L153) · type `bool`

```python
False
```

<a id="config-scheduleanchors-timezone"></a>
### `config.ScheduleAnchors.timezone`

[backend/app/schemas/config.py:158](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L158) · type `str`

```python
Field('UTC', description='IANA timezone used to interpret start times')
```

<a id="config-scheduleanchors-url_scraping"></a>
### `config.ScheduleAnchors.url_scraping`

[backend/app/schemas/config.py:159](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L159) · type `Optional[str]`

```python
Field(None, pattern='^([01]\\d|2[0-3]):[0-5]\\d$', description='HH:MM anchor; null retains startup-relative scheduling')
```

<a id="config-scheduleanchors-epg_refresh"></a>
### `config.ScheduleAnchors.epg_refresh`

[backend/app/schemas/config.py:160](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L160) · type `Optional[str]`

```python
Field(None, pattern='^([01]\\d|2[0-3]):[0-5]\\d$')
```

<a id="config-scheduleanchors-channel_status"></a>
### `config.ScheduleAnchors.channel_status`

[backend/app/schemas/config.py:161](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L161) · type `Optional[str]`

```python
Field(None, pattern='^([01]\\d|2[0-3]):[0-5]\\d$')
```

<a id="config-scheduleanchors-offline_stream_cleanup"></a>
### `config.ScheduleAnchors.offline_stream_cleanup`

[backend/app/schemas/config.py:162](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L162) · type `Optional[str]`

```python
Field(None, pattern='^([01]\\d|2[0-3]):[0-5]\\d$')
```

<a id="config-epgmatchingconfig-enabled"></a>
### `config.EPGMatchingConfig.enabled`

[backend/app/schemas/config.py:176](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L176) · type `bool`

```python
Field(False, description='Automatically apply unambiguous exact guide matches after successful scraping or EPG refresh')
```

<a id="config-offlinecleanupconfig-enabled"></a>
### `config.OfflineCleanupConfig.enabled`

[backend/app/schemas/config.py:180](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L180) · type `bool`

```python
False
```

<a id="config-offlinecleanupconfig-offline_days"></a>
### `config.OfflineCleanupConfig.offline_days`

[backend/app/schemas/config.py:181](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L181) · type `int`

```python
Field(14, ge=1, le=365)
```

<a id="config-offlinecleanupconfig-interval_days"></a>
### `config.OfflineCleanupConfig.interval_days`

[backend/app/schemas/config.py:182](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L182) · type `int`

```python
Field(7, ge=1, le=90)
```

<a id="config-offlinecleanupconfig-remove_linked"></a>
### `config.OfflineCleanupConfig.remove_linked`

[backend/app/schemas/config.py:183](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L183) · type `bool`

```python
False
```

<a id="config-offlinecleanupconfig-rescrape"></a>
### `config.OfflineCleanupConfig.rescrape`

[backend/app/schemas/config.py:184](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L184) · type `bool`

```python
True
```

<a id="config-offlinecleanuppreview-eligible_streams"></a>
### `config.OfflineCleanupPreview.eligible_streams`

[backend/app/schemas/config.py:188](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L188) · type `int`

```python
required / inherited validation
```

<a id="config-offlinecleanuppreview-sources"></a>
### `config.OfflineCleanupPreview.sources`

[backend/app/schemas/config.py:189](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L189) · type `int`

```python
required / inherited validation
```

<a id="config-offlinecleanuppreview-limit"></a>
### `config.OfflineCleanupPreview.limit`

[backend/app/schemas/config.py:190](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L190) · type `int`

```python
500
```

<a id="config-epgmatchingrun-status"></a>
### `config.EPGMatchingRun.status`

[backend/app/schemas/config.py:194](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L194) · type `str`

```python
'never'
```

<a id="config-epgmatchingrun-finished_at"></a>
### `config.EPGMatchingRun.finished_at`

[backend/app/schemas/config.py:195](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L195) · type `Optional[datetime]`

```python
None
```

<a id="config-epgmatchingrun-created"></a>
### `config.EPGMatchingRun.created`

[backend/app/schemas/config.py:196](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L196) · type `int`

```python
0
```

<a id="config-epgmatchingrun-assigned"></a>
### `config.EPGMatchingRun.assigned`

[backend/app/schemas/config.py:197](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L197) · type `int`

```python
0
```

<a id="config-epgmatchingrun-review_needed"></a>
### `config.EPGMatchingRun.review_needed`

[backend/app/schemas/config.py:198](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/config.py#L198) · type `int`

```python
0
```

<a id="epg-epgsourcebase-url"></a>
### `epg.EPGSourceBase.url`

[backend/app/schemas/epg.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L11) · type `str`

```python
required / inherited validation
```

<a id="epg-epgsourcebase-name"></a>
### `epg.EPGSourceBase.name`

[backend/app/schemas/epg.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L12) · type `str`

```python
required / inherited validation
```

<a id="epg-epgsourcecreate-enabled"></a>
### `epg.EPGSourceCreate.enabled`

[backend/app/schemas/epg.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L17) · type `bool`

```python
True
```

<a id="epg-epgsourceupdate-url"></a>
### `epg.EPGSourceUpdate.url`

[backend/app/schemas/epg.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L22) · type `Optional[str]`

```python
None
```

<a id="epg-epgsourceupdate-name"></a>
### `epg.EPGSourceUpdate.name`

[backend/app/schemas/epg.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L23) · type `Optional[str]`

```python
None
```

<a id="epg-epgsourceupdate-enabled"></a>
### `epg.EPGSourceUpdate.enabled`

[backend/app/schemas/epg.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L24) · type `Optional[bool]`

```python
None
```

<a id="epg-epgsourceresponse-id"></a>
### `epg.EPGSourceResponse.id`

[backend/app/schemas/epg.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L29) · type `int`

```python
required / inherited validation
```

<a id="epg-epgsourceresponse-enabled"></a>
### `epg.EPGSourceResponse.enabled`

[backend/app/schemas/epg.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L30) · type `bool`

```python
required / inherited validation
```

<a id="epg-epgsourceresponse-last_updated"></a>
### `epg.EPGSourceResponse.last_updated`

[backend/app/schemas/epg.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L31) · type `Optional[datetime]`

```python
None
```

<a id="epg-epgsourceresponse-error_count"></a>
### `epg.EPGSourceResponse.error_count`

[backend/app/schemas/epg.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L32) · type `int`

```python
0
```

<a id="epg-epgsourceresponse-last_error"></a>
### `epg.EPGSourceResponse.last_error`

[backend/app/schemas/epg.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L33) · type `Optional[str]`

```python
None
```

<a id="epg-epgchannelbase-epg_source_id"></a>
### `epg.EPGChannelBase.epg_source_id`

[backend/app/schemas/epg.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L40) · type `int`

```python
required / inherited validation
```

<a id="epg-epgchannelbase-channel_xml_id"></a>
### `epg.EPGChannelBase.channel_xml_id`

[backend/app/schemas/epg.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L41) · type `str`

```python
required / inherited validation
```

<a id="epg-epgchannelbase-name"></a>
### `epg.EPGChannelBase.name`

[backend/app/schemas/epg.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L42) · type `str`

```python
required / inherited validation
```

<a id="epg-epgchannelbase-icon_url"></a>
### `epg.EPGChannelBase.icon_url`

[backend/app/schemas/epg.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L43) · type `Optional[str]`

```python
None
```

<a id="epg-epgchannelbase-language"></a>
### `epg.EPGChannelBase.language`

[backend/app/schemas/epg.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L44) · type `Optional[str]`

```python
None
```

<a id="epg-epgchannelresponse-id"></a>
### `epg.EPGChannelResponse.id`

[backend/app/schemas/epg.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L49) · type `int`

```python
required / inherited validation
```

<a id="epg-epgchannelresponse-created_at"></a>
### `epg.EPGChannelResponse.created_at`

[backend/app/schemas/epg.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L50) · type `datetime`

```python
required / inherited validation
```

<a id="epg-epgchannelresponse-updated_at"></a>
### `epg.EPGChannelResponse.updated_at`

[backend/app/schemas/epg.py:51](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L51) · type `datetime`

```python
required / inherited validation
```

<a id="epg-epgchannellistresponse-items"></a>
### `epg.EPGChannelListResponse.items`

[backend/app/schemas/epg.py:59](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L59) · type `List[EPGChannelResponse]`

```python
required / inherited validation
```

<a id="epg-epgchannellistresponse-total"></a>
### `epg.EPGChannelListResponse.total`

[backend/app/schemas/epg.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L60) · type `int`

```python
required / inherited validation
```

<a id="epg-epgprogrambase-epg_channel_id"></a>
### `epg.EPGProgramBase.epg_channel_id`

[backend/app/schemas/epg.py:65](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L65) · type `int`

```python
required / inherited validation
```

<a id="epg-epgprogrambase-start_time"></a>
### `epg.EPGProgramBase.start_time`

[backend/app/schemas/epg.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L66) · type `datetime`

```python
required / inherited validation
```

<a id="epg-epgprogrambase-end_time"></a>
### `epg.EPGProgramBase.end_time`

[backend/app/schemas/epg.py:67](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L67) · type `datetime`

```python
required / inherited validation
```

<a id="epg-epgprogrambase-title"></a>
### `epg.EPGProgramBase.title`

[backend/app/schemas/epg.py:68](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L68) · type `str`

```python
required / inherited validation
```

<a id="epg-epgprogrambase-subtitle"></a>
### `epg.EPGProgramBase.subtitle`

[backend/app/schemas/epg.py:69](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L69) · type `Optional[str]`

```python
None
```

<a id="epg-epgprogrambase-description"></a>
### `epg.EPGProgramBase.description`

[backend/app/schemas/epg.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L70) · type `Optional[str]`

```python
None
```

<a id="epg-epgprogrambase-category"></a>
### `epg.EPGProgramBase.category`

[backend/app/schemas/epg.py:71](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L71) · type `Optional[str]`

```python
None
```

<a id="epg-epgprogrambase-image_url"></a>
### `epg.EPGProgramBase.image_url`

[backend/app/schemas/epg.py:72](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L72) · type `Optional[str]`

```python
None
```

<a id="epg-epgprogramresponse-id"></a>
### `epg.EPGProgramResponse.id`

[backend/app/schemas/epg.py:77](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L77) · type `int`

```python
required / inherited validation
```

<a id="epg-epgprogramresponse-program_xml_id"></a>
### `epg.EPGProgramResponse.program_xml_id`

[backend/app/schemas/epg.py:78](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L78) · type `Optional[str]`

```python
None
```

<a id="epg-epgstringmappingbase-search_pattern"></a>
### `epg.EPGStringMappingBase.search_pattern`

[backend/app/schemas/epg.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L85) · type `str`

```python
required / inherited validation
```

<a id="epg-epgstringmappingbase-is_exclusion"></a>
### `epg.EPGStringMappingBase.is_exclusion`

[backend/app/schemas/epg.py:86](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L86) · type `bool`

```python
False
```

<a id="epg-epgstringmappingcreate-epg_channel_id"></a>
### `epg.EPGStringMappingCreate.epg_channel_id`

[backend/app/schemas/epg.py:91](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L91) · type `int`

```python
required / inherited validation
```

<a id="epg-epgstringmappingresponse-id"></a>
### `epg.EPGStringMappingResponse.id`

[backend/app/schemas/epg.py:101](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L101) · type `int`

```python
required / inherited validation
```

<a id="epg-epgstringmappingresponse-epg_channel_id"></a>
### `epg.EPGStringMappingResponse.epg_channel_id`

[backend/app/schemas/epg.py:102](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L102) · type `int`

```python
required / inherited validation
```

<a id="epg-epgchannelmappingrequest-epg_channel_id"></a>
### `epg.EPGChannelMappingRequest.epg_channel_id`

[backend/app/schemas/epg.py:109](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L109) · type `int`

```python
required / inherited validation
```

<a id="epg-epgchannelmappingrequest-tv_channel_id"></a>
### `epg.EPGChannelMappingRequest.tv_channel_id`

[backend/app/schemas/epg.py:110](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L110) · type `int`

```python
required / inherited validation
```

<a id="epg-epgrefreshresponse-source_id"></a>
### `epg.EPGRefreshResponse.source_id`

[backend/app/schemas/epg.py:115](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L115) · type `int`

```python
required / inherited validation
```

<a id="epg-epgrefreshresponse-message"></a>
### `epg.EPGRefreshResponse.message`

[backend/app/schemas/epg.py:116](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L116) · type `str`

```python
required / inherited validation
```

<a id="epg-epgrefreshresponse-success"></a>
### `epg.EPGRefreshResponse.success`

[backend/app/schemas/epg.py:117](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L117) · type `bool`

```python
required / inherited validation
```

<a id="epg-epgrefreshresponse-status"></a>
### `epg.EPGRefreshResponse.status`

[backend/app/schemas/epg.py:118](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L118) · type `str`

```python
'success'
```

<a id="epg-epgrefreshresponse-channels_found"></a>
### `epg.EPGRefreshResponse.channels_found`

[backend/app/schemas/epg.py:119](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L119) · type `Optional[int]`

```python
None
```

<a id="epg-epgrefreshresponse-programs_found"></a>
### `epg.EPGRefreshResponse.programs_found`

[backend/app/schemas/epg.py:120](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L120) · type `Optional[int]`

```python
None
```

<a id="epg-epgrefreshresponse-duration_seconds"></a>
### `epg.EPGRefreshResponse.duration_seconds`

[backend/app/schemas/epg.py:121](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L121) · type `Optional[float]`

```python
None
```

<a id="epg-epgrefreshresponse-error"></a>
### `epg.EPGRefreshResponse.error`

[backend/app/schemas/epg.py:122](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L122) · type `Optional[str]`

```python
None
```

<a id="epg-epgxmlgenerationrequest-search_term"></a>
### `epg.EPGXmlGenerationRequest.search_term`

[backend/app/schemas/epg.py:127](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L127) · type `Optional[str]`

```python
None
```

<a id="epg-epgxmlgenerationrequest-favorites_only"></a>
### `epg.EPGXmlGenerationRequest.favorites_only`

[backend/app/schemas/epg.py:128](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L128) · type `bool`

```python
False
```

<a id="epg-epgxmlgenerationrequest-days_back"></a>
### `epg.EPGXmlGenerationRequest.days_back`

[backend/app/schemas/epg.py:129](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L129) · type `int`

```python
1
```

<a id="epg-epgxmlgenerationrequest-days_forward"></a>
### `epg.EPGXmlGenerationRequest.days_forward`

[backend/app/schemas/epg.py:130](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/epg.py#L130) · type `int`

```python
7
```

<a id="errors-errorpayload-code"></a>
### `errors.ErrorPayload.code`

[backend/app/schemas/errors.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/errors.py#L10) · type `str`

```python
required / inherited validation
```

<a id="errors-errorpayload-message"></a>
### `errors.ErrorPayload.message`

[backend/app/schemas/errors.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/errors.py#L11) · type `str`

```python
required / inherited validation
```

<a id="errors-errorpayload-correlation_id"></a>
### `errors.ErrorPayload.correlation_id`

[backend/app/schemas/errors.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/errors.py#L12) · type `str`

```python
required / inherited validation
```

<a id="errors-errorpayload-context"></a>
### `errors.ErrorPayload.context`

[backend/app/schemas/errors.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/errors.py#L13) · type `Optional[Dict[str, Any]]`

```python
None
```

<a id="errors-errorresponse-error"></a>
### `errors.ErrorResponse.error`

[backend/app/schemas/errors.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/errors.py#L19) · type `ErrorPayload`

```python
required / inherited validation
```

<a id="events-eventfields-title"></a>
### `events.EventFields.title`

[backend/app/schemas/events.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L33) · type `str`

```python
Field(min_length=1, max_length=300)
```

<a id="events-eventfields-sport"></a>
### `events.EventFields.sport`

[backend/app/schemas/events.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L34) · type `str`

```python
Field(default='', max_length=100)
```

<a id="events-eventfields-competition"></a>
### `events.EventFields.competition`

[backend/app/schemas/events.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L35) · type `str`

```python
Field(default='', max_length=200)
```

<a id="events-eventfields-participants"></a>
### `events.EventFields.participants`

[backend/app/schemas/events.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L36) · type `list[str]`

```python
Field(default_factory=list, max_length=8)
```

<a id="events-eventfields-starts_at"></a>
### `events.EventFields.starts_at`

[backend/app/schemas/events.py:37](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L37) · type `datetime | None`

```python
None
```

<a id="events-eventfields-scheduled_date"></a>
### `events.EventFields.scheduled_date`

[backend/app/schemas/events.py:38](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L38) · type `date | None`

```python
None
```

<a id="events-eventfields-ends_at"></a>
### `events.EventFields.ends_at`

[backend/app/schemas/events.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L39) · type `datetime | None`

```python
None
```

<a id="events-eventfields-timezone"></a>
### `events.EventFields.timezone`

[backend/app/schemas/events.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L40) · type `str`

```python
Field(max_length=100)
```

<a id="events-eventfields-time_notes"></a>
### `events.EventFields.time_notes`

[backend/app/schemas/events.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L41) · type `str`

```python
Field(default='', max_length=500)
```

<a id="events-eventfields-state"></a>
### `events.EventFields.state`

[backend/app/schemas/events.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L42) · type `EventState`

```python
'unknown'
```

<a id="events-eventbroadcast-id"></a>
### `events.EventBroadcast.id`

[backend/app/schemas/events.py:78](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L78) · type `str`

```python
Field(min_length=1, max_length=160)
```

<a id="events-eventbroadcast-label"></a>
### `events.EventBroadcast.label`

[backend/app/schemas/events.py:79](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L79) · type `str`

```python
Field(min_length=1, max_length=200)
```

<a id="events-eventbroadcast-language"></a>
### `events.EventBroadcast.language`

[backend/app/schemas/events.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L80) · type `str`

```python
Field(default='', max_length=80)
```

<a id="events-eventbroadcast-quality"></a>
### `events.EventBroadcast.quality`

[backend/app/schemas/events.py:81](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L81) · type `str`

```python
Field(default='', max_length=80)
```

<a id="events-eventbroadcast-country"></a>
### `events.EventBroadcast.country`

[backend/app/schemas/events.py:82](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L82) · type `str`

```python
Field(default='', max_length=80)
```

<a id="events-eventbroadcast-channel_id"></a>
### `events.EventBroadcast.channel_id`

[backend/app/schemas/events.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L84) · type `str | None`

```python
Field(default=None, pattern='^(?:url:)?[0-9a-fA-F]{40}$')
```

<a id="events-eventbroadcast-url"></a>
### `events.EventBroadcast.url`

[backend/app/schemas/events.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L85) · type `str | None`

```python
Field(default=None, max_length=4096)
```

<a id="events-eventbroadcast-headers"></a>
### `events.EventBroadcast.headers`

[backend/app/schemas/events.py:86](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L86) · type `dict[str, str]`

```python
Field(default_factory=dict, max_length=3)
```

<a id="events-eventobservation-artwork_url"></a>
### `events.EventObservation.artwork_url`

[backend/app/schemas/events.py:110](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L110) · type `str | None`

```python
Field(default=None, max_length=4096)
```

<a id="events-eventobservation-source_id"></a>
### `events.EventObservation.source_id`

[backend/app/schemas/events.py:121](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L121) · type `str`

```python
Field(min_length=1, max_length=160, pattern='^[\\w.:-]+$')
```

<a id="events-eventobservation-source_name"></a>
### `events.EventObservation.source_name`

[backend/app/schemas/events.py:122](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L122) · type `str`

```python
Field(min_length=1, max_length=200)
```

<a id="events-eventobservation-source_kind"></a>
### `events.EventObservation.source_kind`

[backend/app/schemas/events.py:123](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L123) · type `Literal['guide', 'w3u', 'telegram', 'manual']`

```python
'manual'
```

<a id="events-eventobservation-external_id"></a>
### `events.EventObservation.external_id`

[backend/app/schemas/events.py:124](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L124) · type `str`

```python
Field(min_length=1, max_length=200)
```

<a id="events-eventobservation-event_id"></a>
### `events.EventObservation.event_id`

[backend/app/schemas/events.py:126](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L126) · type `str | None`

```python
Field(default=None, pattern='^[0-9a-f]{32}$')
```

<a id="events-eventobservation-broadcasts"></a>
### `events.EventObservation.broadcasts`

[backend/app/schemas/events.py:127](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L127) · type `list[EventBroadcast]`

```python
Field(default_factory=list, max_length=50)
```

<a id="events-eventimport-version"></a>
### `events.EventImport.version`

[backend/app/schemas/events.py:137](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L137) · type `Literal[1]`

```python
1
```

<a id="events-eventimport-observations"></a>
### `events.EventImport.observations`

[backend/app/schemas/events.py:138](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L138) · type `list[EventObservation]`

```python
Field(min_length=1, max_length=500)
```

<a id="events-broadcastview-target"></a>
### `events.BroadcastView.target`

[backend/app/schemas/events.py:148](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L148) · type `'EventChannelTarget | None'`

```python
None
```

<a id="events-broadcastview-manually_mapped"></a>
### `events.BroadcastView.manually_mapped`

[backend/app/schemas/events.py:149](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L149) · type `bool`

```python
False
```

<a id="events-broadcastview-via_alias"></a>
### `events.BroadcastView.via_alias`

[backend/app/schemas/events.py:151](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L151) · type `bool`

```python
False
```

<a id="events-broadcastview-source_kept"></a>
### `events.BroadcastView.source_kept`

[backend/app/schemas/events.py:153](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L153) · type `bool`

```python
False
```

<a id="events-broadcastview-id"></a>
### `events.BroadcastView.id`

[backend/app/schemas/events.py:154](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L154) · type `str`

```python
required / inherited validation
```

<a id="events-broadcastview-label"></a>
### `events.BroadcastView.label`

[backend/app/schemas/events.py:155](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L155) · type `str`

```python
required / inherited validation
```

<a id="events-broadcastview-language"></a>
### `events.BroadcastView.language`

[backend/app/schemas/events.py:156](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L156) · type `str`

```python
required / inherited validation
```

<a id="events-broadcastview-quality"></a>
### `events.BroadcastView.quality`

[backend/app/schemas/events.py:157](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L157) · type `str`

```python
required / inherited validation
```

<a id="events-broadcastview-country"></a>
### `events.BroadcastView.country`

[backend/app/schemas/events.py:158](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L158) · type `str`

```python
required / inherited validation
```

<a id="events-broadcastview-source_name"></a>
### `events.BroadcastView.source_name`

[backend/app/schemas/events.py:159](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L159) · type `str`

```python
required / inherited validation
```

<a id="events-broadcastview-origin"></a>
### `events.BroadcastView.origin`

[backend/app/schemas/events.py:160](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L160) · type `str`

```python
required / inherited validation
```

<a id="events-broadcastview-content_id"></a>
### `events.BroadcastView.content_id`

[backend/app/schemas/events.py:161](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L161) · type `str | None`

```python
required / inherited validation
```

<a id="events-broadcastview-compatibility"></a>
### `events.BroadcastView.compatibility`

[backend/app/schemas/events.py:162](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L162) · type `Literal['playable', 'linked', 'unresolved', 'unsupported', 'unavailable']`

```python
required / inherited validation
```

<a id="events-broadcastview-reason"></a>
### `events.BroadcastView.reason`

[backend/app/schemas/events.py:163](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L163) · type `str`

```python
required / inherited validation
```

<a id="events-broadcastview-is_online"></a>
### `events.BroadcastView.is_online`

[backend/app/schemas/events.py:164](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L164) · type `bool | None`

```python
None
```

<a id="events-broadcastview-checked_at"></a>
### `events.BroadcastView.checked_at`

[backend/app/schemas/events.py:165](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L165) · type `datetime | None`

```python
None
```

<a id="events-provenanceview-source_id"></a>
### `events.ProvenanceView.source_id`

[backend/app/schemas/events.py:169](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L169) · type `str`

```python
required / inherited validation
```

<a id="events-provenanceview-source_name"></a>
### `events.ProvenanceView.source_name`

[backend/app/schemas/events.py:170](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L170) · type `str`

```python
required / inherited validation
```

<a id="events-provenanceview-source_kind"></a>
### `events.ProvenanceView.source_kind`

[backend/app/schemas/events.py:171](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L171) · type `str`

```python
required / inherited validation
```

<a id="events-provenanceview-external_id"></a>
### `events.ProvenanceView.external_id`

[backend/app/schemas/events.py:172](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L172) · type `str`

```python
required / inherited validation
```

<a id="events-provenanceview-updated_at"></a>
### `events.ProvenanceView.updated_at`

[backend/app/schemas/events.py:173](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L173) · type `datetime`

```python
required / inherited validation
```

<a id="events-eventprogrammatch-program_id"></a>
### `events.EventProgramMatch.program_id`

[backend/app/schemas/events.py:177](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L177) · type `int`

```python
required / inherited validation
```

<a id="events-eventprogrammatch-title"></a>
### `events.EventProgramMatch.title`

[backend/app/schemas/events.py:178](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L178) · type `str`

```python
required / inherited validation
```

<a id="events-eventprogrammatch-starts_at"></a>
### `events.EventProgramMatch.starts_at`

[backend/app/schemas/events.py:179](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L179) · type `datetime`

```python
required / inherited validation
```

<a id="events-eventprogrammatch-ends_at"></a>
### `events.EventProgramMatch.ends_at`

[backend/app/schemas/events.py:180](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L180) · type `datetime`

```python
required / inherited validation
```

<a id="events-eventprogrammatch-epg_channel"></a>
### `events.EventProgramMatch.epg_channel`

[backend/app/schemas/events.py:181](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L181) · type `'EventChannelTarget'`

```python
required / inherited validation
```

<a id="events-eventprogrammatch-tv_channel"></a>
### `events.EventProgramMatch.tv_channel`

[backend/app/schemas/events.py:182](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L182) · type `'EventChannelTarget | None'`

```python
None
```

<a id="events-eventview-epg_matches"></a>
### `events.EventView.epg_matches`

[backend/app/schemas/events.py:186](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L186) · type `list[EventProgramMatch]`

```python
Field(default_factory=list)
```

<a id="events-eventview-has_artwork"></a>
### `events.EventView.has_artwork`

[backend/app/schemas/events.py:187](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L187) · type `bool`

```python
False
```

<a id="events-eventview-id"></a>
### `events.EventView.id`

[backend/app/schemas/events.py:188](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L188) · type `str`

```python
required / inherited validation
```

<a id="events-eventview-revision"></a>
### `events.EventView.revision`

[backend/app/schemas/events.py:189](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L189) · type `int`

```python
required / inherited validation
```

<a id="events-eventview-corrected"></a>
### `events.EventView.corrected`

[backend/app/schemas/events.py:190](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L190) · type `bool`

```python
required / inherited validation
```

<a id="events-eventview-followed"></a>
### `events.EventView.followed`

[backend/app/schemas/events.py:191](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L191) · type `bool`

```python
required / inherited validation
```

<a id="events-eventview-archived"></a>
### `events.EventView.archived`

[backend/app/schemas/events.py:192](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L192) · type `bool`

```python
required / inherited validation
```

<a id="events-eventview-broadcasts"></a>
### `events.EventView.broadcasts`

[backend/app/schemas/events.py:193](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L193) · type `list[BroadcastView]`

```python
required / inherited validation
```

<a id="events-eventview-provenance"></a>
### `events.EventView.provenance`

[backend/app/schemas/events.py:194](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L194) · type `list[ProvenanceView]`

```python
required / inherited validation
```

<a id="events-eventlist-events"></a>
### `events.EventList.events`

[backend/app/schemas/events.py:198](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L198) · type `list[EventView]`

```python
required / inherited validation
```

<a id="events-eventlist-total"></a>
### `events.EventList.total`

[backend/app/schemas/events.py:199](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L199) · type `int`

```python
required / inherited validation
```

<a id="events-eventinterests-sports"></a>
### `events.EventInterests.sports`

[backend/app/schemas/events.py:203](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L203) · type `list[str]`

```python
Field(default_factory=list, max_length=100)
```

<a id="events-eventinterests-competitions"></a>
### `events.EventInterests.competitions`

[backend/app/schemas/events.py:204](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L204) · type `list[str]`

```python
Field(default_factory=list, max_length=100)
```

<a id="events-eventinterests-teams"></a>
### `events.EventInterests.teams`

[backend/app/schemas/events.py:205](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L205) · type `list[str]`

```python
Field(default_factory=list, max_length=100)
```

<a id="events-eventinterestchoices-sports"></a>
### `events.EventInterestChoices.sports`

[backend/app/schemas/events.py:216](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L216) · type `list[str]`

```python
Field(default_factory=list, max_length=2000)
```

<a id="events-eventinterestchoices-competitions"></a>
### `events.EventInterestChoices.competitions`

[backend/app/schemas/events.py:217](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L217) · type `list[str]`

```python
Field(default_factory=list, max_length=2000)
```

<a id="events-eventinterestchoices-teams"></a>
### `events.EventInterestChoices.teams`

[backend/app/schemas/events.py:218](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L218) · type `list[str]`

```python
Field(default_factory=list, max_length=2000)
```

<a id="events-eventprovideroptions-provider"></a>
### `events.EventProviderOptions.provider`

[backend/app/schemas/events.py:228](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L228) · type `Literal['wosti_es', 'openfootball']`

```python
required / inherited validation
```

<a id="events-eventprovideroptions-feeds"></a>
### `events.EventProviderOptions.feeds`

[backend/app/schemas/events.py:229](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L229) · type `list[str]`

```python
Field(default_factory=lambda: ['all', 'automovilismo'], min_length=1, max_length=20)
```

<a id="events-eventprovideroptions-football_competitions"></a>
### `events.EventProviderOptions.football_competitions`

[backend/app/schemas/events.py:230](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L230) · type `list[str]`

```python
Field(default_factory=list, max_length=20)
```

<a id="events-eventprovideroptions-season"></a>
### `events.EventProviderOptions.season`

[backend/app/schemas/events.py:231](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L231) · type `str`

```python
Field(default_factory=current_football_season, pattern='^20\\d{2}-\\d{2}$')
```

<a id="events-eventprovideroptions-league"></a>
### `events.EventProviderOptions.league`

[backend/app/schemas/events.py:232](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L232) · type `Literal['en.1', 'en.2', 'es.1', 'de.1', 'fr.1', 'it.1', 'nl.1', 'pt.1']`

```python
'es.1'
```

<a id="events-eventprovideroptions-window_days"></a>
### `events.EventProviderOptions.window_days`

[backend/app/schemas/events.py:233](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L233) · type `int`

```python
Field(default=14, ge=1, le=30)
```

<a id="events-eventprovideroptions-interests"></a>
### `events.EventProviderOptions.interests`

[backend/app/schemas/events.py:234](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L234) · type `EventInterests`

```python
Field(default_factory=EventInterests)
```

<a id="events-eventproviderchoice-id"></a>
### `events.EventProviderChoice.id`

[backend/app/schemas/events.py:238](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L238) · type `str`

```python
required / inherited validation
```

<a id="events-eventproviderchoice-name"></a>
### `events.EventProviderChoice.name`

[backend/app/schemas/events.py:239](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L239) · type `str`

```python
required / inherited validation
```

<a id="events-eventproviderchoice-timezone"></a>
### `events.EventProviderChoice.timezone`

[backend/app/schemas/events.py:240](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L240) · type `str`

```python
'Europe/Madrid'
```

<a id="events-eventprovidercatalog-football_competitions"></a>
### `events.EventProviderCatalog.football_competitions`

[backend/app/schemas/events.py:244](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L244) · type `list[EventProviderChoice]`

```python
Field(default_factory=list)
```

<a id="events-eventprovidercatalog-feeds"></a>
### `events.EventProviderCatalog.feeds`

[backend/app/schemas/events.py:245](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L245) · type `list[EventProviderChoice]`

```python
required / inherited validation
```

<a id="events-eventprovidercatalog-leagues"></a>
### `events.EventProviderCatalog.leagues`

[backend/app/schemas/events.py:246](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L246) · type `list[EventProviderChoice]`

```python
required / inherited validation
```

<a id="events-eventchanneltarget-kind"></a>
### `events.EventChannelTarget.kind`

[backend/app/schemas/events.py:250](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L250) · type `Literal['tv', 'epg']`

```python
required / inherited validation
```

<a id="events-eventchanneltarget-id"></a>
### `events.EventChannelTarget.id`

[backend/app/schemas/events.py:251](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L251) · type `int`

```python
Field(ge=1)
```

<a id="events-eventchanneltarget-name"></a>
### `events.EventChannelTarget.name`

[backend/app/schemas/events.py:252](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L252) · type `str`

```python
required / inherited validation
```

<a id="events-eventchanneltarget-country"></a>
### `events.EventChannelTarget.country`

[backend/app/schemas/events.py:253](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L253) · type `str`

```python
''
```

<a id="events-eventchanneltarget-source_name"></a>
### `events.EventChannelTarget.source_name`

[backend/app/schemas/events.py:254](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L254) · type `str`

```python
''
```

<a id="events-eventpreview-available_interests"></a>
### `events.EventPreview.available_interests`

[backend/app/schemas/events.py:258](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L258) · type `EventInterestChoices`

```python
Field(default_factory=EventInterestChoices)
```

<a id="events-eventpreview-token"></a>
### `events.EventPreview.token`

[backend/app/schemas/events.py:259](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L259) · type `str`

```python
required / inherited validation
```

<a id="events-eventpreview-events"></a>
### `events.EventPreview.events`

[backend/app/schemas/events.py:260](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L260) · type `list[EventView]`

```python
required / inherited validation
```

<a id="events-eventpreview-warnings"></a>
### `events.EventPreview.warnings`

[backend/app/schemas/events.py:261](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L261) · type `list[str]`

```python
required / inherited validation
```

<a id="events-eventapply-token"></a>
### `events.EventApply.token`

[backend/app/schemas/events.py:265](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L265) · type `str`

```python
Field(min_length=1, max_length=128)
```

<a id="events-eventapply-selected_ids"></a>
### `events.EventApply.selected_ids`

[backend/app/schemas/events.py:266](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L266) · type `list[str]`

```python
Field(max_length=500)
```

<a id="events-eventapply-refresh_source"></a>
### `events.EventApply.refresh_source`

[backend/app/schemas/events.py:267](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L267) · type `bool`

```python
False
```

<a id="events-eventupdate-revision"></a>
### `events.EventUpdate.revision`

[backend/app/schemas/events.py:271](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L271) · type `int`

```python
Field(ge=1)
```

<a id="events-eventupdate-correction"></a>
### `events.EventUpdate.correction`

[backend/app/schemas/events.py:272](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L272) · type `EventFields | None`

```python
None
```

<a id="events-eventupdate-followed"></a>
### `events.EventUpdate.followed`

[backend/app/schemas/events.py:273](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L273) · type `bool | None`

```python
None
```

<a id="events-eventupdate-archived"></a>
### `events.EventUpdate.archived`

[backend/app/schemas/events.py:274](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L274) · type `bool | None`

```python
None
```

<a id="events-eventsourcepreviewrequest-timeout_seconds"></a>
### `events.EventSourcePreviewRequest.timeout_seconds`

[backend/app/schemas/events.py:278](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L278) · type `int | None`

```python
Field(default=None, ge=5, le=300)
```

<a id="events-eventsourcepreviewrequest-provider_options"></a>
### `events.EventSourcePreviewRequest.provider_options`

[backend/app/schemas/events.py:279](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L279) · type `EventProviderOptions | None`

```python
None
```

<a id="events-eventsourcepreviewrequest-format"></a>
### `events.EventSourcePreviewRequest.format`

[backend/app/schemas/events.py:280](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L280) · type `Literal['event_import', 'schema_org']`

```python
'event_import'
```

<a id="events-eventsourcepreviewrequest-timezone"></a>
### `events.EventSourcePreviewRequest.timezone`

[backend/app/schemas/events.py:281](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L281) · type `str`

```python
Field(default='UTC', max_length=100)
```

<a id="events-eventsourcepreviewrequest-url"></a>
### `events.EventSourcePreviewRequest.url`

[backend/app/schemas/events.py:288](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L288) · type `str | None`

```python
Field(default=None, max_length=4096)
```

<a id="events-eventsourcepreviewrequest-source_id"></a>
### `events.EventSourcePreviewRequest.source_id`

[backend/app/schemas/events.py:289](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L289) · type `str | None`

```python
Field(default=None, pattern='^[0-9a-f]{32}$')
```

<a id="events-eventsourceupdate-revision"></a>
### `events.EventSourceUpdate.revision`

[backend/app/schemas/events.py:303](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L303) · type `int`

```python
Field(ge=1)
```

<a id="events-eventsourceupdate-enabled"></a>
### `events.EventSourceUpdate.enabled`

[backend/app/schemas/events.py:304](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L304) · type `bool`

```python
required / inherited validation
```

<a id="events-eventrefreshresult-updated"></a>
### `events.EventRefreshResult.updated`

[backend/app/schemas/events.py:308](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L308) · type `int`

```python
0
```

<a id="events-eventrefreshresult-pending"></a>
### `events.EventRefreshResult.pending`

[backend/app/schemas/events.py:309](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L309) · type `int`

```python
0
```

<a id="events-eventrefreshresult-status"></a>
### `events.EventRefreshResult.status`

[backend/app/schemas/events.py:310](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L310) · type `Literal['updated', 'error', 'unchanged']`

```python
required / inherited validation
```

<a id="events-eventrefreshresult-message"></a>
### `events.EventRefreshResult.message`

[backend/app/schemas/events.py:311](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L311) · type `str`

```python
required / inherited validation
```

<a id="events-eventsourceview-timeout_seconds"></a>
### `events.EventSourceView.timeout_seconds`

[backend/app/schemas/events.py:315](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L315) · type `int`

```python
Field(default=15, ge=5, le=300)
```

<a id="events-eventsourceview-provider_options"></a>
### `events.EventSourceView.provider_options`

[backend/app/schemas/events.py:316](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L316) · type `EventProviderOptions | None`

```python
None
```

<a id="events-eventsourceview-format"></a>
### `events.EventSourceView.format`

[backend/app/schemas/events.py:317](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L317) · type `Literal['event_import', 'schema_org']`

```python
'event_import'
```

<a id="events-eventsourceview-timezone"></a>
### `events.EventSourceView.timezone`

[backend/app/schemas/events.py:318](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L318) · type `str`

```python
'UTC'
```

<a id="events-eventsourceview-id"></a>
### `events.EventSourceView.id`

[backend/app/schemas/events.py:319](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L319) · type `str`

```python
required / inherited validation
```

<a id="events-eventsourceview-revision"></a>
### `events.EventSourceView.revision`

[backend/app/schemas/events.py:320](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L320) · type `int`

```python
required / inherited validation
```

<a id="events-eventsourceview-name"></a>
### `events.EventSourceView.name`

[backend/app/schemas/events.py:321](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L321) · type `str`

```python
required / inherited validation
```

<a id="events-eventsourceview-origin"></a>
### `events.EventSourceView.origin`

[backend/app/schemas/events.py:322](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L322) · type `str`

```python
required / inherited validation
```

<a id="events-eventsourceview-enabled"></a>
### `events.EventSourceView.enabled`

[backend/app/schemas/events.py:323](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L323) · type `bool`

```python
required / inherited validation
```

<a id="events-eventsourceview-reviewed"></a>
### `events.EventSourceView.reviewed`

[backend/app/schemas/events.py:324](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L324) · type `int`

```python
required / inherited validation
```

<a id="events-eventsourceview-last_attempt"></a>
### `events.EventSourceView.last_attempt`

[backend/app/schemas/events.py:325](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L325) · type `datetime | None`

```python
required / inherited validation
```

<a id="events-eventsourceview-last_success"></a>
### `events.EventSourceView.last_success`

[backend/app/schemas/events.py:326](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L326) · type `datetime | None`

```python
required / inherited validation
```

<a id="events-eventsourceview-last_result"></a>
### `events.EventSourceView.last_result`

[backend/app/schemas/events.py:327](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L327) · type `EventRefreshResult | None`

```python
required / inherited validation
```

<a id="events-eventretention-ended_days"></a>
### `events.EventRetention.ended_days`

[backend/app/schemas/events.py:331](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L331) · type `int`

```python
Field(default=0, ge=0, le=3650)
```

<a id="events-eventretention-archived_days"></a>
### `events.EventRetention.archived_days`

[backend/app/schemas/events.py:332](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L332) · type `int`

```python
Field(default=0, ge=0, le=3650)
```

<a id="events-broadcasterlinkview-id"></a>
### `events.BroadcasterLinkView.id`

[backend/app/schemas/events.py:336](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L336) · type `str`

```python
required / inherited validation
```

<a id="events-broadcasterlinkview-source_id"></a>
### `events.BroadcasterLinkView.source_id`

[backend/app/schemas/events.py:337](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L337) · type `str`

```python
required / inherited validation
```

<a id="events-broadcasterlinkview-source_name"></a>
### `events.BroadcasterLinkView.source_name`

[backend/app/schemas/events.py:338](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L338) · type `str`

```python
required / inherited validation
```

<a id="events-broadcasterlinkview-label"></a>
### `events.BroadcasterLinkView.label`

[backend/app/schemas/events.py:339](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L339) · type `str`

```python
required / inherited validation
```

<a id="events-broadcasterlinkview-target"></a>
### `events.BroadcasterLinkView.target`

[backend/app/schemas/events.py:340](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L340) · type `'EventChannelTarget | None'`

```python
None
```

<a id="events-broadcasterlinkview-content_id"></a>
### `events.BroadcasterLinkView.content_id`

[backend/app/schemas/events.py:341](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L341) · type `str | None`

```python
None
```

<a id="events-broadcasterlinkview-event_count"></a>
### `events.BroadcasterLinkView.event_count`

[backend/app/schemas/events.py:342](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L342) · type `int`

```python
required / inherited validation
```

<a id="events-eventbroadcastmapping-revision"></a>
### `events.EventBroadcastMapping.revision`

[backend/app/schemas/events.py:346](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L346) · type `int`

```python
Field(ge=1)
```

<a id="events-eventbroadcastmapping-broadcast_id"></a>
### `events.EventBroadcastMapping.broadcast_id`

[backend/app/schemas/events.py:347](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L347) · type `str`

```python
Field(min_length=1, max_length=193)
```

<a id="events-eventbroadcastmapping-channel_id"></a>
### `events.EventBroadcastMapping.channel_id`

[backend/app/schemas/events.py:348](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L348) · type `str | None`

```python
Field(default=None, pattern='^(?:url:)?[0-9a-fA-F]{40}$')
```

<a id="events-eventbroadcastmapping-target_kind"></a>
### `events.EventBroadcastMapping.target_kind`

[backend/app/schemas/events.py:349](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L349) · type `Literal['tv', 'epg'] | None`

```python
None
```

<a id="events-eventbroadcastmapping-target_id"></a>
### `events.EventBroadcastMapping.target_id`

[backend/app/schemas/events.py:350](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L350) · type `int | None`

```python
Field(default=None, ge=1)
```

<a id="events-eventbroadcastmapping-apply_to_source"></a>
### `events.EventBroadcastMapping.apply_to_source`

[backend/app/schemas/events.py:352](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L352) · type `bool`

```python
True
```

<a id="events-eventrefreshqueued-status"></a>
### `events.EventRefreshQueued.status`

[backend/app/schemas/events.py:362](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L362) · type `Literal['triggered', 'already_running']`

```python
required / inherited validation
```

<a id="events-eventrefreshqueued-message"></a>
### `events.EventRefreshQueued.message`

[backend/app/schemas/events.py:363](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L363) · type `str`

```python
required / inherited validation
```

<a id="events-eventoverlayrequest-revision"></a>
### `events.EventOverlayRequest.revision`

[backend/app/schemas/events.py:367](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L367) · type `int`

```python
Field(ge=1)
```

<a id="events-eventoverlayrequest-broadcast_id"></a>
### `events.EventOverlayRequest.broadcast_id`

[backend/app/schemas/events.py:368](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L368) · type `str`

```python
Field(min_length=1, max_length=193)
```

<a id="events-eventoverlayrequest-ends_at"></a>
### `events.EventOverlayRequest.ends_at`

[backend/app/schemas/events.py:369](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L369) · type `datetime`

```python
required / inherited validation
```

<a id="events-eventoverlayprogram-title"></a>
### `events.EventOverlayProgram.title`

[backend/app/schemas/events.py:380](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L380) · type `str`

```python
required / inherited validation
```

<a id="events-eventoverlayprogram-starts_at"></a>
### `events.EventOverlayProgram.starts_at`

[backend/app/schemas/events.py:381](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L381) · type `datetime`

```python
required / inherited validation
```

<a id="events-eventoverlayprogram-ends_at"></a>
### `events.EventOverlayProgram.ends_at`

[backend/app/schemas/events.py:382](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L382) · type `datetime`

```python
required / inherited validation
```

<a id="events-eventoverlaypreview-fingerprint"></a>
### `events.EventOverlayPreview.fingerprint`

[backend/app/schemas/events.py:386](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L386) · type `str`

```python
required / inherited validation
```

<a id="events-eventoverlaypreview-channel"></a>
### `events.EventOverlayPreview.channel`

[backend/app/schemas/events.py:387](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L387) · type `EventChannelTarget`

```python
required / inherited validation
```

<a id="events-eventoverlaypreview-programme"></a>
### `events.EventOverlayPreview.programme`

[backend/app/schemas/events.py:388](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L388) · type `EventOverlayProgram`

```python
required / inherited validation
```

<a id="events-eventoverlaypreview-affected"></a>
### `events.EventOverlayPreview.affected`

[backend/app/schemas/events.py:389](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L389) · type `list[EventOverlayProgram]`

```python
required / inherited validation
```

<a id="events-eventoverlayapply-expected_fingerprint"></a>
### `events.EventOverlayApply.expected_fingerprint`

[backend/app/schemas/events.py:393](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L393) · type `str`

```python
Field(pattern='^[0-9a-f]{64}$')
```

<a id="events-eventoverlayview-broadcast_id"></a>
### `events.EventOverlayView.broadcast_id`

[backend/app/schemas/events.py:397](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L397) · type `str`

```python
required / inherited validation
```

<a id="events-eventoverlayview-channel"></a>
### `events.EventOverlayView.channel`

[backend/app/schemas/events.py:398](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L398) · type `EventChannelTarget`

```python
required / inherited validation
```

<a id="events-eventoverlayview-programme"></a>
### `events.EventOverlayView.programme`

[backend/app/schemas/events.py:399](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L399) · type `EventOverlayProgram`

```python
required / inherited validation
```

<a id="events-eventoverlayview-active"></a>
### `events.EventOverlayView.active`

[backend/app/schemas/events.py:400](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/events.py#L400) · type `bool`

```python
required / inherited validation
```

<a id="extraction-recipefield-selector"></a>
### `extraction.RecipeField.selector`

[backend/app/schemas/extraction.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L12) · type `str`

```python
Field('', max_length=256)
```

<a id="extraction-recipefield-attribute"></a>
### `extraction.RecipeField.attribute`

[backend/app/schemas/extraction.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L13) · type `str`

```python
Field('', max_length=80)
```

<a id="extraction-recipefield-path"></a>
### `extraction.RecipeField.path`

[backend/app/schemas/extraction.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L14) · type `str`

```python
Field('', max_length=256)
```

<a id="extraction-recipefield-pattern"></a>
### `extraction.RecipeField.pattern`

[backend/app/schemas/extraction.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L15) · type `str`

```python
Field('', max_length=1024)
```

<a id="extraction-extractionrecipe-schema_version"></a>
### `extraction.ExtractionRecipe.schema_version`

[backend/app/schemas/extraction.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L20) · type `Literal[1]`

```python
1
```

<a id="extraction-extractionrecipe-name"></a>
### `extraction.ExtractionRecipe.name`

[backend/app/schemas/extraction.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L21) · type `str`

```python
Field('My recipe', min_length=1, max_length=100)
```

<a id="extraction-extractionrecipe-version"></a>
### `extraction.ExtractionRecipe.version`

[backend/app/schemas/extraction.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L22) · type `str`

```python
Field('1.0.0', pattern='^\\d+\\.\\d+\\.\\d+$')
```

<a id="extraction-extractionrecipe-mode"></a>
### `extraction.ExtractionRecipe.mode`

[backend/app/schemas/extraction.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L23) · type `Literal['html', 'regex', 'json']`

```python
'html'
```

<a id="extraction-extractionrecipe-records"></a>
### `extraction.ExtractionRecipe.records`

[backend/app/schemas/extraction.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L24) · type `str`

```python
Field('', max_length=1024)
```

<a id="extraction-extractionrecipe-flags"></a>
### `extraction.ExtractionRecipe.flags`

[backend/app/schemas/extraction.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L25) · type `str`

```python
Field('is', pattern='^[ims]{0,3}$')
```

<a id="extraction-extractionrecipe-fields"></a>
### `extraction.ExtractionRecipe.fields`

[backend/app/schemas/extraction.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L26) · type `dict[str, RecipeField]`

```python
required / inherited validation
```

<a id="extraction-recipepreviewrequest-recipe"></a>
### `extraction.RecipePreviewRequest.recipe`

[backend/app/schemas/extraction.py:55](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L55) · type `ExtractionRecipe`

```python
required / inherited validation
```

<a id="extraction-recipepreviewrequest-sample"></a>
### `extraction.RecipePreviewRequest.sample`

[backend/app/schemas/extraction.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L56) · type `str`

```python
Field(max_length=MAX_SAMPLE_BYTES)
```

<a id="extraction-recipefetchrequest-url"></a>
### `extraction.RecipeFetchRequest.url`

[backend/app/schemas/extraction.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L60) · type `str`

```python
Field(min_length=1, max_length=2048)
```

<a id="extraction-recipefetchrequest-url_type"></a>
### `extraction.RecipeFetchRequest.url_type`

[backend/app/schemas/extraction.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L61) · type `Literal['auto', 'regular', 'zeronet', 'ipfs']`

```python
'auto'
```

<a id="extraction-recipesample-sample"></a>
### `extraction.RecipeSample.sample`

[backend/app/schemas/extraction.py:65](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L65) · type `str`

```python
required / inherited validation
```

<a id="extraction-extractedchannel-channel_id"></a>
### `extraction.ExtractedChannel.channel_id`

[backend/app/schemas/extraction.py:69](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L69) · type `str`

```python
required / inherited validation
```

<a id="extraction-extractedchannel-name"></a>
### `extraction.ExtractedChannel.name`

[backend/app/schemas/extraction.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L70) · type `str`

```python
required / inherited validation
```

<a id="extraction-extractedchannel-metadata"></a>
### `extraction.ExtractedChannel.metadata`

[backend/app/schemas/extraction.py:71](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L71) · type `dict[str, str]`

```python
Field(default_factory=dict)
```

<a id="extraction-recipeissue-record"></a>
### `extraction.RecipeIssue.record`

[backend/app/schemas/extraction.py:75](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L75) · type `int`

```python
required / inherited validation
```

<a id="extraction-recipeissue-message"></a>
### `extraction.RecipeIssue.message`

[backend/app/schemas/extraction.py:76](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L76) · type `str`

```python
required / inherited validation
```

<a id="extraction-recipepreview-channels"></a>
### `extraction.RecipePreview.channels`

[backend/app/schemas/extraction.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L80) · type `list[ExtractedChannel]`

```python
required / inherited validation
```

<a id="extraction-recipepreview-record_count"></a>
### `extraction.RecipePreview.record_count`

[backend/app/schemas/extraction.py:81](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L81) · type `int`

```python
required / inherited validation
```

<a id="extraction-recipepreview-invalid_count"></a>
### `extraction.RecipePreview.invalid_count`

[backend/app/schemas/extraction.py:82](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L82) · type `int`

```python
required / inherited validation
```

<a id="extraction-recipepreview-duplicate_count"></a>
### `extraction.RecipePreview.duplicate_count`

[backend/app/schemas/extraction.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L83) · type `int`

```python
required / inherited validation
```

<a id="extraction-recipepreview-issues"></a>
### `extraction.RecipePreview.issues`

[backend/app/schemas/extraction.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/extraction.py#L84) · type `list[RecipeIssue]`

```python
required / inherited validation
```

<a id="import_exclusions-exclusioninput-kind"></a>
### `import_exclusions.ExclusionInput.kind`

[backend/app/schemas/import_exclusions.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L30) · type `RuleKind`

```python
required / inherited validation
```

<a id="import_exclusions-exclusioninput-value"></a>
### `import_exclusions.ExclusionInput.value`

[backend/app/schemas/import_exclusions.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L31) · type `str`

```python
Field(min_length=1, max_length=256)
```

<a id="import_exclusions-exclusioninput-enabled"></a>
### `import_exclusions.ExclusionInput.enabled`

[backend/app/schemas/import_exclusions.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L32) · type `bool`

```python
True
```

<a id="import_exclusions-exclusioninput-note"></a>
### `import_exclusions.ExclusionInput.note`

[backend/app/schemas/import_exclusions.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L33) · type `str | None`

```python
Field(default=None, max_length=500)
```

<a id="import_exclusions-exclusionupdate-expected_revision"></a>
### `import_exclusions.ExclusionUpdate.expected_revision`

[backend/app/schemas/import_exclusions.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L42) · type `int`

```python
Field(ge=1)
```

<a id="import_exclusions-exclusionrule-id"></a>
### `import_exclusions.ExclusionRule.id`

[backend/app/schemas/import_exclusions.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L47) · type `int`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionrule-revision"></a>
### `import_exclusions.ExclusionRule.revision`

[backend/app/schemas/import_exclusions.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L48) · type `int`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionrule-created_at"></a>
### `import_exclusions.ExclusionRule.created_at`

[backend/app/schemas/import_exclusions.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L49) · type `datetime`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionrule-updated_at"></a>
### `import_exclusions.ExclusionRule.updated_at`

[backend/app/schemas/import_exclusions.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L50) · type `datetime`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionwrite-rule"></a>
### `import_exclusions.ExclusionWrite.rule`

[backend/app/schemas/import_exclusions.py:54](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L54) · type `ExclusionRule`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionwrite-policy_revision"></a>
### `import_exclusions.ExclusionWrite.policy_revision`

[backend/app/schemas/import_exclusions.py:55](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L55) · type `int`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionlist-items"></a>
### `import_exclusions.ExclusionList.items`

[backend/app/schemas/import_exclusions.py:59](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L59) · type `list[ExclusionRule]`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionlist-total"></a>
### `import_exclusions.ExclusionList.total`

[backend/app/schemas/import_exclusions.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L60) · type `int`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionlist-policy_revision"></a>
### `import_exclusions.ExclusionList.policy_revision`

[backend/app/schemas/import_exclusions.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L61) · type `int`

```python
required / inherited validation
```

<a id="import_exclusions-importcandidate-channel_id"></a>
### `import_exclusions.ImportCandidate.channel_id`

[backend/app/schemas/import_exclusions.py:65](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L65) · type `str`

```python
Field(max_length=44)
```

<a id="import_exclusions-importcandidate-name"></a>
### `import_exclusions.ImportCandidate.name`

[backend/app/schemas/import_exclusions.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L66) · type `str`

```python
Field(max_length=512)
```

<a id="import_exclusions-exclusionpreviewrequest-candidates"></a>
### `import_exclusions.ExclusionPreviewRequest.candidates`

[backend/app/schemas/import_exclusions.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L70) · type `list[ImportCandidate] | None`

```python
Field(default=None, max_length=200)
```

<a id="import_exclusions-exclusionpreview-policy_revision"></a>
### `import_exclusions.ExclusionPreview.policy_revision`

[backend/app/schemas/import_exclusions.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L80) · type `int`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionpreview-scanned"></a>
### `import_exclusions.ExclusionPreview.scanned`

[backend/app/schemas/import_exclusions.py:81](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L81) · type `int`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionpreview-matched"></a>
### `import_exclusions.ExclusionPreview.matched`

[backend/app/schemas/import_exclusions.py:82](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L82) · type `int`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionpreview-complete"></a>
### `import_exclusions.ExclusionPreview.complete`

[backend/app/schemas/import_exclusions.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L83) · type `bool`

```python
required / inherited validation
```

<a id="import_exclusions-exclusionpreview-examples"></a>
### `import_exclusions.ExclusionPreview.examples`

[backend/app/schemas/import_exclusions.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/import_exclusions.py#L84) · type `list[ImportCandidate]`

```python
required / inherited validation
```

<a id="media-audiotrack-index"></a>
### `media.AudioTrack.index`

[backend/app/schemas/media.py:7](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L7) · type `int`

```python
Field(ge=0, description='Zero-based audio track index (ffmpeg 0:a:index)')
```

<a id="media-audiotrack-language"></a>
### `media.AudioTrack.language`

[backend/app/schemas/media.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L8) · type `Optional[str]`

```python
None
```

<a id="media-audiotrack-title"></a>
### `media.AudioTrack.title`

[backend/app/schemas/media.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L9) · type `Optional[str]`

```python
None
```

<a id="media-audiotrack-codec"></a>
### `media.AudioTrack.codec`

[backend/app/schemas/media.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L10) · type `Optional[str]`

```python
None
```

<a id="media-audiotrack-channels"></a>
### `media.AudioTrack.channels`

[backend/app/schemas/media.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L11) · type `Optional[int]`

```python
None
```

<a id="media-audiotrack-channel_layout"></a>
### `media.AudioTrack.channel_layout`

[backend/app/schemas/media.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L12) · type `Optional[str]`

```python
None
```

<a id="media-subtitletrack-index"></a>
### `media.SubtitleTrack.index`

[backend/app/schemas/media.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L16) · type `int`

```python
Field(ge=0, description='Zero-based subtitle track index (ffmpeg 0:s:index)')
```

<a id="media-subtitletrack-language"></a>
### `media.SubtitleTrack.language`

[backend/app/schemas/media.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L17) · type `Optional[str]`

```python
None
```

<a id="media-subtitletrack-codec"></a>
### `media.SubtitleTrack.codec`

[backend/app/schemas/media.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L18) · type `Optional[str]`

```python
None
```

<a id="media-subtitletrack-supported"></a>
### `media.SubtitleTrack.supported`

[backend/app/schemas/media.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media.py#L19) · type `bool`

```python
True
```

<a id="media_servers-mediaservercreate-kind"></a>
### `media_servers.MediaServerCreate.kind`

[backend/app/schemas/media_servers.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L17) · type `MediaServerKind`

```python
required / inherited validation
```

<a id="media_servers-mediaservercreate-name"></a>
### `media_servers.MediaServerCreate.name`

[backend/app/schemas/media_servers.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L18) · type `str`

```python
Field(..., min_length=1, max_length=255)
```

<a id="media_servers-mediaservercreate-base_url"></a>
### `media_servers.MediaServerCreate.base_url`

[backend/app/schemas/media_servers.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L19) · type `str`

```python
Field(..., min_length=1, max_length=1024)
```

<a id="media_servers-mediaservercreate-api_key"></a>
### `media_servers.MediaServerCreate.api_key`

[backend/app/schemas/media_servers.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L20) · type `Optional[str]`

```python
Field(None, description='Jellyfin API key or Plex owner token')
```

<a id="media_servers-mediaservercreate-tuner_mode"></a>
### `media_servers.MediaServerCreate.tuner_mode`

[backend/app/schemas/media_servers.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L21) · type `TunerMode`

```python
'hdhomerun'
```

<a id="media_servers-mediaservercreate-enabled"></a>
### `media_servers.MediaServerCreate.enabled`

[backend/app/schemas/media_servers.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L22) · type `bool`

```python
True
```

<a id="media_servers-mediaservercreate-auto_refresh"></a>
### `media_servers.MediaServerCreate.auto_refresh`

[backend/app/schemas/media_servers.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L23) · type `bool`

```python
True
```

<a id="media_servers-mediaserverupdate-name"></a>
### `media_servers.MediaServerUpdate.name`

[backend/app/schemas/media_servers.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L27) · type `Optional[str]`

```python
Field(None, min_length=1, max_length=255)
```

<a id="media_servers-mediaserverupdate-base_url"></a>
### `media_servers.MediaServerUpdate.base_url`

[backend/app/schemas/media_servers.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L28) · type `Optional[str]`

```python
Field(None, min_length=1, max_length=1024)
```

<a id="media_servers-mediaserverupdate-api_key"></a>
### `media_servers.MediaServerUpdate.api_key`

[backend/app/schemas/media_servers.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L29) · type `Optional[str]`

```python
Field(None, description='omit = keep, empty = clear')
```

<a id="media_servers-mediaserverupdate-tuner_mode"></a>
### `media_servers.MediaServerUpdate.tuner_mode`

[backend/app/schemas/media_servers.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L30) · type `Optional[TunerMode]`

```python
None
```

<a id="media_servers-mediaserverupdate-enabled"></a>
### `media_servers.MediaServerUpdate.enabled`

[backend/app/schemas/media_servers.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L31) · type `Optional[bool]`

```python
None
```

<a id="media_servers-mediaserverupdate-auto_refresh"></a>
### `media_servers.MediaServerUpdate.auto_refresh`

[backend/app/schemas/media_servers.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L32) · type `Optional[bool]`

```python
None
```

<a id="media_servers-mediaserverresponse-id"></a>
### `media_servers.MediaServerResponse.id`

[backend/app/schemas/media_servers.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L36) · type `int`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-kind"></a>
### `media_servers.MediaServerResponse.kind`

[backend/app/schemas/media_servers.py:37](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L37) · type `MediaServerKind`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-name"></a>
### `media_servers.MediaServerResponse.name`

[backend/app/schemas/media_servers.py:38](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L38) · type `str`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-base_url"></a>
### `media_servers.MediaServerResponse.base_url`

[backend/app/schemas/media_servers.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L39) · type `str`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-tuner_mode"></a>
### `media_servers.MediaServerResponse.tuner_mode`

[backend/app/schemas/media_servers.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L40) · type `TunerMode`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-enabled"></a>
### `media_servers.MediaServerResponse.enabled`

[backend/app/schemas/media_servers.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L41) · type `bool`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-auto_refresh"></a>
### `media_servers.MediaServerResponse.auto_refresh`

[backend/app/schemas/media_servers.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L42) · type `bool`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-has_api_key"></a>
### `media_servers.MediaServerResponse.has_api_key`

[backend/app/schemas/media_servers.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L43) · type `bool`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-connected"></a>
### `media_servers.MediaServerResponse.connected`

[backend/app/schemas/media_servers.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L44) · type `bool`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-tuner_host_id"></a>
### `media_servers.MediaServerResponse.tuner_host_id`

[backend/app/schemas/media_servers.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L45) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaserverresponse-listing_provider_id"></a>
### `media_servers.MediaServerResponse.listing_provider_id`

[backend/app/schemas/media_servers.py:46](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L46) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaserverresponse-dvr_key"></a>
### `media_servers.MediaServerResponse.dvr_key`

[backend/app/schemas/media_servers.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L47) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaserverresponse-last_sync_at"></a>
### `media_servers.MediaServerResponse.last_sync_at`

[backend/app/schemas/media_servers.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L48) · type `Optional[datetime]`

```python
None
```

<a id="media_servers-mediaserverresponse-last_sync_status"></a>
### `media_servers.MediaServerResponse.last_sync_status`

[backend/app/schemas/media_servers.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L49) · type `SyncStatus`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-last_error"></a>
### `media_servers.MediaServerResponse.last_error`

[backend/app/schemas/media_servers.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L50) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaserverresponse-server_version"></a>
### `media_servers.MediaServerResponse.server_version`

[backend/app/schemas/media_servers.py:51](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L51) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaserverresponse-created_at"></a>
### `media_servers.MediaServerResponse.created_at`

[backend/app/schemas/media_servers.py:52](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L52) · type `datetime`

```python
required / inherited validation
```

<a id="media_servers-mediaserverresponse-updated_at"></a>
### `media_servers.MediaServerResponse.updated_at`

[backend/app/schemas/media_servers.py:53](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L53) · type `datetime`

```python
required / inherited validation
```

<a id="media_servers-mediaservertestrequest-kind"></a>
### `media_servers.MediaServerTestRequest.kind`

[backend/app/schemas/media_servers.py:59](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L59) · type `MediaServerKind`

```python
required / inherited validation
```

<a id="media_servers-mediaservertestrequest-base_url"></a>
### `media_servers.MediaServerTestRequest.base_url`

[backend/app/schemas/media_servers.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L60) · type `str`

```python
required / inherited validation
```

<a id="media_servers-mediaservertestrequest-api_key"></a>
### `media_servers.MediaServerTestRequest.api_key`

[backend/app/schemas/media_servers.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L61) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaservertestrequest-id"></a>
### `media_servers.MediaServerTestRequest.id`

[backend/app/schemas/media_servers.py:62](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L62) · type `Optional[int]`

```python
None
```

<a id="media_servers-mediaserverproberesponse-reachable"></a>
### `media_servers.MediaServerProbeResponse.reachable`

[backend/app/schemas/media_servers.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L66) · type `bool`

```python
required / inherited validation
```

<a id="media_servers-mediaserverproberesponse-authenticated"></a>
### `media_servers.MediaServerProbeResponse.authenticated`

[backend/app/schemas/media_servers.py:67](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L67) · type `bool`

```python
required / inherited validation
```

<a id="media_servers-mediaserverproberesponse-credentials"></a>
### `media_servers.MediaServerProbeResponse.credentials`

[backend/app/schemas/media_servers.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L70) · type `Literal['ok', 'missing', 'rejected']`

```python
required / inherited validation
```

<a id="media_servers-mediaserverproberesponse-version"></a>
### `media_servers.MediaServerProbeResponse.version`

[backend/app/schemas/media_servers.py:71](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L71) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaserverproberesponse-message"></a>
### `media_servers.MediaServerProbeResponse.message`

[backend/app/schemas/media_servers.py:72](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L72) · type `str`

```python
required / inherited validation
```

<a id="media_servers-mediaserverproberesponse-tuner_access"></a>
### `media_servers.MediaServerProbeResponse.tuner_access`

[backend/app/schemas/media_servers.py:73](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L73) · type `TunerAccessResponse`

```python
required / inherited validation
```

<a id="media_servers-mediaserverrefreshresponse-status"></a>
### `media_servers.MediaServerRefreshResponse.status`

[backend/app/schemas/media_servers.py:77](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L77) · type `Literal['ok', 'error', 'manual']`

```python
required / inherited validation
```

<a id="media_servers-mediaserverrefreshresponse-message"></a>
### `media_servers.MediaServerRefreshResponse.message`

[backend/app/schemas/media_servers.py:78](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L78) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaserverrefreshresponse-last_sync_at"></a>
### `media_servers.MediaServerRefreshResponse.last_sync_at`

[backend/app/schemas/media_servers.py:79](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L79) · type `Optional[datetime]`

```python
None
```

<a id="media_servers-mediaserverstatusresponse-connected"></a>
### `media_servers.MediaServerStatusResponse.connected`

[backend/app/schemas/media_servers.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L83) · type `bool`

```python
required / inherited validation
```

<a id="media_servers-mediaserverstatusresponse-channel_count"></a>
### `media_servers.MediaServerStatusResponse.channel_count`

[backend/app/schemas/media_servers.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L84) · type `Optional[int]`

```python
None
```

<a id="media_servers-mediaserverstatusresponse-refresh_state"></a>
### `media_servers.MediaServerStatusResponse.refresh_state`

[backend/app/schemas/media_servers.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L85) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaserverstatusresponse-last_result"></a>
### `media_servers.MediaServerStatusResponse.last_result`

[backend/app/schemas/media_servers.py:86](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L86) · type `Optional[str]`

```python
None
```

<a id="media_servers-mediaserverstatusresponse-steps"></a>
### `media_servers.MediaServerStatusResponse.steps`

[backend/app/schemas/media_servers.py:87](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L87) · type `List[str]`

```python
Field(default_factory=list)
```

<a id="media_servers-mediaserverstatusresponse-paste"></a>
### `media_servers.MediaServerStatusResponse.paste`

[backend/app/schemas/media_servers.py:88](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L88) · type `Dict[str, str]`

```python
Field(default_factory=dict)
```

<a id="media_servers-mediaserverstatusresponse-error"></a>
### `media_servers.MediaServerStatusResponse.error`

[backend/app/schemas/media_servers.py:89](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/media_servers.py#L89) · type `Optional[str]`

```python
None
```

<a id="player-playersessioncreate-subtitle_index"></a>
### `player.PlayerSessionCreate.subtitle_index`

[backend/app/schemas/player.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L15) · type `Optional[int]`

```python
Field(None, ge=0, le=63, description='Subtitle track to play; null disables subtitles')
```

<a id="player-playersessioncreate-audio_index"></a>
### `player.PlayerSessionCreate.audio_index`

[backend/app/schemas/player.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L16) · type `Optional[int]`

```python
Field(None, ge=0, le=63, description='Audio track to play; null uses the first available audio track')
```

<a id="player-playersessioncreate-content_id"></a>
### `player.PlayerSessionCreate.content_id`

[backend/app/schemas/player.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L17) · type `str`

```python
Field(..., pattern='^(?:url:)?[0-9a-fA-F]{40}$', description='AceStream content ID (40 hex) or imported HTTP stream ID (url: followed by 40 hex)')
```

<a id="player-playercodecs-video"></a>
### `player.PlayerCodecs.video`

[backend/app/schemas/player.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L21) · type `Optional[str]`

```python
None
```

<a id="player-playercodecs-audio"></a>
### `player.PlayerCodecs.audio`

[backend/app/schemas/player.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L22) · type `Optional[str]`

```python
None
```

<a id="player-playerstats-status"></a>
### `player.PlayerStats.status`

[backend/app/schemas/player.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L26) · type `str`

```python
required / inherited validation
```

<a id="player-playerstats-peers"></a>
### `player.PlayerStats.peers`

[backend/app/schemas/player.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L27) · type `int`

```python
required / inherited validation
```

<a id="player-playerstats-speed_down"></a>
### `player.PlayerStats.speed_down`

[backend/app/schemas/player.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L28) · type `int`

```python
required / inherited validation
```

<a id="player-playerstats-speed_up"></a>
### `player.PlayerStats.speed_up`

[backend/app/schemas/player.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L29) · type `int`

```python
required / inherited validation
```

<a id="player-playersessionstatus-subtitle_index"></a>
### `player.PlayerSessionStatus.subtitle_index`

[backend/app/schemas/player.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L33) · type `Optional[int]`

```python
None
```

<a id="player-playersessionstatus-subtitle_tracks"></a>
### `player.PlayerSessionStatus.subtitle_tracks`

[backend/app/schemas/player.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L34) · type `List[SubtitleTrack]`

```python
Field(default_factory=list)
```

<a id="player-playersessionstatus-audio_index"></a>
### `player.PlayerSessionStatus.audio_index`

[backend/app/schemas/player.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L35) · type `Optional[int]`

```python
None
```

<a id="player-playersessionstatus-audio_tracks"></a>
### `player.PlayerSessionStatus.audio_tracks`

[backend/app/schemas/player.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L36) · type `List[AudioTrack]`

```python
Field(default_factory=list)
```

<a id="player-playersessionstatus-id"></a>
### `player.PlayerSessionStatus.id`

[backend/app/schemas/player.py:37](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L37) · type `str`

```python
required / inherited validation
```

<a id="player-playersessionstatus-content_id"></a>
### `player.PlayerSessionStatus.content_id`

[backend/app/schemas/player.py:38](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L38) · type `str`

```python
required / inherited validation
```

<a id="player-playersessionstatus-state"></a>
### `player.PlayerSessionStatus.state`

[backend/app/schemas/player.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L39) · type `PlayerStateValue`

```python
required / inherited validation
```

<a id="player-playersessionstatus-error"></a>
### `player.PlayerSessionStatus.error`

[backend/app/schemas/player.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L40) · type `Optional[PlayerErrorValue]`

```python
None
```

<a id="player-playersessionstatus-error_message"></a>
### `player.PlayerSessionStatus.error_message`

[backend/app/schemas/player.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L41) · type `str`

```python
''
```

<a id="player-playersessionstatus-codecs"></a>
### `player.PlayerSessionStatus.codecs`

[backend/app/schemas/player.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L42) · type `PlayerCodecs`

```python
required / inherited validation
```

<a id="player-playersessionstatus-stats"></a>
### `player.PlayerSessionStatus.stats`

[backend/app/schemas/player.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L43) · type `Optional[PlayerStats]`

```python
None
```

<a id="player-playersessionstatus-viewers"></a>
### `player.PlayerSessionStatus.viewers`

[backend/app/schemas/player.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L44) · type `int`

```python
required / inherited validation
```

<a id="player-playersessionstatus-playlist_url"></a>
### `player.PlayerSessionStatus.playlist_url`

[backend/app/schemas/player.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L45) · type `str`

```python
required / inherited validation
```

<a id="player-playersessionstatus-hls_ready"></a>
### `player.PlayerSessionStatus.hls_ready`

[backend/app/schemas/player.py:46](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L46) · type `bool`

```python
required / inherited validation
```

<a id="player-playersessionlistresponse-sessions"></a>
### `player.PlayerSessionListResponse.sessions`

[backend/app/schemas/player.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L50) · type `List[PlayerSessionStatus]`

```python
required / inherited validation
```

<a id="player-playercapabilities-ffmpeg_available"></a>
### `player.PlayerCapabilities.ffmpeg_available`

[backend/app/schemas/player.py:54](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L54) · type `bool`

```python
required / inherited validation
```

<a id="player-playercapabilities-ffmpeg_path"></a>
### `player.PlayerCapabilities.ffmpeg_path`

[backend/app/schemas/player.py:55](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L55) · type `Optional[str]`

```python
None
```

<a id="player-playercapabilities-max_sessions"></a>
### `player.PlayerCapabilities.max_sessions`

[backend/app/schemas/player.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L56) · type `int`

```python
required / inherited validation
```

<a id="player-playercapabilities-hls_dir"></a>
### `player.PlayerCapabilities.hls_dir`

[backend/app/schemas/player.py:57](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L57) · type `str`

```python
required / inherited validation
```

<a id="player-activestream-kind"></a>
### `player.ActiveStream.kind`

[backend/app/schemas/player.py:68](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L68) · type `Literal['browser', 'relay']`

```python
required / inherited validation
```

<a id="player-activestream-id"></a>
### `player.ActiveStream.id`

[backend/app/schemas/player.py:69](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L69) · type `str`

```python
required / inherited validation
```

<a id="player-activestream-content_id"></a>
### `player.ActiveStream.content_id`

[backend/app/schemas/player.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L70) · type `str`

```python
required / inherited validation
```

<a id="player-activestream-channel_name"></a>
### `player.ActiveStream.channel_name`

[backend/app/schemas/player.py:72](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L72) · type `Optional[str]`

```python
None
```

<a id="player-activestream-state"></a>
### `player.ActiveStream.state`

[backend/app/schemas/player.py:73](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L73) · type `Literal['starting', 'ready', 'error', 'stopped', 'streaming']`

```python
required / inherited validation
```

<a id="player-activestream-viewers"></a>
### `player.ActiveStream.viewers`

[backend/app/schemas/player.py:74](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L74) · type `int`

```python
1
```

<a id="player-activestream-peers"></a>
### `player.ActiveStream.peers`

[backend/app/schemas/player.py:76](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L76) · type `Optional[int]`

```python
None
```

<a id="player-activestream-client_label"></a>
### `player.ActiveStream.client_label`

[backend/app/schemas/player.py:78](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L78) · type `Optional[str]`

```python
None
```

<a id="player-activestream-started_at"></a>
### `player.ActiveStream.started_at`

[backend/app/schemas/player.py:79](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L79) · type `Optional[datetime]`

```python
None
```

<a id="player-activestreamlistresponse-streams"></a>
### `player.ActiveStreamListResponse.streams`

[backend/app/schemas/player.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/player.py#L83) · type `List[ActiveStream]`

```python
required / inherited validation
```

<a id="recordings-recordingsettings-enabled"></a>
### `recordings.RecordingSettings.enabled`

[backend/app/schemas/recordings.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L12) · type `bool`

```python
False
```

<a id="recordings-recordingsettings-max_concurrent"></a>
### `recordings.RecordingSettings.max_concurrent`

[backend/app/schemas/recordings.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L13) · type `int`

```python
Field(default=1, ge=1, le=4)
```

<a id="recordings-recordingsettings-min_free_bytes"></a>
### `recordings.RecordingSettings.min_free_bytes`

[backend/app/schemas/recordings.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L14) · type `int`

```python
Field(default=2 * 1024 ** 3, ge=64 * 1024 ** 2)
```

<a id="recordings-recordingsettings-max_recording_bytes"></a>
### `recordings.RecordingSettings.max_recording_bytes`

[backend/app/schemas/recordings.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L15) · type `int`

```python
Field(default=100 * 1024 ** 3, ge=1024 ** 2)
```

<a id="recordings-recordingsettings-retention_days"></a>
### `recordings.RecordingSettings.retention_days`

[backend/app/schemas/recordings.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L16) · type `int | None`

```python
Field(default=None, ge=1, le=3650)
```

<a id="recordings-programmeselection-id"></a>
### `recordings.ProgrammeSelection.id`

[backend/app/schemas/recordings.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L21) · type `int`

```python
required / inherited validation
```

<a id="recordings-programmeselection-epg_channel_id"></a>
### `recordings.ProgrammeSelection.epg_channel_id`

[backend/app/schemas/recordings.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L22) · type `int`

```python
required / inherited validation
```

<a id="recordings-programmeselection-start_time"></a>
### `recordings.ProgrammeSelection.start_time`

[backend/app/schemas/recordings.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L23) · type `AwareDatetime`

```python
required / inherited validation
```

<a id="recordings-programmeselection-end_time"></a>
### `recordings.ProgrammeSelection.end_time`

[backend/app/schemas/recordings.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L24) · type `AwareDatetime`

```python
required / inherited validation
```

<a id="recordings-programmeselection-title"></a>
### `recordings.ProgrammeSelection.title`

[backend/app/schemas/recordings.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L25) · type `str`

```python
required / inherited validation
```

<a id="recordings-programmeselection-subtitle"></a>
### `recordings.ProgrammeSelection.subtitle`

[backend/app/schemas/recordings.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L26) · type `str | None`

```python
None
```

<a id="recordings-programmeselection-description"></a>
### `recordings.ProgrammeSelection.description`

[backend/app/schemas/recordings.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L27) · type `str | None`

```python
None
```

<a id="recordings-programmeselection-category"></a>
### `recordings.ProgrammeSelection.category`

[backend/app/schemas/recordings.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L28) · type `str | None`

```python
None
```

<a id="recordings-recordingcreate-tv_channel_id"></a>
### `recordings.RecordingCreate.tv_channel_id`

[backend/app/schemas/recordings.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L33) · type `int`

```python
Field(gt=0)
```

<a id="recordings-recordingcreate-mode"></a>
### `recordings.RecordingCreate.mode`

[backend/app/schemas/recordings.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L34) · type `Literal['now', 'schedule']`

```python
'schedule'
```

<a id="recordings-recordingcreate-start_time"></a>
### `recordings.RecordingCreate.start_time`

[backend/app/schemas/recordings.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L35) · type `AwareDatetime`

```python
required / inherited validation
```

<a id="recordings-recordingcreate-end_time"></a>
### `recordings.RecordingCreate.end_time`

[backend/app/schemas/recordings.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L36) · type `AwareDatetime`

```python
required / inherited validation
```

<a id="recordings-recordingcreate-timezone"></a>
### `recordings.RecordingCreate.timezone`

[backend/app/schemas/recordings.py:37](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L37) · type `str`

```python
Field(max_length=64)
```

<a id="recordings-recordingcreate-programme"></a>
### `recordings.RecordingCreate.programme`

[backend/app/schemas/recordings.py:38](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L38) · type `ProgrammeSelection | None`

```python
None
```

<a id="recordings-recordingcreate-idempotency_key"></a>
### `recordings.RecordingCreate.idempotency_key`

[backend/app/schemas/recordings.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L39) · type `str`

```python
Field(min_length=16, max_length=64, pattern='^[a-zA-Z0-9_-]+$')
```

<a id="recordings-recordingedit-expected_revision"></a>
### `recordings.RecordingEdit.expected_revision`

[backend/app/schemas/recordings.py:68](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L68) · type `int`

```python
Field(ge=1)
```

<a id="recordings-recordingedit-start_time"></a>
### `recordings.RecordingEdit.start_time`

[backend/app/schemas/recordings.py:69](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L69) · type `AwareDatetime | None`

```python
None
```

<a id="recordings-recordingedit-end_time"></a>
### `recordings.RecordingEdit.end_time`

[backend/app/schemas/recordings.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L70) · type `AwareDatetime | None`

```python
None
```

<a id="recordings-recordingedit-protected"></a>
### `recordings.RecordingEdit.protected`

[backend/app/schemas/recordings.py:71](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L71) · type `bool | None`

```python
None
```

<a id="recordings-recordingsnapshot-title"></a>
### `recordings.RecordingSnapshot.title`

[backend/app/schemas/recordings.py:75](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L75) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingsnapshot-channel_name"></a>
### `recordings.RecordingSnapshot.channel_name`

[backend/app/schemas/recordings.py:76](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L76) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingsnapshot-subtitle"></a>
### `recordings.RecordingSnapshot.subtitle`

[backend/app/schemas/recordings.py:77](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L77) · type `str | None`

```python
None
```

<a id="recordings-recordingsnapshot-description"></a>
### `recordings.RecordingSnapshot.description`

[backend/app/schemas/recordings.py:78](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L78) · type `str | None`

```python
None
```

<a id="recordings-recordingsnapshot-category"></a>
### `recordings.RecordingSnapshot.category`

[backend/app/schemas/recordings.py:79](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L79) · type `str | None`

```python
None
```

<a id="recordings-recordingsnapshot-guide_source_uuid"></a>
### `recordings.RecordingSnapshot.guide_source_uuid`

[backend/app/schemas/recordings.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L80) · type `str | None`

```python
None
```

<a id="recordings-recordingsnapshot-guide_channel_id"></a>
### `recordings.RecordingSnapshot.guide_channel_id`

[backend/app/schemas/recordings.py:81](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L81) · type `str | None`

```python
None
```

<a id="recordings-recordingsnapshot-original_start"></a>
### `recordings.RecordingSnapshot.original_start`

[backend/app/schemas/recordings.py:82](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L82) · type `datetime | None`

```python
None
```

<a id="recordings-recordingsnapshot-original_end"></a>
### `recordings.RecordingSnapshot.original_end`

[backend/app/schemas/recordings.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L83) · type `datetime | None`

```python
None
```

<a id="recordings-recordingsnapshot-provider_programme_id"></a>
### `recordings.RecordingSnapshot.provider_programme_id`

[backend/app/schemas/recordings.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L84) · type `str | None`

```python
None
```

<a id="recordings-recordinggap-start"></a>
### `recordings.RecordingGap.start`

[backend/app/schemas/recordings.py:88](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L88) · type `datetime`

```python
required / inherited validation
```

<a id="recordings-recordinggap-end"></a>
### `recordings.RecordingGap.end`

[backend/app/schemas/recordings.py:89](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L89) · type `datetime`

```python
required / inherited validation
```

<a id="recordings-recordinggap-reason"></a>
### `recordings.RecordingGap.reason`

[backend/app/schemas/recordings.py:90](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L90) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingfile-id"></a>
### `recordings.RecordingFile.id`

[backend/app/schemas/recordings.py:95](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L95) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingfile-kind"></a>
### `recordings.RecordingFile.kind`

[backend/app/schemas/recordings.py:96](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L96) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingfile-state"></a>
### `recordings.RecordingFile.state`

[backend/app/schemas/recordings.py:97](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L97) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingfile-profile"></a>
### `recordings.RecordingFile.profile`

[backend/app/schemas/recordings.py:98](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L98) · type `str | None`

```python
required / inherited validation
```

<a id="recordings-recordingfile-source_artifact_id"></a>
### `recordings.RecordingFile.source_artifact_id`

[backend/app/schemas/recordings.py:99](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L99) · type `str | None`

```python
required / inherited validation
```

<a id="recordings-recordingfile-bytes"></a>
### `recordings.RecordingFile.bytes`

[backend/app/schemas/recordings.py:100](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L100) · type `int`

```python
required / inherited validation
```

<a id="recordings-recordingfile-duration"></a>
### `recordings.RecordingFile.duration`

[backend/app/schemas/recordings.py:101](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L101) · type `float | None`

```python
required / inherited validation
```

<a id="recordings-recordingfile-codecs"></a>
### `recordings.RecordingFile.codecs`

[backend/app/schemas/recordings.py:102](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L102) · type `list[str]`

```python
required / inherited validation
```

<a id="recordings-recordingfile-reason"></a>
### `recordings.RecordingFile.reason`

[backend/app/schemas/recordings.py:103](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L103) · type `str | None`

```python
required / inherited validation
```

<a id="recordings-recordingattemptview-id"></a>
### `recordings.RecordingAttemptView.id`

[backend/app/schemas/recordings.py:108](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L108) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingattemptview-ordinal"></a>
### `recordings.RecordingAttemptView.ordinal`

[backend/app/schemas/recordings.py:109](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L109) · type `int`

```python
required / inherited validation
```

<a id="recordings-recordingattemptview-source_id"></a>
### `recordings.RecordingAttemptView.source_id`

[backend/app/schemas/recordings.py:110](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L110) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingattemptview-route"></a>
### `recordings.RecordingAttemptView.route`

[backend/app/schemas/recordings.py:111](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L111) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingattemptview-started_at"></a>
### `recordings.RecordingAttemptView.started_at`

[backend/app/schemas/recordings.py:112](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L112) · type `datetime`

```python
required / inherited validation
```

<a id="recordings-recordingattemptview-ended_at"></a>
### `recordings.RecordingAttemptView.ended_at`

[backend/app/schemas/recordings.py:113](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L113) · type `datetime | None`

```python
required / inherited validation
```

<a id="recordings-recordingattemptview-exit_code"></a>
### `recordings.RecordingAttemptView.exit_code`

[backend/app/schemas/recordings.py:114](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L114) · type `int | None`

```python
required / inherited validation
```

<a id="recordings-recordingattemptview-reason"></a>
### `recordings.RecordingAttemptView.reason`

[backend/app/schemas/recordings.py:115](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L115) · type `str | None`

```python
required / inherited validation
```

<a id="recordings-recordingview-id"></a>
### `recordings.RecordingView.id`

[backend/app/schemas/recordings.py:120](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L120) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingview-tv_channel_id"></a>
### `recordings.RecordingView.tv_channel_id`

[backend/app/schemas/recordings.py:121](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L121) · type `int | None`

```python
required / inherited validation
```

<a id="recordings-recordingview-snapshot"></a>
### `recordings.RecordingView.snapshot`

[backend/app/schemas/recordings.py:122](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L122) · type `RecordingSnapshot`

```python
required / inherited validation
```

<a id="recordings-recordingview-start_time"></a>
### `recordings.RecordingView.start_time`

[backend/app/schemas/recordings.py:123](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L123) · type `datetime`

```python
required / inherited validation
```

<a id="recordings-recordingview-end_time"></a>
### `recordings.RecordingView.end_time`

[backend/app/schemas/recordings.py:124](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L124) · type `datetime`

```python
required / inherited validation
```

<a id="recordings-recordingview-timezone"></a>
### `recordings.RecordingView.timezone`

[backend/app/schemas/recordings.py:125](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L125) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingview-state"></a>
### `recordings.RecordingView.state`

[backend/app/schemas/recordings.py:126](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L126) · type `RecordingState`

```python
required / inherited validation
```

<a id="recordings-recordingview-revision"></a>
### `recordings.RecordingView.revision`

[backend/app/schemas/recordings.py:127](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L127) · type `int`

```python
required / inherited validation
```

<a id="recordings-recordingview-protected"></a>
### `recordings.RecordingView.protected`

[backend/app/schemas/recordings.py:128](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L128) · type `bool`

```python
required / inherited validation
```

<a id="recordings-recordingview-actual_start"></a>
### `recordings.RecordingView.actual_start`

[backend/app/schemas/recordings.py:129](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L129) · type `datetime | None`

```python
required / inherited validation
```

<a id="recordings-recordingview-actual_end"></a>
### `recordings.RecordingView.actual_end`

[backend/app/schemas/recordings.py:130](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L130) · type `datetime | None`

```python
required / inherited validation
```

<a id="recordings-recordingview-reason"></a>
### `recordings.RecordingView.reason`

[backend/app/schemas/recordings.py:131](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L131) · type `str | None`

```python
required / inherited validation
```

<a id="recordings-recordingview-gaps"></a>
### `recordings.RecordingView.gaps`

[backend/app/schemas/recordings.py:132](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L132) · type `list[RecordingGap]`

```python
required / inherited validation
```

<a id="recordings-recordingview-created_at"></a>
### `recordings.RecordingView.created_at`

[backend/app/schemas/recordings.py:133](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L133) · type `datetime`

```python
required / inherited validation
```

<a id="recordings-recordingview-files"></a>
### `recordings.RecordingView.files`

[backend/app/schemas/recordings.py:134](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L134) · type `list[RecordingFile]`

```python
Field(default_factory=list)
```

<a id="recordings-recordingview-attempts"></a>
### `recordings.RecordingView.attempts`

[backend/app/schemas/recordings.py:135](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L135) · type `list[RecordingAttemptView]`

```python
Field(default_factory=list)
```

<a id="recordings-recordinglist-items"></a>
### `recordings.RecordingList.items`

[backend/app/schemas/recordings.py:139](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L139) · type `list[RecordingView]`

```python
required / inherited validation
```

<a id="recordings-recordinglist-total"></a>
### `recordings.RecordingList.total`

[backend/app/schemas/recordings.py:140](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L140) · type `int`

```python
required / inherited validation
```

<a id="recordings-recordingcapabilities-enabled"></a>
### `recordings.RecordingCapabilities.enabled`

[backend/app/schemas/recordings.py:144](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L144) · type `bool`

```python
required / inherited validation
```

<a id="recordings-recordingcapabilities-available"></a>
### `recordings.RecordingCapabilities.available`

[backend/app/schemas/recordings.py:145](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L145) · type `bool`

```python
required / inherited validation
```

<a id="recordings-recordingcapabilities-storage_ready"></a>
### `recordings.RecordingCapabilities.storage_ready`

[backend/app/schemas/recordings.py:146](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L146) · type `bool`

```python
required / inherited validation
```

<a id="recordings-recordingcapabilities-message"></a>
### `recordings.RecordingCapabilities.message`

[backend/app/schemas/recordings.py:147](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L147) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingcapabilities-stream_copy"></a>
### `recordings.RecordingCapabilities.stream_copy`

[backend/app/schemas/recordings.py:148](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L148) · type `bool`

```python
required / inherited validation
```

<a id="recordings-recordingcapabilities-mp4_remux"></a>
### `recordings.RecordingCapabilities.mp4_remux`

[backend/app/schemas/recordings.py:149](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L149) · type `bool`

```python
required / inherited validation
```

<a id="recordings-recordingcapabilities-aac_conversion"></a>
### `recordings.RecordingCapabilities.aac_conversion`

[backend/app/schemas/recordings.py:150](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L150) · type `bool`

```python
required / inherited validation
```

<a id="recordings-recordingcapabilities-settings"></a>
### `recordings.RecordingCapabilities.settings`

[backend/app/schemas/recordings.py:151](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L151) · type `RecordingSettings`

```python
required / inherited validation
```

<a id="recordings-recordingconversion-file_id"></a>
### `recordings.RecordingConversion.file_id`

[backend/app/schemas/recordings.py:155](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L155) · type `str`

```python
Field(pattern='^[0-9a-f]{32}$')
```

<a id="recordings-recordingconversion-profile"></a>
### `recordings.RecordingConversion.profile`

[backend/app/schemas/recordings.py:156](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L156) · type `Literal['remux', 'aac']`

```python
'remux'
```

<a id="recordings-recordingplaybackrequest-file_id"></a>
### `recordings.RecordingPlaybackRequest.file_id`

[backend/app/schemas/recordings.py:160](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L160) · type `str`

```python
Field(pattern='^[0-9a-f]{32}$')
```

<a id="recordings-recordingplaybackview-id"></a>
### `recordings.RecordingPlaybackView.id`

[backend/app/schemas/recordings.py:164](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L164) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingplaybackview-state"></a>
### `recordings.RecordingPlaybackView.state`

[backend/app/schemas/recordings.py:165](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L165) · type `Literal['preparing', 'ready', 'failed']`

```python
required / inherited validation
```

<a id="recordings-recordingplaybackview-file_id"></a>
### `recordings.RecordingPlaybackView.file_id`

[backend/app/schemas/recordings.py:166](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L166) · type `str`

```python
required / inherited validation
```

<a id="recordings-recordingplaybackview-media_url"></a>
### `recordings.RecordingPlaybackView.media_url`

[backend/app/schemas/recordings.py:167](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L167) · type `str | None`

```python
None
```

<a id="recordings-recordingplaybackview-message"></a>
### `recordings.RecordingPlaybackView.message`

[backend/app/schemas/recordings.py:168](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py#L168) · type `str`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerbase-name"></a>
### `remote_players.RemotePlayerBase.name`

[backend/app/schemas/remote_players.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L14) · type `str`

```python
Field(..., min_length=1, max_length=255)
```

<a id="remote_players-remoteplayerbase-kind"></a>
### `remote_players.RemotePlayerBase.kind`

[backend/app/schemas/remote_players.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L15) · type `PlayerKind`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerbase-host"></a>
### `remote_players.RemotePlayerBase.host`

[backend/app/schemas/remote_players.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L16) · type `str`

```python
Field(..., min_length=1, max_length=255, description='Hostname or IP, no scheme')
```

<a id="remote_players-remoteplayerbase-port"></a>
### `remote_players.RemotePlayerBase.port`

[backend/app/schemas/remote_players.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L17) · type `int`

```python
Field(8080, ge=1, le=65535)
```

<a id="remote_players-remoteplayerbase-username"></a>
### `remote_players.RemotePlayerBase.username`

[backend/app/schemas/remote_players.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L18) · type `Optional[str]`

```python
Field(None, max_length=255, description='Kodi only; default kodi')
```

<a id="remote_players-remoteplayerbase-base_url_id"></a>
### `remote_players.RemotePlayerBase.base_url_id`

[backend/app/schemas/remote_players.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L19) · type `Optional[int]`

```python
Field(None, description='Stream link format; null = server relay URL')
```

<a id="remote_players-remoteplayercreate-password"></a>
### `remote_players.RemotePlayerCreate.password`

[backend/app/schemas/remote_players.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L23) · type `Optional[str]`

```python
Field(None, max_length=1024)
```

<a id="remote_players-remoteplayerupdate-name"></a>
### `remote_players.RemotePlayerUpdate.name`

[backend/app/schemas/remote_players.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L27) · type `Optional[str]`

```python
Field(None, min_length=1, max_length=255)
```

<a id="remote_players-remoteplayerupdate-kind"></a>
### `remote_players.RemotePlayerUpdate.kind`

[backend/app/schemas/remote_players.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L28) · type `Optional[PlayerKind]`

```python
None
```

<a id="remote_players-remoteplayerupdate-host"></a>
### `remote_players.RemotePlayerUpdate.host`

[backend/app/schemas/remote_players.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L29) · type `Optional[str]`

```python
Field(None, min_length=1, max_length=255)
```

<a id="remote_players-remoteplayerupdate-port"></a>
### `remote_players.RemotePlayerUpdate.port`

[backend/app/schemas/remote_players.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L30) · type `Optional[int]`

```python
Field(None, ge=1, le=65535)
```

<a id="remote_players-remoteplayerupdate-username"></a>
### `remote_players.RemotePlayerUpdate.username`

[backend/app/schemas/remote_players.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L31) · type `Optional[str]`

```python
Field(None, max_length=255)
```

<a id="remote_players-remoteplayerupdate-password"></a>
### `remote_players.RemotePlayerUpdate.password`

[backend/app/schemas/remote_players.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L32) · type `Optional[str]`

```python
Field(None, max_length=1024, description='omit = keep, empty string = clear')
```

<a id="remote_players-remoteplayerupdate-base_url_id"></a>
### `remote_players.RemotePlayerUpdate.base_url_id`

[backend/app/schemas/remote_players.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L33) · type `Optional[int]`

```python
None
```

<a id="remote_players-remoteplayerupdate-clear_base_url"></a>
### `remote_players.RemotePlayerUpdate.clear_base_url`

[backend/app/schemas/remote_players.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L34) · type `bool`

```python
False
```

<a id="remote_players-remoteplayerresponse-id"></a>
### `remote_players.RemotePlayerResponse.id`

[backend/app/schemas/remote_players.py:38](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L38) · type `int`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerresponse-has_password"></a>
### `remote_players.RemotePlayerResponse.has_password`

[backend/app/schemas/remote_players.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L39) · type `bool`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerresponse-created_at"></a>
### `remote_players.RemotePlayerResponse.created_at`

[backend/app/schemas/remote_players.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L40) · type `datetime`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerresponse-updated_at"></a>
### `remote_players.RemotePlayerResponse.updated_at`

[backend/app/schemas/remote_players.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L41) · type `datetime`

```python
required / inherited validation
```

<a id="remote_players-remoteplayertestrequest-kind"></a>
### `remote_players.RemotePlayerTestRequest.kind`

[backend/app/schemas/remote_players.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L47) · type `PlayerKind`

```python
required / inherited validation
```

<a id="remote_players-remoteplayertestrequest-host"></a>
### `remote_players.RemotePlayerTestRequest.host`

[backend/app/schemas/remote_players.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L48) · type `str`

```python
Field(..., min_length=1, max_length=255)
```

<a id="remote_players-remoteplayertestrequest-port"></a>
### `remote_players.RemotePlayerTestRequest.port`

[backend/app/schemas/remote_players.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L49) · type `int`

```python
Field(8080, ge=1, le=65535)
```

<a id="remote_players-remoteplayertestrequest-username"></a>
### `remote_players.RemotePlayerTestRequest.username`

[backend/app/schemas/remote_players.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L50) · type `Optional[str]`

```python
None
```

<a id="remote_players-remoteplayertestrequest-password"></a>
### `remote_players.RemotePlayerTestRequest.password`

[backend/app/schemas/remote_players.py:51](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L51) · type `Optional[str]`

```python
None
```

<a id="remote_players-remoteplayertestrequest-id"></a>
### `remote_players.RemotePlayerTestRequest.id`

[backend/app/schemas/remote_players.py:52](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L52) · type `Optional[int]`

```python
Field(None, description="Use this saved player's password when none is given")
```

<a id="remote_players-tuneraccessresponse-addresses"></a>
### `remote_players.TunerAccessResponse.addresses`

[backend/app/schemas/remote_players.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L56) · type `List[str]`

```python
required / inherited validation
```

<a id="remote_players-tuneraccessresponse-allowed"></a>
### `remote_players.TunerAccessResponse.allowed`

[backend/app/schemas/remote_players.py:57](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L57) · type `bool`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerproberesponse-reachable"></a>
### `remote_players.RemotePlayerProbeResponse.reachable`

[backend/app/schemas/remote_players.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L61) · type `bool`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerproberesponse-authenticated"></a>
### `remote_players.RemotePlayerProbeResponse.authenticated`

[backend/app/schemas/remote_players.py:62](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L62) · type `bool`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerproberesponse-version"></a>
### `remote_players.RemotePlayerProbeResponse.version`

[backend/app/schemas/remote_players.py:63](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L63) · type `Optional[str]`

```python
None
```

<a id="remote_players-remoteplayerproberesponse-message"></a>
### `remote_players.RemotePlayerProbeResponse.message`

[backend/app/schemas/remote_players.py:64](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L64) · type `str`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerproberesponse-hint"></a>
### `remote_players.RemotePlayerProbeResponse.hint`

[backend/app/schemas/remote_players.py:65](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L65) · type `Optional[str]`

```python
None
```

<a id="remote_players-remoteplayerproberesponse-tuner_access"></a>
### `remote_players.RemotePlayerProbeResponse.tuner_access`

[backend/app/schemas/remote_players.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L66) · type `TunerAccessResponse`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerstatusresponse-state"></a>
### `remote_players.RemotePlayerStatusResponse.state`

[backend/app/schemas/remote_players.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L70) · type `Literal['playing', 'paused', 'stopped']`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerstatusresponse-title"></a>
### `remote_players.RemotePlayerStatusResponse.title`

[backend/app/schemas/remote_players.py:71](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L71) · type `Optional[str]`

```python
None
```

<a id="remote_players-remoteplayerstatusresponse-position_s"></a>
### `remote_players.RemotePlayerStatusResponse.position_s`

[backend/app/schemas/remote_players.py:72](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L72) · type `Optional[int]`

```python
None
```

<a id="remote_players-remoteplayerstatusresponse-length_s"></a>
### `remote_players.RemotePlayerStatusResponse.length_s`

[backend/app/schemas/remote_players.py:73](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L73) · type `Optional[int]`

```python
None
```

<a id="remote_players-remoteplayerstatusresponse-volume_pct"></a>
### `remote_players.RemotePlayerStatusResponse.volume_pct`

[backend/app/schemas/remote_players.py:74](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L74) · type `Optional[int]`

```python
None
```

<a id="remote_players-remoteplayerstatusresponse-message"></a>
### `remote_players.RemotePlayerStatusResponse.message`

[backend/app/schemas/remote_players.py:75](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L75) · type `Optional[str]`

```python
None
```

<a id="remote_players-remoteplayerplayrequest-content_id"></a>
### `remote_players.RemotePlayerPlayRequest.content_id`

[backend/app/schemas/remote_players.py:79](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L79) · type `str`

```python
Field(..., pattern='^[0-9a-fA-F]{40}$')
```

<a id="remote_players-remoteplayerplayrequest-title"></a>
### `remote_players.RemotePlayerPlayRequest.title`

[backend/app/schemas/remote_players.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L80) · type `Optional[str]`

```python
None
```

<a id="remote_players-remoteplayerplayresponse-url"></a>
### `remote_players.RemotePlayerPlayResponse.url`

[backend/app/schemas/remote_players.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L84) · type `str`

```python
required / inherited validation
```

<a id="remote_players-remoteplayerplayresponse-warnings"></a>
### `remote_players.RemotePlayerPlayResponse.warnings`

[backend/app/schemas/remote_players.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L85) · type `List[str]`

```python
Field(default_factory=list, description='Why the player probably cannot fetch this URL: localhost | docker-internal | tuner_blocked')
```

<a id="remote_players-remoteplayercommandrequest-command"></a>
### `remote_players.RemotePlayerCommandRequest.command`

[backend/app/schemas/remote_players.py:92](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L92) · type `PlayerCommand`

```python
required / inherited validation
```

<a id="remote_players-remoteplayercommandrequest-value"></a>
### `remote_players.RemotePlayerCommandRequest.value`

[backend/app/schemas/remote_players.py:93](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L93) · type `Optional[int]`

```python
Field(None, ge=0, le=200, description='Percent, volume only')
```

<a id="remote_players-scanrequest-cidr"></a>
### `remote_players.ScanRequest.cidr`

[backend/app/schemas/remote_players.py:104](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L104) · type `str`

```python
required / inherited validation
```

<a id="remote_players-scanrequest-ports"></a>
### `remote_players.ScanRequest.ports`

[backend/app/schemas/remote_players.py:105](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L105) · type `List[int]`

```python
Field(default_factory=lambda: [8080])
```

<a id="remote_players-scanrequest-timeout_ms"></a>
### `remote_players.ScanRequest.timeout_ms`

[backend/app/schemas/remote_players.py:106](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L106) · type `int`

```python
Field(400, ge=50, le=5000)
```

<a id="remote_players-scanhitresponse-host"></a>
### `remote_players.ScanHitResponse.host`

[backend/app/schemas/remote_players.py:110](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L110) · type `str`

```python
required / inherited validation
```

<a id="remote_players-scanhitresponse-port"></a>
### `remote_players.ScanHitResponse.port`

[backend/app/schemas/remote_players.py:111](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L111) · type `int`

```python
required / inherited validation
```

<a id="remote_players-scanhitresponse-kind"></a>
### `remote_players.ScanHitResponse.kind`

[backend/app/schemas/remote_players.py:112](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L112) · type `Literal['vlc', 'kodi', 'unknown']`

```python
required / inherited validation
```

<a id="remote_players-scanhitresponse-hint"></a>
### `remote_players.ScanHitResponse.hint`

[backend/app/schemas/remote_players.py:113](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L113) · type `str`

```python
required / inherited validation
```

<a id="remote_players-scanresultresponse-hosts"></a>
### `remote_players.ScanResultResponse.hosts`

[backend/app/schemas/remote_players.py:117](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L117) · type `List[ScanHitResponse]`

```python
required / inherited validation
```

<a id="remote_players-scanresultresponse-scanned"></a>
### `remote_players.ScanResultResponse.scanned`

[backend/app/schemas/remote_players.py:118](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L118) · type `int`

```python
required / inherited validation
```

<a id="remote_players-scanresultresponse-duration_ms"></a>
### `remote_players.ScanResultResponse.duration_ms`

[backend/app/schemas/remote_players.py:119](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L119) · type `int`

```python
required / inherited validation
```

<a id="remote_players-scandefaultresponse-cidr"></a>
### `remote_players.ScanDefaultResponse.cidr`

[backend/app/schemas/remote_players.py:123](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L123) · type `Optional[str]`

```python
None
```

<a id="remote_players-scandefaultresponse-hint"></a>
### `remote_players.ScanDefaultResponse.hint`

[backend/app/schemas/remote_players.py:124](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L124) · type `str`

```python
required / inherited validation
```

<a id="remote_players-androidpairstartrequest-host"></a>
### `remote_players.AndroidPairStartRequest.host`

[backend/app/schemas/remote_players.py:128](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L128) · type `str`

```python
Field(..., min_length=1, max_length=255)
```

<a id="remote_players-androidpairstartrequest-port"></a>
### `remote_players.AndroidPairStartRequest.port`

[backend/app/schemas/remote_players.py:129](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L129) · type `int`

```python
Field(8443, ge=1, le=65535)
```

<a id="remote_players-androidpairstartresponse-challenge"></a>
### `remote_players.AndroidPairStartResponse.challenge`

[backend/app/schemas/remote_players.py:133](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L133) · type `str`

```python
required / inherited validation
```

<a id="remote_players-androidpairstartresponse-fingerprint"></a>
### `remote_players.AndroidPairStartResponse.fingerprint`

[backend/app/schemas/remote_players.py:134](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L134) · type `str`

```python
required / inherited validation
```

<a id="remote_players-androidpairfinishrequest-challenge"></a>
### `remote_players.AndroidPairFinishRequest.challenge`

[backend/app/schemas/remote_players.py:138](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L138) · type `str`

```python
Field(..., min_length=1, max_length=256)
```

<a id="remote_players-androidpairfinishrequest-fingerprint"></a>
### `remote_players.AndroidPairFinishRequest.fingerprint`

[backend/app/schemas/remote_players.py:139](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L139) · type `str`

```python
Field(..., pattern='^[0-9a-f]{64}$')
```

<a id="remote_players-androidpairfinishrequest-code"></a>
### `remote_players.AndroidPairFinishRequest.code`

[backend/app/schemas/remote_players.py:140](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L140) · type `str`

```python
Field(..., pattern='^[0-9]{6}$')
```

<a id="remote_players-androidpairfinishresponse-password"></a>
### `remote_players.AndroidPairFinishResponse.password`

[backend/app/schemas/remote_players.py:144](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/remote_players.py#L144) · type `str`

```python
Field(..., description='New paired credential; submit with player create/update. Never returned for saved players.')
```

<a id="saved_searches-savedsearchinput-name"></a>
### `saved_searches.SavedSearchInput.name`

[backend/app/schemas/saved_searches.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L10) · type `str`

```python
Field(min_length=1, max_length=100)
```

<a id="saved_searches-savedsearchinput-query"></a>
### `saved_searches.SavedSearchInput.query`

[backend/app/schemas/saved_searches.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L11) · type `str`

```python
Field(min_length=1, max_length=256)
```

<a id="saved_searches-savedsearchinput-category"></a>
### `saved_searches.SavedSearchInput.category`

[backend/app/schemas/saved_searches.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L12) · type `str`

```python
Field(default='', max_length=100)
```

<a id="saved_searches-savedsearchinput-refresh_enabled"></a>
### `saved_searches.SavedSearchInput.refresh_enabled`

[backend/app/schemas/saved_searches.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L13) · type `bool`

```python
False
```

<a id="saved_searches-savedsearchupdate-expected_revision"></a>
### `saved_searches.SavedSearchUpdate.expected_revision`

[backend/app/schemas/saved_searches.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L27) · type `int`

```python
Field(ge=1)
```

<a id="saved_searches-savedsearchrunrequest-expected_revision"></a>
### `saved_searches.SavedSearchRunRequest.expected_revision`

[backend/app/schemas/saved_searches.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L31) · type `int`

```python
Field(ge=1)
```

<a id="saved_searches-savedsearchrunrequest-preview_token"></a>
### `saved_searches.SavedSearchRunRequest.preview_token`

[backend/app/schemas/saved_searches.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L32) · type `str | None`

```python
Field(default=None, max_length=100)
```

<a id="saved_searches-savedsearchresult-schema_version"></a>
### `saved_searches.SavedSearchResult.schema_version`

[backend/app/schemas/saved_searches.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L39) · type `int`

```python
1
```

<a id="saved_searches-savedsearchresult-outcome"></a>
### `saved_searches.SavedSearchResult.outcome`

[backend/app/schemas/saved_searches.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L40) · type `Outcome`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchresult-stop_reason"></a>
### `saved_searches.SavedSearchResult.stop_reason`

[backend/app/schemas/saved_searches.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L41) · type `str | None`

```python
None
```

<a id="saved_searches-savedsearchresult-pages_fetched"></a>
### `saved_searches.SavedSearchResult.pages_fetched`

[backend/app/schemas/saved_searches.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L42) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-candidates_seen"></a>
### `saved_searches.SavedSearchResult.candidates_seen`

[backend/app/schemas/saved_searches.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L43) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-unique_infohashes"></a>
### `saved_searches.SavedSearchResult.unique_infohashes`

[backend/app/schemas/saved_searches.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L44) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-resolved_content_ids"></a>
### `saved_searches.SavedSearchResult.resolved_content_ids`

[backend/app/schemas/saved_searches.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L45) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-added"></a>
### `saved_searches.SavedSearchResult.added`

[backend/app/schemas/saved_searches.py:46](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L46) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-existing"></a>
### `saved_searches.SavedSearchResult.existing`

[backend/app/schemas/saved_searches.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L47) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-excluded_candidates"></a>
### `saved_searches.SavedSearchResult.excluded_candidates`

[backend/app/schemas/saved_searches.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L48) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-unresolved_candidates"></a>
### `saved_searches.SavedSearchResult.unresolved_candidates`

[backend/app/schemas/saved_searches.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L49) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-duplicates"></a>
### `saved_searches.SavedSearchResult.duplicates`

[backend/app/schemas/saved_searches.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L50) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-deferred_candidates"></a>
### `saved_searches.SavedSearchResult.deferred_candidates`

[backend/app/schemas/saved_searches.py:51](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L51) · type `int`

```python
0
```

<a id="saved_searches-savedsearchresult-duration_seconds"></a>
### `saved_searches.SavedSearchResult.duration_seconds`

[backend/app/schemas/saved_searches.py:52](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L52) · type `float`

```python
0
```

<a id="saved_searches-savedsearchresult-policy_revision"></a>
### `saved_searches.SavedSearchResult.policy_revision`

[backend/app/schemas/saved_searches.py:53](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L53) · type `int`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchresult-definition_revision"></a>
### `saved_searches.SavedSearchResult.definition_revision`

[backend/app/schemas/saved_searches.py:54](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L54) · type `int`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchresult-started_at"></a>
### `saved_searches.SavedSearchResult.started_at`

[backend/app/schemas/saved_searches.py:55](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L55) · type `datetime`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchresult-finished_at"></a>
### `saved_searches.SavedSearchResult.finished_at`

[backend/app/schemas/saved_searches.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L56) · type `datetime`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchresult-samples"></a>
### `saved_searches.SavedSearchResult.samples`

[backend/app/schemas/saved_searches.py:57](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L57) · type `list[SearchImportOutcome]`

```python
Field(default_factory=list, max_length=100)
```

<a id="saved_searches-savedsearchresult-samples_truncated"></a>
### `saved_searches.SavedSearchResult.samples_truncated`

[backend/app/schemas/saved_searches.py:58](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L58) · type `bool`

```python
False
```

<a id="saved_searches-savedsearchview-id"></a>
### `saved_searches.SavedSearchView.id`

[backend/app/schemas/saved_searches.py:63](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L63) · type `int`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchview-revision"></a>
### `saved_searches.SavedSearchView.revision`

[backend/app/schemas/saved_searches.py:64](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L64) · type `int`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchview-created_at"></a>
### `saved_searches.SavedSearchView.created_at`

[backend/app/schemas/saved_searches.py:65](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L65) · type `datetime`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchview-updated_at"></a>
### `saved_searches.SavedSearchView.updated_at`

[backend/app/schemas/saved_searches.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L66) · type `datetime`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchview-last_attempt_at"></a>
### `saved_searches.SavedSearchView.last_attempt_at`

[backend/app/schemas/saved_searches.py:67](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L67) · type `datetime | None`

```python
None
```

<a id="saved_searches-savedsearchview-last_started_at"></a>
### `saved_searches.SavedSearchView.last_started_at`

[backend/app/schemas/saved_searches.py:68](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L68) · type `datetime | None`

```python
None
```

<a id="saved_searches-savedsearchview-last_finished_at"></a>
### `saved_searches.SavedSearchView.last_finished_at`

[backend/app/schemas/saved_searches.py:69](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L69) · type `datetime | None`

```python
None
```

<a id="saved_searches-savedsearchview-last_success_at"></a>
### `saved_searches.SavedSearchView.last_success_at`

[backend/app/schemas/saved_searches.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L70) · type `datetime | None`

```python
None
```

<a id="saved_searches-savedsearchview-last_outcome"></a>
### `saved_searches.SavedSearchView.last_outcome`

[backend/app/schemas/saved_searches.py:71](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L71) · type `Outcome | None`

```python
None
```

<a id="saved_searches-savedsearchview-last_result"></a>
### `saved_searches.SavedSearchView.last_result`

[backend/app/schemas/saved_searches.py:72](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L72) · type `SavedSearchResult | None`

```python
None
```

<a id="saved_searches-savedsearchview-error_code"></a>
### `saved_searches.SavedSearchView.error_code`

[backend/app/schemas/saved_searches.py:73](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L73) · type `str | None`

```python
None
```

<a id="saved_searches-savedsearchview-error_message"></a>
### `saved_searches.SavedSearchView.error_message`

[backend/app/schemas/saved_searches.py:74](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L74) · type `str | None`

```python
None
```

<a id="saved_searches-savedsearchview-run_id"></a>
### `saved_searches.SavedSearchView.run_id`

[backend/app/schemas/saved_searches.py:75](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L75) · type `str | None`

```python
None
```

<a id="saved_searches-savedsearchview-run_state"></a>
### `saved_searches.SavedSearchView.run_state`

[backend/app/schemas/saved_searches.py:76](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L76) · type `Literal['waiting', 'running'] | None`

```python
None
```

<a id="saved_searches-savedsearchlist-items"></a>
### `saved_searches.SavedSearchList.items`

[backend/app/schemas/saved_searches.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L80) · type `list[SavedSearchView]`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchlist-total"></a>
### `saved_searches.SavedSearchList.total`

[backend/app/schemas/saved_searches.py:81](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L81) · type `int`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchpreviewrequest-definition"></a>
### `saved_searches.SavedSearchPreviewRequest.definition`

[backend/app/schemas/saved_searches.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L85) · type `SavedSearchInput | None`

```python
None
```

<a id="saved_searches-savedsearchpreviewrequest-saved_search_id"></a>
### `saved_searches.SavedSearchPreviewRequest.saved_search_id`

[backend/app/schemas/saved_searches.py:86](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L86) · type `int | None`

```python
Field(default=None, ge=1)
```

<a id="saved_searches-savedsearchpreviewrequest-expected_revision"></a>
### `saved_searches.SavedSearchPreviewRequest.expected_revision`

[backend/app/schemas/saved_searches.py:87](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L87) · type `int | None`

```python
Field(default=None, ge=1)
```

<a id="saved_searches-savedsearchpreview-preview_token"></a>
### `saved_searches.SavedSearchPreview.preview_token`

[backend/app/schemas/saved_searches.py:99](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L99) · type `str`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchpreview-result"></a>
### `saved_searches.SavedSearchPreview.result`

[backend/app/schemas/saved_searches.py:100](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L100) · type `SavedSearchResult`

```python
required / inherited validation
```

<a id="saved_searches-savedsearchpreview-expires_in_seconds"></a>
### `saved_searches.SavedSearchPreview.expires_in_seconds`

[backend/app/schemas/saved_searches.py:101](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/saved_searches.py#L101) · type `int`

```python
300
```

<a id="scraper-scraperrequest-url"></a>
### `scraper.ScraperRequest.url`

[backend/app/schemas/scraper.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L12) · type `str`

```python
required / inherited validation
```

<a id="scraper-scraperrequest-url_type"></a>
### `scraper.ScraperRequest.url_type`

[backend/app/schemas/scraper.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L13) · type `str`

```python
'auto'
```

<a id="scraper-scraperrequest-run_async"></a>
### `scraper.ScraperRequest.run_async`

[backend/app/schemas/scraper.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L14) · type `bool`

```python
False
```

<a id="scraper-channelresult-channel_id"></a>
### `scraper.ChannelResult.channel_id`

[backend/app/schemas/scraper.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L19) · type `str`

```python
required / inherited validation
```

<a id="scraper-channelresult-name"></a>
### `scraper.ChannelResult.name`

[backend/app/schemas/scraper.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L20) · type `str`

```python
required / inherited validation
```

<a id="scraper-channelresult-metadata"></a>
### `scraper.ChannelResult.metadata`

[backend/app/schemas/scraper.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L21) · type `Dict[str, Any]`

```python
{}
```

<a id="scraper-scraperresult-excluded_count"></a>
### `scraper.ScraperResult.excluded_count`

[backend/app/schemas/scraper.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L25) · type `int`

```python
0
```

<a id="scraper-scraperresult-message"></a>
### `scraper.ScraperResult.message`

[backend/app/schemas/scraper.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L27) · type `str`

```python
required / inherited validation
```

<a id="scraper-scraperresult-channels"></a>
### `scraper.ScraperResult.channels`

[backend/app/schemas/scraper.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L28) · type `List[ChannelResult]`

```python
required / inherited validation
```

<a id="scraper-scraperresult-url"></a>
### `scraper.ScraperResult.url`

[backend/app/schemas/scraper.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L29) · type `str`

```python
required / inherited validation
```

<a id="scraper-sourcename-name"></a>
### `scraper.SourceName.name`

[backend/app/schemas/scraper.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L33) · type `Optional[str]`

```python
Field(None, max_length=255)
```

<a id="scraper-builtinprovider-id"></a>
### `scraper.BuiltinProvider.id`

[backend/app/schemas/scraper.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L42) · type `str`

```python
required / inherited validation
```

<a id="scraper-builtinprovider-name"></a>
### `scraper.BuiltinProvider.name`

[backend/app/schemas/scraper.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L43) · type `str`

```python
required / inherited validation
```

<a id="scraper-builtinprovider-url"></a>
### `scraper.BuiltinProvider.url`

[backend/app/schemas/scraper.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L44) · type `str`

```python
required / inherited validation
```

<a id="scraper-urlresponse-id"></a>
### `scraper.URLResponse.id`

[backend/app/schemas/scraper.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L49) · type `int`

```python
required / inherited validation
```

<a id="scraper-urlresponse-url"></a>
### `scraper.URLResponse.url`

[backend/app/schemas/scraper.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L50) · type `str`

```python
required / inherited validation
```

<a id="scraper-urlresponse-url_type"></a>
### `scraper.URLResponse.url_type`

[backend/app/schemas/scraper.py:51](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L51) · type `str`

```python
required / inherited validation
```

<a id="scraper-urlresponse-status"></a>
### `scraper.URLResponse.status`

[backend/app/schemas/scraper.py:52](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L52) · type `str`

```python
required / inherited validation
```

<a id="scraper-urlresponse-last_processed"></a>
### `scraper.URLResponse.last_processed`

[backend/app/schemas/scraper.py:53](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L53) · type `Optional[datetime]`

```python
None
```

<a id="scraper-urlresponse-last_scraped"></a>
### `scraper.URLResponse.last_scraped`

[backend/app/schemas/scraper.py:54](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L54) · type `Optional[datetime]`

```python
None
```

<a id="scraper-urlresponse-error_count"></a>
### `scraper.URLResponse.error_count`

[backend/app/schemas/scraper.py:55](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L55) · type `int`

```python
0
```

<a id="scraper-urlresponse-last_error"></a>
### `scraper.URLResponse.last_error`

[backend/app/schemas/scraper.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L56) · type `Optional[str]`

```python
None
```

<a id="scraper-urlresponse-error"></a>
### `scraper.URLResponse.error`

[backend/app/schemas/scraper.py:57](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L57) · type `Optional[str]`

```python
None
```

<a id="scraper-urlresponse-enabled"></a>
### `scraper.URLResponse.enabled`

[backend/app/schemas/scraper.py:58](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L58) · type `bool`

```python
True
```

<a id="scraper-urlresponse-extraction_recipe"></a>
### `scraper.URLResponse.extraction_recipe`

[backend/app/schemas/scraper.py:59](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L59) · type `Optional[ExtractionRecipe]`

```python
None
```

<a id="scraper-urlresponse-scrape_bare_ids"></a>
### `scraper.URLResponse.scrape_bare_ids`

[backend/app/schemas/scraper.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L60) · type `bool`

```python
False
```

<a id="scraper-urlresponse-added_at"></a>
### `scraper.URLResponse.added_at`

[backend/app/schemas/scraper.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L61) · type `datetime`

```python
required / inherited validation
```

<a id="scraper-urlresponse-channels_found"></a>
### `scraper.URLResponse.channels_found`

[backend/app/schemas/scraper.py:64](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L64) · type `int`

```python
0
```

<a id="scraper-urlresponse-assigned_count"></a>
### `scraper.URLResponse.assigned_count`

[backend/app/schemas/scraper.py:65](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L65) · type `int`

```python
0
```

<a id="scraper-urldeleteresult-deleted_streams"></a>
### `scraper.URLDeleteResult.deleted_streams`

[backend/app/schemas/scraper.py:79](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L79) · type `int`

```python
0
```

<a id="scraper-orphanedsource-source_url"></a>
### `scraper.OrphanedSource.source_url`

[backend/app/schemas/scraper.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L84) · type `str`

```python
required / inherited validation
```

<a id="scraper-orphanedsource-count"></a>
### `scraper.OrphanedSource.count`

[backend/app/schemas/scraper.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L85) · type `int`

```python
required / inherited validation
```

<a id="scraper-orphanedsource-assigned_count"></a>
### `scraper.OrphanedSource.assigned_count`

[backend/app/schemas/scraper.py:86](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L86) · type `int`

```python
required / inherited validation
```

<a id="scraper-orphancleanuprequest-source_urls"></a>
### `scraper.OrphanCleanupRequest.source_urls`

[backend/app/schemas/scraper.py:90](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L90) · type `List[str]`

```python
Field(min_length=1, max_length=200)
```

<a id="scraper-orphancleanupresult-deleted"></a>
### `scraper.OrphanCleanupResult.deleted`

[backend/app/schemas/scraper.py:94](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L94) · type `Dict[str, int]`

```python
required / inherited validation
```

<a id="scraper-urlcreate-url"></a>
### `scraper.URLCreate.url`

[backend/app/schemas/scraper.py:99](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L99) · type `str`

```python
required / inherited validation
```

<a id="scraper-urlcreate-url_type"></a>
### `scraper.URLCreate.url_type`

[backend/app/schemas/scraper.py:100](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L100) · type `str`

```python
'regular'
```

<a id="scraper-urlcreate-enabled"></a>
### `scraper.URLCreate.enabled`

[backend/app/schemas/scraper.py:101](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L101) · type `bool`

```python
True
```

<a id="scraper-urlcreate-status"></a>
### `scraper.URLCreate.status`

[backend/app/schemas/scraper.py:102](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L102) · type `str`

```python
'active'
```

<a id="scraper-urlcreate-extraction_recipe"></a>
### `scraper.URLCreate.extraction_recipe`

[backend/app/schemas/scraper.py:103](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L103) · type `Optional[ExtractionRecipe]`

```python
None
```

<a id="scraper-urlcreate-scrape_bare_ids"></a>
### `scraper.URLCreate.scrape_bare_ids`

[backend/app/schemas/scraper.py:104](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L104) · type `bool`

```python
False
```

<a id="scraper-urlupdate-url"></a>
### `scraper.URLUpdate.url`

[backend/app/schemas/scraper.py:109](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L109) · type `Optional[str]`

```python
None
```

<a id="scraper-urlupdate-url_type"></a>
### `scraper.URLUpdate.url_type`

[backend/app/schemas/scraper.py:110](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L110) · type `Optional[str]`

```python
None
```

<a id="scraper-urlupdate-enabled"></a>
### `scraper.URLUpdate.enabled`

[backend/app/schemas/scraper.py:111](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L111) · type `Optional[bool]`

```python
None
```

<a id="scraper-urlupdate-status"></a>
### `scraper.URLUpdate.status`

[backend/app/schemas/scraper.py:112](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L112) · type `Optional[str]`

```python
None
```

<a id="scraper-urlupdate-extraction_recipe"></a>
### `scraper.URLUpdate.extraction_recipe`

[backend/app/schemas/scraper.py:113](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L113) · type `Optional[ExtractionRecipe]`

```python
None
```

<a id="scraper-urlupdate-scrape_bare_ids"></a>
### `scraper.URLUpdate.scrape_bare_ids`

[backend/app/schemas/scraper.py:114](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/scraper.py#L114) · type `Optional[bool]`

```python
None
```

<a id="search-searchresultitem-id"></a>
### `search.SearchResultItem.id`

[backend/app/schemas/search.py:5](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L5) · type `str`

```python
Field(..., description='Acestream channel ID (infohash)')
```

<a id="search-searchresultitem-name"></a>
### `search.SearchResultItem.name`

[backend/app/schemas/search.py:6](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L6) · type `str`

```python
Field(..., min_length=1, max_length=512, description='Channel name')
```

<a id="search-searchresultitem-bitrate"></a>
### `search.SearchResultItem.bitrate`

[backend/app/schemas/search.py:7](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L7) · type `Optional[int]`

```python
Field(None, description='Channel bitrate')
```

<a id="search-searchresultitem-categories"></a>
### `search.SearchResultItem.categories`

[backend/app/schemas/search.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L8) · type `List[str]`

```python
Field(default_factory=list, description='Categories of the channel')
```

<a id="search-searchresultitem-status"></a>
### `search.SearchResultItem.status`

[backend/app/schemas/search.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L9) · type `Optional[int]`

```python
Field(None, description='Catalogue status: 2 available, 1 uncertain; not a live probe')
```

<a id="search-searchresultitem-availability"></a>
### `search.SearchResultItem.availability`

[backend/app/schemas/search.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L10) · type `Optional[float]`

```python
Field(None, description='Catalogue availability score')
```

<a id="search-searchresultitem-availability_updated_at"></a>
### `search.SearchResultItem.availability_updated_at`

[backend/app/schemas/search.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L11) · type `Optional[int]`

```python
Field(None, description='Unix timestamp of the catalogue availability update')
```

<a id="search-searchpagination-page"></a>
### `search.SearchPagination.page`

[backend/app/schemas/search.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L31) · type `int`

```python
Field(..., description='Current page number')
```

<a id="search-searchpagination-page_size"></a>
### `search.SearchPagination.page_size`

[backend/app/schemas/search.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L32) · type `int`

```python
Field(..., description='Results per page')
```

<a id="search-searchpagination-total_results"></a>
### `search.SearchPagination.total_results`

[backend/app/schemas/search.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L33) · type `int`

```python
Field(..., description='Total number of results')
```

<a id="search-searchpagination-total_pages"></a>
### `search.SearchPagination.total_pages`

[backend/app/schemas/search.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L34) · type `int`

```python
Field(..., description='Total number of pages')
```

<a id="search-resolvedsearchresult-content_id"></a>
### `search.ResolvedSearchResult.content_id`

[backend/app/schemas/search.py:38](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L38) · type `str`

```python
Field(..., pattern='^[0-9a-f]{40}$', description='Resolved transport-file content ID for saving or playback')
```

<a id="search-searchresponse-success"></a>
### `search.SearchResponse.success`

[backend/app/schemas/search.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L41) · type `bool`

```python
Field(..., description='Success status of the request')
```

<a id="search-searchresponse-message"></a>
### `search.SearchResponse.message`

[backend/app/schemas/search.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L42) · type `str`

```python
Field(..., description='Message describing the result')
```

<a id="search-searchresponse-results"></a>
### `search.SearchResponse.results`

[backend/app/schemas/search.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L43) · type `List[SearchResultItem]`

```python
Field(default_factory=list, description='Search results')
```

<a id="search-searchresponse-pagination"></a>
### `search.SearchResponse.pagination`

[backend/app/schemas/search.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L44) · type `SearchPagination`

```python
Field(..., description='Pagination information')
```

<a id="search-addchannelrequest-id"></a>
### `search.AddChannelRequest.id`

[backend/app/schemas/search.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L47) · type `str`

```python
Field(pattern='^[0-9a-fA-F]{40}$', description='Catalogue infohash; resolved by the server before import')
```

<a id="search-addchannelrequest-name"></a>
### `search.AddChannelRequest.name`

[backend/app/schemas/search.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L48) · type `str`

```python
Field(..., min_length=1, max_length=512, description='Channel name')
```

<a id="search-addchannelrequest-url"></a>
### `search.AddChannelRequest.url`

[backend/app/schemas/search.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L49) · type `str`

```python
Field(..., description='Channel URL')
```

<a id="search-addchannelrequest-category"></a>
### `search.AddChannelRequest.category`

[backend/app/schemas/search.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L50) · type `Optional[str]`

```python
Field(None, description='Channel category')
```

<a id="search-addchannelrequest-description"></a>
### `search.AddChannelRequest.description`

[backend/app/schemas/search.py:51](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L51) · type `Optional[str]`

```python
Field(None, description='Channel description')
```

<a id="search-addchannelrequest-logo"></a>
### `search.AddChannelRequest.logo`

[backend/app/schemas/search.py:52](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L52) · type `Optional[str]`

```python
Field(None, description='Channel logo URL')
```

<a id="search-addchannelrequest-tv_channel_id"></a>
### `search.AddChannelRequest.tv_channel_id`

[backend/app/schemas/search.py:53](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L53) · type `Optional[int]`

```python
Field(None, description='TV channel ID for association')
```

<a id="search-addmultiplerequest-channels"></a>
### `search.AddMultipleRequest.channels`

[backend/app/schemas/search.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L56) · type `List[AddChannelRequest]`

```python
Field(..., min_length=1, max_length=100, description='Catalogue results to resolve and import')
```

<a id="search-searchimportitem-infohash"></a>
### `search.SearchImportItem.infohash`

[backend/app/schemas/search.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L60) · type `str`

```python
Field(pattern='^[a-fA-F0-9]{40}$')
```

<a id="search-searchimportitem-name"></a>
### `search.SearchImportItem.name`

[backend/app/schemas/search.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L61) · type `str`

```python
Field(min_length=1, max_length=512)
```

<a id="search-searchimportitem-category"></a>
### `search.SearchImportItem.category`

[backend/app/schemas/search.py:62](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L62) · type `str`

```python
Field(default='', max_length=100)
```

<a id="search-searchimportrequest-items"></a>
### `search.SearchImportRequest.items`

[backend/app/schemas/search.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L66) · type `list[SearchImportItem]`

```python
Field(min_length=1, max_length=100)
```

<a id="search-searchimportrequest-tv_channel_id"></a>
### `search.SearchImportRequest.tv_channel_id`

[backend/app/schemas/search.py:67](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L67) · type `Optional[int]`

```python
Field(None, gt=0, description='Explicit Add and Link target; existing assignments are preserved.')
```

<a id="search-searchimportoutcome-infohash"></a>
### `search.SearchImportOutcome.infohash`

[backend/app/schemas/search.py:74](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L74) · type `str`

```python
required / inherited validation
```

<a id="search-searchimportoutcome-content_id"></a>
### `search.SearchImportOutcome.content_id`

[backend/app/schemas/search.py:75](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L75) · type `str | None`

```python
None
```

<a id="search-searchimportoutcome-outcome"></a>
### `search.SearchImportOutcome.outcome`

[backend/app/schemas/search.py:76](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L76) · type `Literal['added', 'existing', 'excluded', 'unresolved', 'duplicate', 'deferred']`

```python
required / inherited validation
```

<a id="search-searchimportoutcome-rule_ids"></a>
### `search.SearchImportOutcome.rule_ids`

[backend/app/schemas/search.py:77](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L77) · type `list[int]`

```python
Field(default_factory=list)
```

<a id="search-searchimportresponse-items"></a>
### `search.SearchImportResponse.items`

[backend/app/schemas/search.py:81](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L81) · type `list[SearchImportOutcome]`

```python
required / inherited validation
```

<a id="search-searchimportresponse-policy_revision"></a>
### `search.SearchImportResponse.policy_revision`

[backend/app/schemas/search.py:82](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L82) · type `int`

```python
required / inherited validation
```

<a id="search-searchimportresponse-added"></a>
### `search.SearchImportResponse.added`

[backend/app/schemas/search.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L83) · type `int`

```python
0
```

<a id="search-searchimportresponse-existing"></a>
### `search.SearchImportResponse.existing`

[backend/app/schemas/search.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L84) · type `int`

```python
0
```

<a id="search-searchimportresponse-excluded"></a>
### `search.SearchImportResponse.excluded`

[backend/app/schemas/search.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L85) · type `int`

```python
0
```

<a id="search-searchimportresponse-unresolved"></a>
### `search.SearchImportResponse.unresolved`

[backend/app/schemas/search.py:86](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L86) · type `int`

```python
0
```

<a id="search-searchimportresponse-deferred"></a>
### `search.SearchImportResponse.deferred`

[backend/app/schemas/search.py:87](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/search.py#L87) · type `int`

```python
0
```

<a id="setup-runtimeoption-name"></a>
### `setup.RuntimeOption.name`

[backend/app/schemas/setup.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L9) · type `str`

```python
required / inherited validation
```

<a id="setup-runtimeoption-group"></a>
### `setup.RuntimeOption.group`

[backend/app/schemas/setup.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L10) · type `str`

```python
required / inherited validation
```

<a id="setup-runtimeoption-label"></a>
### `setup.RuntimeOption.label`

[backend/app/schemas/setup.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L11) · type `str`

```python
required / inherited validation
```

<a id="setup-runtimeoption-kind"></a>
### `setup.RuntimeOption.kind`

[backend/app/schemas/setup.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L12) · type `str`

```python
required / inherited validation
```

<a id="setup-runtimeoption-default"></a>
### `setup.RuntimeOption.default`

[backend/app/schemas/setup.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L13) · type `RuntimeValue`

```python
required / inherited validation
```

<a id="setup-runtimeoption-help"></a>
### `setup.RuntimeOption.help`

[backend/app/schemas/setup.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L14) · type `str`

```python
required / inherited validation
```

<a id="setup-runtimeoption-minimum"></a>
### `setup.RuntimeOption.minimum`

[backend/app/schemas/setup.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L15) · type `float | None`

```python
None
```

<a id="setup-runtimeoption-maximum"></a>
### `setup.RuntimeOption.maximum`

[backend/app/schemas/setup.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L16) · type `float | None`

```python
None
```

<a id="setup-setupstate-version"></a>
### `setup.SetupState.version`

[backend/app/schemas/setup.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L20) · type `Literal[1]`

```python
1
```

<a id="setup-setupstate-setup_complete"></a>
### `setup.SetupState.setup_complete`

[backend/app/schemas/setup.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L21) · type `bool`

```python
required / inherited validation
```

<a id="setup-setupstate-revision"></a>
### `setup.SetupState.revision`

[backend/app/schemas/setup.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L22) · type `str`

```python
required / inherited validation
```

<a id="setup-setupstate-runtime"></a>
### `setup.SetupState.runtime`

[backend/app/schemas/setup.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L23) · type `dict[str, RuntimeValue]`

```python
required / inherited validation
```

<a id="setup-setupstate-options"></a>
### `setup.SetupState.options`

[backend/app/schemas/setup.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L24) · type `list[RuntimeOption]`

```python
required / inherited validation
```

<a id="setup-setupstate-unavailable"></a>
### `setup.SetupState.unavailable`

[backend/app/schemas/setup.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L25) · type `dict[str, str]`

```python
required / inherited validation
```

<a id="setup-setupstate-restart_required"></a>
### `setup.SetupState.restart_required`

[backend/app/schemas/setup.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L26) · type `bool`

```python
required / inherited validation
```

<a id="setup-setupstate-api_protected"></a>
### `setup.SetupState.api_protected`

[backend/app/schemas/setup.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L27) · type `bool`

```python
required / inherited validation
```

<a id="setup-setupstate-resolved_runtime"></a>
### `setup.SetupState.resolved_runtime`

[backend/app/schemas/setup.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L28) · type `dict[str, RuntimeValue]`

```python
Field(default_factory=dict)
```

<a id="setup-setupstate-saved_overrides"></a>
### `setup.SetupState.saved_overrides`

[backend/app/schemas/setup.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L29) · type `dict[str, str]`

```python
Field(default_factory=dict)
```

<a id="setup-setupstate-recordings_configured"></a>
### `setup.SetupState.recordings_configured`

[backend/app/schemas/setup.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L30) · type `bool`

```python
False
```

<a id="setup-setupupdate-expected_revision"></a>
### `setup.SetupUpdate.expected_revision`

[backend/app/schemas/setup.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L35) · type `str`

```python
Field(min_length=64, max_length=64)
```

<a id="setup-setupupdate-runtime"></a>
### `setup.SetupUpdate.runtime`

[backend/app/schemas/setup.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L36) · type `dict[str, RuntimeValue]`

```python
Field(max_length=100)
```

<a id="setup-setupupdate-setup_complete"></a>
### `setup.SetupUpdate.setup_complete`

[backend/app/schemas/setup.py:37](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/setup.py#L37) · type `bool`

```python
True
```

<a id="startup-startupevent-time"></a>
### `startup.StartupEvent.time`

[backend/app/schemas/startup.py:7](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L7) · type `str`

```python
required / inherited validation
```

<a id="startup-startupevent-message"></a>
### `startup.StartupEvent.message`

[backend/app/schemas/startup.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L8) · type `str`

```python
required / inherited validation
```

<a id="startup-startupevent-level"></a>
### `startup.StartupEvent.level`

[backend/app/schemas/startup.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L9) · type `Literal['info', 'warning', 'error']`

```python
'info'
```

<a id="startup-migrationprogress-status"></a>
### `startup.MigrationProgress.status`

[backend/app/schemas/startup.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L13) · type `str`

```python
required / inherited validation
```

<a id="startup-migrationprogress-total"></a>
### `startup.MigrationProgress.total`

[backend/app/schemas/startup.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L14) · type `int`

```python
0
```

<a id="startup-migrationprogress-processed"></a>
### `startup.MigrationProgress.processed`

[backend/app/schemas/startup.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L15) · type `int`

```python
0
```

<a id="startup-migrationprogress-migrated"></a>
### `startup.MigrationProgress.migrated`

[backend/app/schemas/startup.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L16) · type `int`

```python
0
```

<a id="startup-migrationprogress-skipped"></a>
### `startup.MigrationProgress.skipped`

[backend/app/schemas/startup.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L17) · type `int`

```python
0
```

<a id="startup-migrationprogress-stale"></a>
### `startup.MigrationProgress.stale`

[backend/app/schemas/startup.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L18) · type `int`

```python
0
```

<a id="startup-migrationprogress-percent"></a>
### `startup.MigrationProgress.percent`

[backend/app/schemas/startup.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L19) · type `float`

```python
0
```

<a id="startup-startupstatus-status"></a>
### `startup.StartupStatus.status`

[backend/app/schemas/startup.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L23) · type `Literal['starting', 'ready', 'failed']`

```python
required / inherited validation
```

<a id="startup-startupstatus-phase"></a>
### `startup.StartupStatus.phase`

[backend/app/schemas/startup.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L24) · type `str`

```python
required / inherited validation
```

<a id="startup-startupstatus-events"></a>
### `startup.StartupStatus.events`

[backend/app/schemas/startup.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L25) · type `list[StartupEvent]`

```python
required / inherited validation
```

<a id="startup-startupstatus-migration"></a>
### `startup.StartupStatus.migration`

[backend/app/schemas/startup.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L26) · type `MigrationProgress | None`

```python
None
```

<a id="startup-startupstatus-recovery_available"></a>
### `startup.StartupStatus.recovery_available`

[backend/app/schemas/startup.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L27) · type `bool`

```python
False
```

<a id="startup-startupstatus-recovery_token"></a>
### `startup.StartupStatus.recovery_token`

[backend/app/schemas/startup.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L28) · type `str`

```python
required / inherited validation
```

<a id="startup-startupstatus-guidance"></a>
### `startup.StartupStatus.guidance`

[backend/app/schemas/startup.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L29) · type `str | None`

```python
None
```

<a id="startup-startuprecoveryrequest-action"></a>
### `startup.StartupRecoveryRequest.action`

[backend/app/schemas/startup.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L33) · type `Literal['retry', 'salvage', 'fresh']`

```python
required / inherited validation
```

<a id="startup-startuprecoveryrequest-recovery_token"></a>
### `startup.StartupRecoveryRequest.recovery_token`

[backend/app/schemas/startup.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L34) · type `str`

```python
required / inherited validation
```

<a id="startup-startuprecoveryrequest-confirm"></a>
### `startup.StartupRecoveryRequest.confirm`

[backend/app/schemas/startup.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/startup.py#L35) · type `bool`

```python
False
```

<a id="stats_schemas-urlstats-id"></a>
### `stats_schemas.URLStats.id`

[backend/app/schemas/stats_schemas.py:5](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L5) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-urlstats-url"></a>
### `stats_schemas.URLStats.url`

[backend/app/schemas/stats_schemas.py:6](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L6) · type `str`

```python
required / inherited validation
```

<a id="stats_schemas-urlstats-url_type"></a>
### `stats_schemas.URLStats.url_type`

[backend/app/schemas/stats_schemas.py:7](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L7) · type `str`

```python
required / inherited validation
```

<a id="stats_schemas-urlstats-status"></a>
### `stats_schemas.URLStats.status`

[backend/app/schemas/stats_schemas.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L8) · type `str`

```python
required / inherited validation
```

<a id="stats_schemas-urlstats-last_processed"></a>
### `stats_schemas.URLStats.last_processed`

[backend/app/schemas/stats_schemas.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L9) · type `Optional[str]`

```python
None
```

<a id="stats_schemas-urlstats-channel_count"></a>
### `stats_schemas.URLStats.channel_count`

[backend/app/schemas/stats_schemas.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L10) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-urlstats-enabled"></a>
### `stats_schemas.URLStats.enabled`

[backend/app/schemas/stats_schemas.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L11) · type `bool`

```python
required / inherited validation
```

<a id="stats_schemas-urlstats-error_count"></a>
### `stats_schemas.URLStats.error_count`

[backend/app/schemas/stats_schemas.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L12) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-urlstats-last_error"></a>
### `stats_schemas.URLStats.last_error`

[backend/app/schemas/stats_schemas.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L13) · type `Optional[str]`

```python
None
```

<a id="stats_schemas-statsresponse-urls"></a>
### `stats_schemas.StatsResponse.urls`

[backend/app/schemas/stats_schemas.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L16) · type `List[URLStats]`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-total_channels"></a>
### `stats_schemas.StatsResponse.total_channels`

[backend/app/schemas/stats_schemas.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L17) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-channels"></a>
### `stats_schemas.StatsResponse.channels`

[backend/app/schemas/stats_schemas.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L18) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-channels_checked"></a>
### `stats_schemas.StatsResponse.channels_checked`

[backend/app/schemas/stats_schemas.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L19) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-channels_online"></a>
### `stats_schemas.StatsResponse.channels_online`

[backend/app/schemas/stats_schemas.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L20) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-channels_offline"></a>
### `stats_schemas.StatsResponse.channels_offline`

[backend/app/schemas/stats_schemas.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L21) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-base_url"></a>
### `stats_schemas.StatsResponse.base_url`

[backend/app/schemas/stats_schemas.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L22) · type `str`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-ace_engine_url"></a>
### `stats_schemas.StatsResponse.ace_engine_url`

[backend/app/schemas/stats_schemas.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L23) · type `str`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-rescrape_interval"></a>
### `stats_schemas.StatsResponse.rescrape_interval`

[backend/app/schemas/stats_schemas.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L24) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-addpid"></a>
### `stats_schemas.StatsResponse.addpid`

[backend/app/schemas/stats_schemas.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L25) · type `bool`

```python
required / inherited validation
```

<a id="stats_schemas-statsresponse-task_manager_status"></a>
### `stats_schemas.StatsResponse.task_manager_status`

[backend/app/schemas/stats_schemas.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L26) · type `str`

```python
required / inherited validation
```

<a id="stats_schemas-tvchannelstatsresponse-total"></a>
### `stats_schemas.TVChannelStatsResponse.total`

[backend/app/schemas/stats_schemas.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L29) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-tvchannelstatsresponse-active"></a>
### `stats_schemas.TVChannelStatsResponse.active`

[backend/app/schemas/stats_schemas.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L30) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-tvchannelstatsresponse-with_epg"></a>
### `stats_schemas.TVChannelStatsResponse.with_epg`

[backend/app/schemas/stats_schemas.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L31) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-tvchannelstatsresponse-acestreams"></a>
### `stats_schemas.TVChannelStatsResponse.acestreams`

[backend/app/schemas/stats_schemas.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L32) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthchanneltotals-total"></a>
### `stats_schemas.HealthChannelTotals.total`

[backend/app/schemas/stats_schemas.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L36) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthchanneltotals-online"></a>
### `stats_schemas.HealthChannelTotals.online`

[backend/app/schemas/stats_schemas.py:37](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L37) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthchanneltotals-offline"></a>
### `stats_schemas.HealthChannelTotals.offline`

[backend/app/schemas/stats_schemas.py:38](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L38) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthchanneltotals-unknown"></a>
### `stats_schemas.HealthChannelTotals.unknown`

[backend/app/schemas/stats_schemas.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L39) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthurltotals-total"></a>
### `stats_schemas.HealthURLTotals.total`

[backend/app/schemas/stats_schemas.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L43) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthurltotals-active"></a>
### `stats_schemas.HealthURLTotals.active`

[backend/app/schemas/stats_schemas.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L44) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthurltotals-error"></a>
### `stats_schemas.HealthURLTotals.error`

[backend/app/schemas/stats_schemas.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L45) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthepgtotals-sources"></a>
### `stats_schemas.HealthEPGTotals.sources`

[backend/app/schemas/stats_schemas.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L49) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthepgtotals-channels"></a>
### `stats_schemas.HealthEPGTotals.channels`

[backend/app/schemas/stats_schemas.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L50) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthepgtotals-programs"></a>
### `stats_schemas.HealthEPGTotals.programs`

[backend/app/schemas/stats_schemas.py:51](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L51) · type `int`

```python
required / inherited validation
```

<a id="stats_schemas-healthstatsresponse-channels"></a>
### `stats_schemas.HealthStatsResponse.channels`

[backend/app/schemas/stats_schemas.py:57](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L57) · type `HealthChannelTotals`

```python
required / inherited validation
```

<a id="stats_schemas-healthstatsresponse-urls"></a>
### `stats_schemas.HealthStatsResponse.urls`

[backend/app/schemas/stats_schemas.py:58](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L58) · type `HealthURLTotals`

```python
required / inherited validation
```

<a id="stats_schemas-healthstatsresponse-epg"></a>
### `stats_schemas.HealthStatsResponse.epg`

[backend/app/schemas/stats_schemas.py:59](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stats_schemas.py#L59) · type `HealthEPGTotals`

```python
required / inherited validation
```

<a id="storage-storagedirectory-path"></a>
### `storage.StorageDirectory.path`

[backend/app/schemas/storage.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L8) · type `str`

```python
required / inherited validation
```

<a id="storage-storagedirectory-mounted"></a>
### `storage.StorageDirectory.mounted`

[backend/app/schemas/storage.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L9) · type `bool | None`

```python
None
```

<a id="storage-storagedirectory-mount_point"></a>
### `storage.StorageDirectory.mount_point`

[backend/app/schemas/storage.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L10) · type `str | None`

```python
None
```

<a id="storage-storagedirectory-read_only"></a>
### `storage.StorageDirectory.read_only`

[backend/app/schemas/storage.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L11) · type `bool | None`

```python
None
```

<a id="storage-storagedirectory-directory_bytes"></a>
### `storage.StorageDirectory.directory_bytes`

[backend/app/schemas/storage.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L12) · type `int | None`

```python
None
```

<a id="storage-storagedirectory-size_complete"></a>
### `storage.StorageDirectory.size_complete`

[backend/app/schemas/storage.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L13) · type `bool`

```python
False
```

<a id="storage-storagedirectory-filesystem_total_bytes"></a>
### `storage.StorageDirectory.filesystem_total_bytes`

[backend/app/schemas/storage.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L14) · type `int | None`

```python
None
```

<a id="storage-storagedirectory-filesystem_free_bytes"></a>
### `storage.StorageDirectory.filesystem_free_bytes`

[backend/app/schemas/storage.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L15) · type `int | None`

```python
None
```

<a id="storage-storagedirectory-message"></a>
### `storage.StorageDirectory.message`

[backend/app/schemas/storage.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L16) · type `str`

```python
''
```

<a id="storage-configurationwarning-legacy"></a>
### `storage.ConfigurationWarning.legacy`

[backend/app/schemas/storage.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L20) · type `str`

```python
required / inherited validation
```

<a id="storage-configurationwarning-replacement"></a>
### `storage.ConfigurationWarning.replacement`

[backend/app/schemas/storage.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L21) · type `str`

```python
required / inherited validation
```

<a id="storage-configurationwarning-selected"></a>
### `storage.ConfigurationWarning.selected`

[backend/app/schemas/storage.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L22) · type `str`

```python
required / inherited validation
```

<a id="storage-storagereport-checked_at"></a>
### `storage.StorageReport.checked_at`

[backend/app/schemas/storage.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L26) · type `datetime`

```python
required / inherited validation
```

<a id="storage-storagereport-directories"></a>
### `storage.StorageReport.directories`

[backend/app/schemas/storage.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L27) · type `list[StorageDirectory]`

```python
required / inherited validation
```

<a id="storage-storagereport-mount_detection"></a>
### `storage.StorageReport.mount_detection`

[backend/app/schemas/storage.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L28) · type `Literal['available', 'unavailable']`

```python
required / inherited validation
```

<a id="storage-storagereport-configuration_warnings"></a>
### `storage.StorageReport.configuration_warnings`

[backend/app/schemas/storage.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L29) · type `list[ConfigurationWarning]`

```python
[]
```

<a id="storage-storagereport-message"></a>
### `storage.StorageReport.message`

[backend/app/schemas/storage.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/storage.py#L30) · type `str`

```python
''
```

<a id="stream_stats-streamstats-observed_at"></a>
### `stream_stats.StreamStats.observed_at`

[backend/app/schemas/stream_stats.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stream_stats.py#L8) · type `datetime`

```python
required / inherited validation
```

<a id="stream_stats-streamstats-peers"></a>
### `stream_stats.StreamStats.peers`

[backend/app/schemas/stream_stats.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stream_stats.py#L9) · type `Optional[int]`

```python
Field(None, ge=0, le=2147483647)
```

<a id="stream_stats-streamstats-download_speed_kbytes_sec"></a>
### `stream_stats.StreamStats.download_speed_kbytes_sec`

[backend/app/schemas/stream_stats.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stream_stats.py#L10) · type `Optional[float]`

```python
Field(None, ge=0, le=1000000000000.0, description='Engine speed_down in Kbytes/sec; not encoded media bitrate')
```

<a id="stream_stats-streamstats-upload_speed_kbytes_sec"></a>
### `stream_stats.StreamStats.upload_speed_kbytes_sec`

[backend/app/schemas/stream_stats.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/stream_stats.py#L11) · type `Optional[float]`

```python
Field(None, ge=0, le=1000000000000.0, description='Engine speed_up in Kbytes/sec')
```

<a id="system-servicestatus-name"></a>
### `system.ServiceStatus.name`

[backend/app/schemas/system.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L12) · type `str`

```python
Field(description='Stable identifier: acestream, acestream-check, acexy, ipfs, zeronet, warp')
```

<a id="system-servicestatus-label"></a>
### `system.ServiceStatus.label`

[backend/app/schemas/system.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L13) · type `str`

```python
required / inherited validation
```

<a id="system-servicestatus-description"></a>
### `system.ServiceStatus.description`

[backend/app/schemas/system.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L14) · type `str`

```python
required / inherited validation
```

<a id="system-servicestatus-state"></a>
### `system.ServiceStatus.state`

[backend/app/schemas/system.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L15) · type `ServiceState`

```python
required / inherited validation
```

<a id="system-servicestatus-installed"></a>
### `system.ServiceStatus.installed`

[backend/app/schemas/system.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L16) · type `bool`

```python
Field(description='Shipped in this image flavor')
```

<a id="system-servicestatus-enabled"></a>
### `system.ServiceStatus.enabled`

[backend/app/schemas/system.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L17) · type `bool`

```python
Field(description='Turned on through its ENABLE_* variable')
```

<a id="system-servicestatus-managed"></a>
### `system.ServiceStatus.managed`

[backend/app/schemas/system.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L18) · type `bool`

```python
Field(description="Supervised by this container's entrypoint (controls available)")
```

<a id="system-servicestatus-stopped_by_user"></a>
### `system.ServiceStatus.stopped_by_user`

[backend/app/schemas/system.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L19) · type `bool`

```python
Field(default=False, description='Intentionally stopped until Start or container restart')
```

<a id="system-servicestatus-running"></a>
### `system.ServiceStatus.running`

[backend/app/schemas/system.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L20) · type `bool`

```python
Field(description='The service answered its health probe')
```

<a id="system-servicestatus-endpoint"></a>
### `system.ServiceStatus.endpoint`

[backend/app/schemas/system.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L21) · type `Optional[str]`

```python
Field(default=None, description='Where the app reaches the service')
```

<a id="system-servicestatus-open_streams"></a>
### `system.ServiceStatus.open_streams`

[backend/app/schemas/system.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L22) · type `Optional[int]`

```python
Field(default=None, ge=0, description='Distinct open streams; includes startup and idle grace. Null means unavailable, not zero.')
```

<a id="system-servicestatus-stream_count_scope"></a>
### `system.ServiceStatus.stream_count_scope`

[backend/app/schemas/system.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L23) · type `Optional[Literal['app', 'service']]`

```python
Field(default=None, description='app counts web-player and relay content IDs only; service is the Acexy-reported total. Counts may overlap.')
```

<a id="system-servicestatus-version"></a>
### `system.ServiceStatus.version`

[backend/app/schemas/system.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L24) · type `Optional[str]`

```python
None
```

<a id="system-servicestatus-distribution"></a>
### `system.ServiceStatus.distribution`

[backend/app/schemas/system.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L25) · type `Optional[str]`

```python
Field(default=None, description='Package or image that supplied the service')
```

<a id="system-servicestatus-distribution_url"></a>
### `system.ServiceStatus.distribution_url`

[backend/app/schemas/system.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L26) · type `Optional[str]`

```python
Field(default=None, description='Public attribution page for the distribution')
```

<a id="system-servicestatus-message"></a>
### `system.ServiceStatus.message`

[backend/app/schemas/system.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L27) · type `str`

```python
required / inherited validation
```

<a id="system-servicestatus-pid"></a>
### `system.ServiceStatus.pid`

[backend/app/schemas/system.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L28) · type `Optional[int]`

```python
None
```

<a id="system-servicestatus-uptime_seconds"></a>
### `system.ServiceStatus.uptime_seconds`

[backend/app/schemas/system.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L29) · type `Optional[int]`

```python
None
```

<a id="system-servicesstatusresponse-services"></a>
### `system.ServicesStatusResponse.services`

[backend/app/schemas/system.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L33) · type `List[ServiceStatus]`

```python
required / inherited validation
```

<a id="system-servicesstatusresponse-supervised"></a>
### `system.ServicesStatusResponse.supervised`

[backend/app/schemas/system.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L34) · type `bool`

```python
Field(description='True when the app runs under the container entrypoint')
```

<a id="system-servicesstatusresponse-checked_at"></a>
### `system.ServicesStatusResponse.checked_at`

[backend/app/schemas/system.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L35) · type `str`

```python
required / inherited validation
```

<a id="system-servicerestartresponse-name"></a>
### `system.ServiceRestartResponse.name`

[backend/app/schemas/system.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L39) · type `str`

```python
required / inherited validation
```

<a id="system-servicerestartresponse-success"></a>
### `system.ServiceRestartResponse.success`

[backend/app/schemas/system.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L40) · type `bool`

```python
required / inherited validation
```

<a id="system-servicerestartresponse-message"></a>
### `system.ServiceRestartResponse.message`

[backend/app/schemas/system.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L41) · type `str`

```python
required / inherited validation
```

<a id="system-publicurlresponse-url"></a>
### `system.PublicUrlResponse.url`

[backend/app/schemas/system.py:46](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L46) · type `str`

```python
Field(description='scheme://host[:port], no trailing slash')
```

<a id="system-publicurlresponse-source"></a>
### `system.PublicUrlResponse.source`

[backend/app/schemas/system.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L47) · type `Literal['setting', 'forwarded', 'request']`

```python
required / inherited validation
```

<a id="system-publicurlresponse-warnings"></a>
### `system.PublicUrlResponse.warnings`

[backend/app/schemas/system.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/system.py#L48) · type `List[str]`

```python
Field(default_factory=list, description='localhost | docker-internal | unset | proxied')
```

<a id="telegram-telegramlogin-api_id"></a>
### `telegram.TelegramLogin.api_id`

[backend/app/schemas/telegram.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L10) · type `int`

```python
Field(gt=0, le=2147483647)
```

<a id="telegram-telegramlogin-api_hash"></a>
### `telegram.TelegramLogin.api_hash`

[backend/app/schemas/telegram.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L11) · type `SecretStr`

```python
Field(min_length=32, max_length=32)
```

<a id="telegram-telegramlogin-phone"></a>
### `telegram.TelegramLogin.phone`

[backend/app/schemas/telegram.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L12) · type `SecretStr`

```python
Field(min_length=5, max_length=32)
```

<a id="telegram-telegramcode-code"></a>
### `telegram.TelegramCode.code`

[backend/app/schemas/telegram.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L16) · type `SecretStr`

```python
Field(min_length=1, max_length=16)
```

<a id="telegram-telegrampassword-password"></a>
### `telegram.TelegramPassword.password`

[backend/app/schemas/telegram.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L20) · type `SecretStr`

```python
Field(min_length=1, max_length=256)
```

<a id="telegram-telegramstatus-state"></a>
### `telegram.TelegramStatus.state`

[backend/app/schemas/telegram.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L24) · type `str`

```python
required / inherited validation
```

<a id="telegram-telegramstatus-message"></a>
### `telegram.TelegramStatus.message`

[backend/app/schemas/telegram.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L25) · type `str`

```python
''
```

<a id="telegram-telegramstatus-account_label"></a>
### `telegram.TelegramStatus.account_label`

[backend/app/schemas/telegram.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L26) · type `str`

```python
''
```

<a id="telegram-telegramstatus-queue_size"></a>
### `telegram.TelegramStatus.queue_size`

[backend/app/schemas/telegram.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L27) · type `int`

```python
0
```

<a id="telegram-telegramstatus-retry_at"></a>
### `telegram.TelegramStatus.retry_at`

[backend/app/schemas/telegram.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L28) · type `datetime | None`

```python
None
```

<a id="telegram-telegrampeer-id"></a>
### `telegram.TelegramPeer.id`

[backend/app/schemas/telegram.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L32) · type `str`

```python
required / inherited validation
```

<a id="telegram-telegrampeer-label"></a>
### `telegram.TelegramPeer.label`

[backend/app/schemas/telegram.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L33) · type `str`

```python
required / inherited validation
```

<a id="telegram-telegrampeer-kind"></a>
### `telegram.TelegramPeer.kind`

[backend/app/schemas/telegram.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L34) · type `Literal['user', 'chat', 'channel', 'topic']`

```python
required / inherited validation
```

<a id="telegram-telegramsourceconfig-name"></a>
### `telegram.TelegramSourceConfig.name`

[backend/app/schemas/telegram.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L39) · type `str`

```python
Field(min_length=1, max_length=100)
```

<a id="telegram-telegramsourceconfig-chat_id"></a>
### `telegram.TelegramSourceConfig.chat_id`

[backend/app/schemas/telegram.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L40) · type `str`

```python
Field(pattern='^-?[1-9][0-9]{0,18}$')
```

<a id="telegram-telegramsourceconfig-topic_id"></a>
### `telegram.TelegramSourceConfig.topic_id`

[backend/app/schemas/telegram.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L41) · type `int | None`

```python
Field(None, gt=0)
```

<a id="telegram-telegramsourceconfig-enabled"></a>
### `telegram.TelegramSourceConfig.enabled`

[backend/app/schemas/telegram.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L42) · type `bool`

```python
True
```

<a id="telegram-telegramsourceconfig-sender_ids"></a>
### `telegram.TelegramSourceConfig.sender_ids`

[backend/app/schemas/telegram.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L43) · type `list[str]`

```python
Field(default_factory=list, max_length=100)
```

<a id="telegram-telegramsourceconfig-sender_rule"></a>
### `telegram.TelegramSourceConfig.sender_rule`

[backend/app/schemas/telegram.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L44) · type `Literal['posting', 'original']`

```python
'posting'
```

<a id="telegram-telegramsourceconfig-include_forwards"></a>
### `telegram.TelegramSourceConfig.include_forwards`

[backend/app/schemas/telegram.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L45) · type `bool`

```python
True
```

<a id="telegram-telegramsourceconfig-include"></a>
### `telegram.TelegramSourceConfig.include`

[backend/app/schemas/telegram.py:46](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L46) · type `str`

```python
Field('', max_length=512)
```

<a id="telegram-telegramsourceconfig-exclude"></a>
### `telegram.TelegramSourceConfig.exclude`

[backend/app/schemas/telegram.py:47](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L47) · type `str`

```python
Field('', max_length=512)
```

<a id="telegram-telegramsourceconfig-filter_mode"></a>
### `telegram.TelegramSourceConfig.filter_mode`

[backend/app/schemas/telegram.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L48) · type `Literal['keyword', 'regex']`

```python
'keyword'
```

<a id="telegram-telegramsourceconfig-bare_ids"></a>
### `telegram.TelegramSourceConfig.bare_ids`

[backend/app/schemas/telegram.py:49](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L49) · type `bool`

```python
True
```

<a id="telegram-telegramsourceconfig-recipe"></a>
### `telegram.TelegramSourceConfig.recipe`

[backend/app/schemas/telegram.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L50) · type `ExtractionRecipe | None`

```python
None
```

<a id="telegram-telegramsourcecreate-history_count"></a>
### `telegram.TelegramSourceCreate.history_count`

[backend/app/schemas/telegram.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L66) · type `int`

```python
Field(0, ge=0, le=1000)
```

<a id="telegram-telegramsourcecreate-history_since"></a>
### `telegram.TelegramSourceCreate.history_since`

[backend/app/schemas/telegram.py:67](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L67) · type `datetime | None`

```python
None
```

<a id="telegram-telegramsource-excluded_count"></a>
### `telegram.TelegramSource.excluded_count`

[backend/app/schemas/telegram.py:77](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L77) · type `int`

```python
0
```

<a id="telegram-telegramsource-id"></a>
### `telegram.TelegramSource.id`

[backend/app/schemas/telegram.py:78](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L78) · type `int`

```python
required / inherited validation
```

<a id="telegram-telegramsource-chat_label"></a>
### `telegram.TelegramSource.chat_label`

[backend/app/schemas/telegram.py:79](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L79) · type `str`

```python
required / inherited validation
```

<a id="telegram-telegramsource-sender_labels"></a>
### `telegram.TelegramSource.sender_labels`

[backend/app/schemas/telegram.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L80) · type `dict[str, str]`

```python
Field(default_factory=dict)
```

<a id="telegram-telegramsource-cursor"></a>
### `telegram.TelegramSource.cursor`

[backend/app/schemas/telegram.py:81](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L81) · type `int`

```python
required / inherited validation
```

<a id="telegram-telegramsource-state"></a>
### `telegram.TelegramSource.state`

[backend/app/schemas/telegram.py:82](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L82) · type `str`

```python
required / inherited validation
```

<a id="telegram-telegramsource-last_success"></a>
### `telegram.TelegramSource.last_success`

[backend/app/schemas/telegram.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L83) · type `datetime | None`

```python
None
```

<a id="telegram-telegramsource-imported_count"></a>
### `telegram.TelegramSource.imported_count`

[backend/app/schemas/telegram.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L84) · type `int`

```python
required / inherited validation
```

<a id="telegram-telegramsource-message"></a>
### `telegram.TelegramSource.message`

[backend/app/schemas/telegram.py:85](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L85) · type `str`

```python
required / inherited validation
```

<a id="telegram-telegrampreviewmessage-excluded_count"></a>
### `telegram.TelegramPreviewMessage.excluded_count`

[backend/app/schemas/telegram.py:89](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L89) · type `int`

```python
0
```

<a id="telegram-telegrampreviewmessage-excluded_rule_ids"></a>
### `telegram.TelegramPreviewMessage.excluded_rule_ids`

[backend/app/schemas/telegram.py:90](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L90) · type `dict[str, list[int]]`

```python
Field(default_factory=dict)
```

<a id="telegram-telegrampreviewmessage-message_id"></a>
### `telegram.TelegramPreviewMessage.message_id`

[backend/app/schemas/telegram.py:91](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L91) · type `int`

```python
required / inherited validation
```

<a id="telegram-telegrampreviewmessage-sender_id"></a>
### `telegram.TelegramPreviewMessage.sender_id`

[backend/app/schemas/telegram.py:92](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L92) · type `str | None`

```python
None
```

<a id="telegram-telegrampreviewmessage-outcome"></a>
### `telegram.TelegramPreviewMessage.outcome`

[backend/app/schemas/telegram.py:93](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L93) · type `str`

```python
required / inherited validation
```

<a id="telegram-telegrampreviewmessage-result"></a>
### `telegram.TelegramPreviewMessage.result`

[backend/app/schemas/telegram.py:94](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L94) · type `RecipePreview`

```python
required / inherited validation
```

<a id="telegram-telegrampreviewrequest-source"></a>
### `telegram.TelegramPreviewRequest.source`

[backend/app/schemas/telegram.py:98](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L98) · type `TelegramSourceConfig`

```python
required / inherited validation
```

<a id="telegram-telegrampreviewrequest-limit"></a>
### `telegram.TelegramPreviewRequest.limit`

[backend/app/schemas/telegram.py:99](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L99) · type `int`

```python
Field(10, ge=1, le=30)
```

<a id="telegram-telegrampreview-chat_id"></a>
### `telegram.TelegramPreview.chat_id`

[backend/app/schemas/telegram.py:103](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L103) · type `str`

```python
required / inherited validation
```

<a id="telegram-telegrampreview-messages"></a>
### `telegram.TelegramPreview.messages`

[backend/app/schemas/telegram.py:104](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L104) · type `list[TelegramPreviewMessage]`

```python
required / inherited validation
```

<a id="telegram-telegramresolve-username"></a>
### `telegram.TelegramResolve.username`

[backend/app/schemas/telegram.py:108](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/telegram.py#L108) · type `str`

```python
Field(pattern='^@?[A-Za-z][A-Za-z0-9_]{3,31}$')
```

<a id="tuner-tunersettingsresponse-friendly_name"></a>
### `tuner.TunerSettingsResponse.friendly_name`

[backend/app/schemas/tuner.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L10) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunersettingsresponse-tuner_count"></a>
### `tuner.TunerSettingsResponse.tuner_count`

[backend/app/schemas/tuner.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L11) · type `int`

```python
required / inherited validation
```

<a id="tuner-tunersettingsresponse-max_channels"></a>
### `tuner.TunerSettingsResponse.max_channels`

[backend/app/schemas/tuner.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L12) · type `int`

```python
required / inherited validation
```

<a id="tuner-tunersettingsresponse-only_online"></a>
### `tuner.TunerSettingsResponse.only_online`

[backend/app/schemas/tuner.py:13](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L13) · type `bool`

```python
required / inherited validation
```

<a id="tuner-tunersettingsresponse-hide_unusable"></a>
### `tuner.TunerSettingsResponse.hide_unusable`

[backend/app/schemas/tuner.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L14) · type `bool`

```python
Field(False, description='Leave out sources no list has published for two weeks or whose recent playback clearly failed, and channels left with none (lineup and M3U playlists)')
```

<a id="tuner-tunersettingsresponse-plex_compatible_audio"></a>
### `tuner.TunerSettingsResponse.plex_compatible_audio`

[backend/app/schemas/tuner.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L15) · type `bool`

```python
Field(False, description='Convert tuner audio to stereo AAC/LATM for Plex Desktop; copy video unless experimental recovery is enabled')
```

<a id="tuner-tunersettingsresponse-experimental_transcoding"></a>
### `tuner.TunerSettingsResponse.experimental_transcoding`

[backend/app/schemas/tuner.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L16) · type `bool`

```python
Field(False, description='Experimental CPU-intensive transcoding for midstream recovery; default recovery requires client reconnection')
```

<a id="tuner-tunersettingsresponse-source_start_seconds"></a>
### `tuner.TunerSettingsResponse.source_start_seconds`

[backend/app/schemas/tuner.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L17) · type `int`

```python
Field(15, description='Seconds a source gets to deliver its first byte before the next is tried')
```

<a id="tuner-tunersettingsresponse-startup_budget_seconds"></a>
### `tuner.TunerSettingsResponse.startup_budget_seconds`

[backend/app/schemas/tuner.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L18) · type `int`

```python
Field(45, description="Seconds for the whole start across sources; keep it under the player's own timeout (Kodi gives up after about 30)")
```

<a id="tuner-tunersettingsupdate-friendly_name"></a>
### `tuner.TunerSettingsUpdate.friendly_name`

[backend/app/schemas/tuner.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L22) · type `Optional[str]`

```python
Field(None, max_length=255)
```

<a id="tuner-tunersettingsupdate-tuner_count"></a>
### `tuner.TunerSettingsUpdate.tuner_count`

[backend/app/schemas/tuner.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L23) · type `Optional[int]`

```python
Field(None, ge=1, le=16)
```

<a id="tuner-tunersettingsupdate-max_channels"></a>
### `tuner.TunerSettingsUpdate.max_channels`

[backend/app/schemas/tuner.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L24) · type `Optional[int]`

```python
Field(None, ge=1, le=1000)
```

<a id="tuner-tunersettingsupdate-only_online"></a>
### `tuner.TunerSettingsUpdate.only_online`

[backend/app/schemas/tuner.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L25) · type `Optional[bool]`

```python
None
```

<a id="tuner-tunersettingsupdate-hide_unusable"></a>
### `tuner.TunerSettingsUpdate.hide_unusable`

[backend/app/schemas/tuner.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L26) · type `Optional[bool]`

```python
None
```

<a id="tuner-tunersettingsupdate-plex_compatible_audio"></a>
### `tuner.TunerSettingsUpdate.plex_compatible_audio`

[backend/app/schemas/tuner.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L27) · type `Optional[bool]`

```python
None
```

<a id="tuner-tunersettingsupdate-experimental_transcoding"></a>
### `tuner.TunerSettingsUpdate.experimental_transcoding`

[backend/app/schemas/tuner.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L28) · type `Optional[bool]`

```python
None
```

<a id="tuner-tunersettingsupdate-source_start_seconds"></a>
### `tuner.TunerSettingsUpdate.source_start_seconds`

[backend/app/schemas/tuner.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L29) · type `Optional[int]`

```python
Field(None, ge=5, le=180)
```

<a id="tuner-tunersettingsupdate-startup_budget_seconds"></a>
### `tuner.TunerSettingsUpdate.startup_budget_seconds`

[backend/app/schemas/tuner.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L30) · type `Optional[int]`

```python
Field(None, ge=5, le=180)
```

<a id="tuner-tunerrenumbered-tv_channel_id"></a>
### `tuner.TunerRenumbered.tv_channel_id`

[backend/app/schemas/tuner.py:34](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L34) · type `int`

```python
required / inherited validation
```

<a id="tuner-tunerrenumbered-name"></a>
### `tuner.TunerRenumbered.name`

[backend/app/schemas/tuner.py:35](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L35) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerrenumbered-requested_number"></a>
### `tuner.TunerRenumbered.requested_number`

[backend/app/schemas/tuner.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L36) · type `int`

```python
required / inherited validation
```

<a id="tuner-tunerrenumbered-assigned_number"></a>
### `tuner.TunerRenumbered.assigned_number`

[backend/app/schemas/tuner.py:37](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L37) · type `int`

```python
required / inherited validation
```

<a id="tuner-tunerurls-tuner"></a>
### `tuner.TunerUrls.tuner`

[backend/app/schemas/tuner.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L41) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerurls-lineup"></a>
### `tuner.TunerUrls.lineup`

[backend/app/schemas/tuner.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L42) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerurls-guide"></a>
### `tuner.TunerUrls.guide`

[backend/app/schemas/tuner.py:43](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L43) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerurls-playlist"></a>
### `tuner.TunerUrls.playlist`

[backend/app/schemas/tuner.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L44) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerurls-epg"></a>
### `tuner.TunerUrls.epg`

[backend/app/schemas/tuner.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L45) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerurls-stream_template"></a>
### `tuner.TunerUrls.stream_template`

[backend/app/schemas/tuner.py:46](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L46) · type `str`

```python
Field(description='Stable TV channel playback URL template; replace {tv_channel_id} with its numeric ID')
```

<a id="tuner-tunerdenial-client_ip"></a>
### `tuner.TunerDenial.client_ip`

[backend/app/schemas/tuner.py:50](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L50) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerdenial-peer"></a>
### `tuner.TunerDenial.peer`

[backend/app/schemas/tuner.py:51](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L51) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerdenial-path"></a>
### `tuner.TunerDenial.path`

[backend/app/schemas/tuner.py:52](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L52) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerdenial-at"></a>
### `tuner.TunerDenial.at`

[backend/app/schemas/tuner.py:53](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L53) · type `float`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-channel_count"></a>
### `tuner.TunerStatusResponse.channel_count`

[backend/app/schemas/tuner.py:57](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L57) · type `int`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-renumbered"></a>
### `tuner.TunerStatusResponse.renumbered`

[backend/app/schemas/tuner.py:58](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L58) · type `List[TunerRenumbered]`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-overflow"></a>
### `tuner.TunerStatusResponse.overflow`

[backend/app/schemas/tuner.py:59](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L59) · type `int`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-device_id"></a>
### `tuner.TunerStatusResponse.device_id`

[backend/app/schemas/tuner.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L60) · type `str`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-urls"></a>
### `tuner.TunerStatusResponse.urls`

[backend/app/schemas/tuner.py:61](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L61) · type `TunerUrls`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-ffmpeg_available"></a>
### `tuner.TunerStatusResponse.ffmpeg_available`

[backend/app/schemas/tuner.py:62](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L62) · type `bool`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-allowed_networks"></a>
### `tuner.TunerStatusResponse.allowed_networks`

[backend/app/schemas/tuner.py:63](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L63) · type `List[str]`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-client_ip"></a>
### `tuner.TunerStatusResponse.client_ip`

[backend/app/schemas/tuner.py:64](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L64) · type `Optional[str]`

```python
None
```

<a id="tuner-tunerstatusresponse-peer"></a>
### `tuner.TunerStatusResponse.peer`

[backend/app/schemas/tuner.py:65](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L65) · type `Optional[str]`

```python
None
```

<a id="tuner-tunerstatusresponse-client_allowed"></a>
### `tuner.TunerStatusResponse.client_allowed`

[backend/app/schemas/tuner.py:66](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L66) · type `bool`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-client_source"></a>
### `tuner.TunerStatusResponse.client_source`

[backend/app/schemas/tuner.py:67](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L67) · type `Literal['direct', 'forwarded', 'docker-gateway', 'loopback']`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-warnings"></a>
### `tuner.TunerStatusResponse.warnings`

[backend/app/schemas/tuner.py:68](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L68) · type `List[str]`

```python
required / inherited validation
```

<a id="tuner-tunerstatusresponse-recent_denials"></a>
### `tuner.TunerStatusResponse.recent_denials`

[backend/app/schemas/tuner.py:69](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tuner.py#L69) · type `List[TunerDenial]`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchoptions-include_similar"></a>
### `tv_matching.TVMatchOptions.include_similar`

[backend/app/schemas/tv_matching.py:7](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L7) · type `bool`

```python
Field(False, description='Include similar names for explicit review; never automatic assignments.')
```

<a id="tv_matching-tvmatchoptions-assumed_country"></a>
### `tv_matching.TVMatchOptions.assumed_country`

[backend/app/schemas/tv_matching.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L8) · type `Literal['ES', 'PT', 'FR', 'DE', 'IT', 'GB', 'US', 'NL', 'PL', 'TR', 'BE', 'AR', 'RU'] | None`

```python
Field(default=None, description='Matching-only country for unlabelled streams and TV channels; explicit countries take precedence.')
```

<a id="tv_matching-tvmatchcandidate-acestream_channel_id"></a>
### `tv_matching.TVMatchCandidate.acestream_channel_id`

[backend/app/schemas/tv_matching.py:14](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L14) · type `str`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchcandidate-acestream_name"></a>
### `tv_matching.TVMatchCandidate.acestream_name`

[backend/app/schemas/tv_matching.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L15) · type `str`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchcandidate-tv_channel_id"></a>
### `tv_matching.TVMatchCandidate.tv_channel_id`

[backend/app/schemas/tv_matching.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L16) · type `int`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchcandidate-tv_channel_name"></a>
### `tv_matching.TVMatchCandidate.tv_channel_name`

[backend/app/schemas/tv_matching.py:17](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L17) · type `str`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchcandidate-score"></a>
### `tv_matching.TVMatchCandidate.score`

[backend/app/schemas/tv_matching.py:18](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L18) · type `float`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchcandidate-reason"></a>
### `tv_matching.TVMatchCandidate.reason`

[backend/app/schemas/tv_matching.py:19](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L19) · type `str`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchcandidate-recommended"></a>
### `tv_matching.TVMatchCandidate.recommended`

[backend/app/schemas/tv_matching.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L20) · type `bool`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchpreview-tv_channels"></a>
### `tv_matching.TVMatchPreview.tv_channels`

[backend/app/schemas/tv_matching.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L24) · type `int`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchpreview-unassigned_streams"></a>
### `tv_matching.TVMatchPreview.unassigned_streams`

[backend/app/schemas/tv_matching.py:25](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L25) · type `int`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchpreview-ambiguous_streams"></a>
### `tv_matching.TVMatchPreview.ambiguous_streams`

[backend/app/schemas/tv_matching.py:26](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L26) · type `int`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchpreview-unmatched_streams"></a>
### `tv_matching.TVMatchPreview.unmatched_streams`

[backend/app/schemas/tv_matching.py:27](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L27) · type `int`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchpreview-candidates"></a>
### `tv_matching.TVMatchPreview.candidates`

[backend/app/schemas/tv_matching.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L28) · type `list[TVMatchCandidate]`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchassignment-acestream_channel_id"></a>
### `tv_matching.TVMatchAssignment.acestream_channel_id`

[backend/app/schemas/tv_matching.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L32) · type `str`

```python
Field(min_length=1, max_length=100)
```

<a id="tv_matching-tvmatchassignment-tv_channel_id"></a>
### `tv_matching.TVMatchAssignment.tv_channel_id`

[backend/app/schemas/tv_matching.py:33](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L33) · type `int`

```python
Field(gt=0)
```

<a id="tv_matching-tvmatchapplyrequest-assignments"></a>
### `tv_matching.TVMatchApplyRequest.assignments`

[backend/app/schemas/tv_matching.py:37](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L37) · type `list[TVMatchAssignment]`

```python
Field(min_length=1, max_length=10000)
```

<a id="tv_matching-tvmatchapplyresponse-assigned_count"></a>
### `tv_matching.TVMatchApplyResponse.assigned_count`

[backend/app/schemas/tv_matching.py:41](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L41) · type `int`

```python
required / inherited validation
```

<a id="tv_matching-tvmatchapplyresponse-skipped_count"></a>
### `tv_matching.TVMatchApplyResponse.skipped_count`

[backend/app/schemas/tv_matching.py:42](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/tv_matching.py#L42) · type `int`

```python
required / inherited validation
```

<a id="updates-updatestatus-current_version"></a>
### `updates.UpdateStatus.current_version`

[backend/app/schemas/updates.py:7](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/updates.py#L7) · type `str`

```python
required / inherited validation
```

<a id="updates-updatestatus-latest_version"></a>
### `updates.UpdateStatus.latest_version`

[backend/app/schemas/updates.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/updates.py#L8) · type `str | None`

```python
None
```

<a id="updates-updatestatus-update_available"></a>
### `updates.UpdateStatus.update_available`

[backend/app/schemas/updates.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/updates.py#L9) · type `bool`

```python
False
```

<a id="updates-updatestatus-release_url"></a>
### `updates.UpdateStatus.release_url`

[backend/app/schemas/updates.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/updates.py#L10) · type `str | None`

```python
None
```

<a id="updates-updatestatus-deployment"></a>
### `updates.UpdateStatus.deployment`

[backend/app/schemas/updates.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/updates.py#L11) · type `Literal['docker', 'native']`

```python
required / inherited validation
```

<a id="updates-updatestatus-status"></a>
### `updates.UpdateStatus.status`

[backend/app/schemas/updates.py:12](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/updates.py#L12) · type `Literal['checked', 'unavailable']`

```python
required / inherited validation
```

<a id="warp-warplicenserequest-license_key"></a>
### `warp.WarpLicenseRequest.license_key`

[backend/app/schemas/warp.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L21) · type `str`

```python
Field(..., description='The WARP license key to register', min_length=8)
```

<a id="warp-warpmoderequest-mode"></a>
### `warp.WarpModeRequest.mode`

[backend/app/schemas/warp.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L29) · type `WarpModeEnum`

```python
Field(..., description='The WARP mode to set')
```

<a id="warp-warpstatusresponse-running"></a>
### `warp.WarpStatusResponse.running`

[backend/app/schemas/warp.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L36) · type `bool`

```python
Field(default=False, description='Whether the WARP daemon is running')
```

<a id="warp-warpstatusresponse-connected"></a>
### `warp.WarpStatusResponse.connected`

[backend/app/schemas/warp.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L40) · type `bool`

```python
Field(default=False, description='Whether WARP is connected')
```

<a id="warp-warpstatusresponse-mode"></a>
### `warp.WarpStatusResponse.mode`

[backend/app/schemas/warp.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L44) · type `Optional[str]`

```python
Field(default=None, description='The current WARP mode')
```

<a id="warp-warpstatusresponse-account_type"></a>
### `warp.WarpStatusResponse.account_type`

[backend/app/schemas/warp.py:48](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L48) · type `str`

```python
Field(default='free', description='The type of WARP account (free, premium, team)')
```

<a id="warp-warpstatusresponse-ip"></a>
### `warp.WarpStatusResponse.ip`

[backend/app/schemas/warp.py:52](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L52) · type `Optional[str]`

```python
Field(default=None, description='The current IP address when connected to WARP')
```

<a id="warp-warpstatusresponse-location"></a>
### `warp.WarpStatusResponse.location`

[backend/app/schemas/warp.py:56](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L56) · type `Optional[str]`

```python
Field(default=None, description="Country code reported by Cloudflare's trace")
```

<a id="warp-warpstatusresponse-colo"></a>
### `warp.WarpStatusResponse.colo`

[backend/app/schemas/warp.py:57](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L57) · type `Optional[str]`

```python
Field(default=None, description='Cloudflare data centre serving the tunnel')
```

<a id="warp-warpstatusresponse-tunnel"></a>
### `warp.WarpStatusResponse.tunnel`

[backend/app/schemas/warp.py:58](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L58) · type `Dict[str, Optional[str]]`

```python
Field(default_factory=dict, description='Details from `warp-cli tunnel stats`')
```

<a id="warp-warpstatusresponse-registration"></a>
### `warp.WarpStatusResponse.registration`

[backend/app/schemas/warp.py:59](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L59) · type `Dict[str, Optional[str]]`

```python
Field(default_factory=dict, description='Account/device ids and masked license')
```

<a id="warp-warpstatusresponse-cf_trace"></a>
### `warp.WarpStatusResponse.cf_trace`

[backend/app/schemas/warp.py:60](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L60) · type `Dict[str, str]`

```python
Field(default_factory=dict, description='Cloudflare trace information')
```

<a id="warp-warpresponse-success"></a>
### `warp.WarpResponse.success`

[backend/app/schemas/warp.py:67](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L67) · type `bool`

```python
required / inherited validation
```

<a id="warp-warpresponse-status"></a>
### `warp.WarpResponse.status`

[backend/app/schemas/warp.py:68](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L68) · type `str`

```python
Field(default='success', description='Operation status (success/error)')
```

<a id="warp-warpresponse-message"></a>
### `warp.WarpResponse.message`

[backend/app/schemas/warp.py:69](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L69) · type `str`

```python
required / inherited validation
```

<a id="warp-warpresponse-details"></a>
### `warp.WarpResponse.details`

[backend/app/schemas/warp.py:70](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L70) · type `Optional[Dict[str, Any]]`

```python
None
```

<a id="warp-warpexclusionsupdate-hosts"></a>
### `warp.WarpExclusionsUpdate.hosts`

[backend/app/schemas/warp.py:75](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L75) · type `list[str]`

```python
Field(max_length=64)
```

<a id="warp-warpexclusionsupdate-expected_revision"></a>
### `warp.WarpExclusionsUpdate.expected_revision`

[backend/app/schemas/warp.py:76](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L76) · type `str`

```python
Field(min_length=64, max_length=64)
```

<a id="warp-warpexclusionsstate-hosts"></a>
### `warp.WarpExclusionsState.hosts`

[backend/app/schemas/warp.py:80](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L80) · type `list[str]`

```python
required / inherited validation
```

<a id="warp-warpexclusionsstate-revision"></a>
### `warp.WarpExclusionsState.revision`

[backend/app/schemas/warp.py:81](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L81) · type `str`

```python
required / inherited validation
```

<a id="warp-warpexclusionsstate-active_hosts"></a>
### `warp.WarpExclusionsState.active_hosts`

[backend/app/schemas/warp.py:82](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L82) · type `list[str] | None`

```python
required / inherited validation
```

<a id="warp-warpexclusionsstate-applied"></a>
### `warp.WarpExclusionsState.applied`

[backend/app/schemas/warp.py:83](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L83) · type `bool`

```python
required / inherited validation
```

<a id="warp-warpexclusionsstate-error"></a>
### `warp.WarpExclusionsState.error`

[backend/app/schemas/warp.py:84](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/warp.py#L84) · type `str | None`

```python
None
```

<a id="watch-watchchannel-id"></a>
### `watch.WatchChannel.id`

[backend/app/schemas/watch.py:7](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L7) · type `str`

```python
required / inherited validation
```

<a id="watch-watchchannel-name"></a>
### `watch.WatchChannel.name`

[backend/app/schemas/watch.py:8](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L8) · type `str`

```python
required / inherited validation
```

<a id="watch-watchchannel-category"></a>
### `watch.WatchChannel.category`

[backend/app/schemas/watch.py:9](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L9) · type `str | None`

```python
None
```

<a id="watch-watchchannel-tv_channel_id"></a>
### `watch.WatchChannel.tv_channel_id`

[backend/app/schemas/watch.py:10](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L10) · type `int | None`

```python
None
```

<a id="watch-watchchannel-online"></a>
### `watch.WatchChannel.online`

[backend/app/schemas/watch.py:11](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L11) · type `bool | None`

```python
None
```

<a id="watch-watchchannels-items"></a>
### `watch.WatchChannels.items`

[backend/app/schemas/watch.py:15](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L15) · type `list[WatchChannel]`

```python
required / inherited validation
```

<a id="watch-watchchannels-total"></a>
### `watch.WatchChannels.total`

[backend/app/schemas/watch.py:16](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L16) · type `int`

```python
required / inherited validation
```

<a id="watch-watchprogramme-id"></a>
### `watch.WatchProgramme.id`

[backend/app/schemas/watch.py:20](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L20) · type `int`

```python
required / inherited validation
```

<a id="watch-watchprogramme-channel"></a>
### `watch.WatchProgramme.channel`

[backend/app/schemas/watch.py:21](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L21) · type `str`

```python
required / inherited validation
```

<a id="watch-watchprogramme-title"></a>
### `watch.WatchProgramme.title`

[backend/app/schemas/watch.py:22](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L22) · type `str`

```python
required / inherited validation
```

<a id="watch-watchprogramme-start"></a>
### `watch.WatchProgramme.start`

[backend/app/schemas/watch.py:23](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L23) · type `datetime`

```python
required / inherited validation
```

<a id="watch-watchprogramme-end"></a>
### `watch.WatchProgramme.end`

[backend/app/schemas/watch.py:24](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L24) · type `datetime`

```python
required / inherited validation
```

<a id="watch-watchevent-id"></a>
### `watch.WatchEvent.id`

[backend/app/schemas/watch.py:28](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L28) · type `str`

```python
required / inherited validation
```

<a id="watch-watchevent-title"></a>
### `watch.WatchEvent.title`

[backend/app/schemas/watch.py:29](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L29) · type `str`

```python
required / inherited validation
```

<a id="watch-watchevent-starts_at"></a>
### `watch.WatchEvent.starts_at`

[backend/app/schemas/watch.py:30](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L30) · type `str | None`

```python
None
```

<a id="watch-watchevent-competition"></a>
### `watch.WatchEvent.competition`

[backend/app/schemas/watch.py:31](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L31) · type `str`

```python
''
```

<a id="watch-watchevent-state"></a>
### `watch.WatchEvent.state`

[backend/app/schemas/watch.py:32](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L32) · type `str`

```python
''
```

<a id="watch-watchrecording-id"></a>
### `watch.WatchRecording.id`

[backend/app/schemas/watch.py:36](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L36) · type `str`

```python
required / inherited validation
```

<a id="watch-watchrecording-title"></a>
### `watch.WatchRecording.title`

[backend/app/schemas/watch.py:37](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L37) · type `str`

```python
required / inherited validation
```

<a id="watch-watchrecording-channel"></a>
### `watch.WatchRecording.channel`

[backend/app/schemas/watch.py:38](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L38) · type `str`

```python
required / inherited validation
```

<a id="watch-watchrecording-state"></a>
### `watch.WatchRecording.state`

[backend/app/schemas/watch.py:39](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L39) · type `str`

```python
required / inherited validation
```

<a id="watch-watchrecording-files"></a>
### `watch.WatchRecording.files`

[backend/app/schemas/watch.py:40](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L40) · type `list[str]`

```python
Field(default_factory=list)
```

<a id="watch-playlistlink-url"></a>
### `watch.PlaylistLink.url`

[backend/app/schemas/watch.py:44](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L44) · type `str`

```python
required / inherited validation
```

<a id="watch-playlistlink-guide_url"></a>
### `watch.PlaylistLink.guide_url`

[backend/app/schemas/watch.py:45](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/watch.py#L45) · type `str`

```python
required / inherited validation
```
