# Surface → evidence → composition → interaction → verification → acceptance

Current public source: `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`. Each row is an authored, composed design proposal. “Rendered” evidence is the current [verification run](verification-review-06.md), not an implementation or user-approval claim. Exact field rows and state lists appear in the linked specification.

This matrix covers every composed surface and field occurrence. [Source control map](source-control-map.md) records the current input-bearing TSX modules, including reused controls; [source contracts](source-contracts.md) preserves request/response constraints separately from visual fields. Historical screenshots are not new passes.

<a id="recording-schedule"></a>
## Schedule a programme

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/live-tv?channel=demo`; recording.adjust_times, recording.timezone, recording.start_time, recording.end_time; ready, loading, error, permission, dirty, pending, success, conflict, capacity, stale | [RecordingDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingDialog.tsx) | [Composed screen](workflow-prototype.html?screen=recording-schedule); [specification](workflow-specification.md#recording-schedule) | [Desktop EN](workflow-exports/recording-schedule-cyan-en.jpg), [phone ES](workflow-exports/recording-schedule-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-dst"></a>
## Choose the exact time

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/recordings`; recording.start_choice, recording.end_choice; ready, loading, error, permission, dirty, pending, success, conflict, gap | [recordingTimes.ts](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/utils/recordingTimes.ts) | [Composed screen](workflow-prototype.html?screen=recording-dst); [specification](workflow-specification.md#recording-dst) | [Desktop EN](workflow-exports/recording-dst-cyan-en.jpg), [phone ES](workflow-exports/recording-dst-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-now"></a>
## Record now

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/live-tv`; recording.end_time; ready, loading, error, permission, dirty, pending, success, conflict | [RecordingDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingDialog.tsx) | [Composed screen](workflow-prototype.html?screen=recording-now); [specification](workflow-specification.md#recording-now) | [Desktop EN](workflow-exports/recording-now-cyan-en.jpg), [phone ES](workflow-exports/recording-now-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-active"></a>
## Recording in progress

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/recordings`; recording.end_time; ready, loading, error, permission, dirty, pending, success, conflict, starting, finalizing, interrupted | [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx) | [Composed screen](workflow-prototype.html?screen=recording-active); [specification](workflow-specification.md#recording-active) | [Desktop EN](workflow-exports/recording-active-cyan-en.jpg), [phone ES](workflow-exports/recording-active-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-parts"></a>
## Parts and playback

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/recordings`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, unsupported, preparing, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [RecordingPlayback.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingPlayback.tsx); [recordings.py](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py) | [Composed screen](workflow-prototype.html?screen=recording-parts); [specification](workflow-specification.md#recording-parts) | [Desktop EN](workflow-exports/recording-parts-cyan-en.jpg), [phone ES](workflow-exports/recording-parts-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-copy"></a>
## Prepare a compatible copy

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/recordings`; conversion.profile; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, failed, ready-copy | [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx) | [Composed screen](workflow-prototype.html?screen=recording-copy); [specification](workflow-specification.md#recording-copy) | [Desktop EN](workflow-exports/recording-copy-cyan-en.jpg), [phone ES](workflow-exports/recording-copy-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-settings"></a>
## Recording settings

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=automation`; recordings.enabled, recordings.max_concurrent, recordings.min_free_bytes, recordings.max_recording_bytes, recordings.retention_enabled, recordings.retention_days; ready, loading, error, permission, dirty, pending, success, conflict, unavailable | [RecordingSettingsFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingSettingsFields.tsx) | [Composed screen](workflow-prototype.html?screen=recording-settings); [specification](workflow-specification.md#recording-settings) | [Desktop EN](workflow-exports/recording-settings-cyan-en.jpg), [phone ES](workflow-exports/recording-settings-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-storage"></a>
## Storage for recordings

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/recordings`; read/control surface; ready, loading, error, permission, low | [RecordingOverview.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingOverview.tsx) | [Composed screen](workflow-prototype.html?screen=recording-storage); [specification](workflow-specification.md#recording-storage) | [Desktop EN](workflow-exports/recording-storage-cyan-en.jpg), [phone ES](workflow-exports/recording-storage-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-cancel"></a>
## Cancel this schedule

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/recordings`; read/control surface; ready, loading, error, permission, pending, success, conflict | [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx) | [Composed screen](workflow-prototype.html?screen=recording-cancel); [specification](workflow-specification.md#recording-cancel) | [Desktop EN](workflow-exports/recording-cancel-cyan-en.jpg), [phone ES](workflow-exports/recording-cancel-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-delete"></a>
## Delete saved files

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/recordings`; read/control surface; ready, loading, error, permission, pending, success, conflict, held | [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx) | [Composed screen](workflow-prototype.html?screen=recording-delete); [specification](workflow-specification.md#recording-delete) | [Desktop EN](workflow-exports/recording-delete-cyan-en.jpg), [phone ES](workflow-exports/recording-delete-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recording-disable"></a>
## Disable all recording

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/recordings`; read/control surface; ready, loading, error, permission, pending, success, conflict | [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx) | [Composed screen](workflow-prototype.html?screen=recording-disable); [specification](workflow-specification.md#recording-disable) | [Desktop EN](workflow-exports/recording-disable-cyan-en.jpg), [phone ES](workflow-exports/recording-disable-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-activate"></a>
## Choose who can use this installation

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; bootstrap.enabled, account.username, account.password, bootstrap.password_confirmation, bootstrap.legacy_token, bootstrap.migrate_legacy_token; ready, loading, error, permission, dirty, pending, success, conflict, blocked | [AccountSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccountSetup.tsx) | [Composed screen](workflow-prototype.html?screen=access-activate); [specification](workflow-specification.md#access-activate) | [Desktop EN](workflow-exports/access-activate-cyan-en.jpg), [phone ES](workflow-exports/access-activate-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-login"></a>
## Sign in

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/watch`; account.username, login.password; ready, loading, error, permission, dirty, pending, success, conflict, expired, denied | [LoginForm.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/LoginForm.tsx) | [Composed screen](workflow-prototype.html?screen=access-login); [specification](workflow-specification.md#access-login) | [Desktop EN](workflow-exports/access-login-cyan-en.jpg), [phone ES](workflow-exports/access-login-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-account"></a>
## Account permissions

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; account.administrator, account.enabled, permissions.live, permissions.channels, permissions.guide, permissions.events, permissions.recordings, permissions.playlists, permissions.cast, permissions.cast_server; ready, loading, error, permission, dirty, pending, success, conflict, last-admin | [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx) | [Composed screen](workflow-prototype.html?screen=access-account); [specification](workflow-specification.md#access-account) | [Desktop EN](workflow-exports/access-account-cyan-en.jpg), [phone ES](workflow-exports/access-account-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-create"></a>
## Create an account

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; account.username, account.password, account.administrator, permissions.live, permissions.channels, permissions.guide, permissions.events, permissions.recordings, permissions.playlists, permissions.cast, permissions.cast_server; ready, loading, error, permission, dirty, pending, success, conflict | [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx) | [Composed screen](workflow-prototype.html?screen=access-create); [specification](workflow-specification.md#access-create) | [Desktop EN](workflow-exports/access-create-cyan-en.jpg), [phone ES](workflow-exports/access-create-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-policy"></a>
## Viewing without signing in

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; public_features.live, public_features.channels, public_features.guide, public_features.events, public_features.cast, policy.public_playlists, policy.local_iptv, policy.local_networks; ready, loading, error, permission, dirty, pending, success, conflict | [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx) | [Composed screen](workflow-prototype.html?screen=access-policy); [specification](workflow-specification.md#access-policy) | [Desktop EN](workflow-exports/access-policy-cyan-en.jpg), [phone ES](workflow-exports/access-policy-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-password"></a>
## Change your password

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; password.current_password, account.password, password.password_confirmation; ready, loading, error, permission, dirty, pending, success, conflict | [PasswordForm.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/PasswordForm.tsx) | [Composed screen](workflow-prototype.html?screen=access-password); [specification](workflow-specification.md#access-password) | [Desktop EN](workflow-exports/access-password-cyan-en.jpg), [phone ES](workflow-exports/access-password-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-sessions"></a>
## Login sessions

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict | [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx) | [Composed screen](workflow-prototype.html?screen=access-sessions); [specification](workflow-specification.md#access-sessions) | [Desktop EN](workflow-exports/access-sessions-cyan-en.jpg), [phone ES](workflow-exports/access-sessions-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-credentials"></a>
## Playback and API credentials

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; credential.label, credential.kind; ready, loading, error, permission, dirty, pending, success, conflict | [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx) | [Composed screen](workflow-prototype.html?screen=access-credentials); [specification](workflow-specification.md#access-credentials) | [Desktop EN](workflow-exports/access-credentials-cyan-en.jpg), [phone ES](workflow-exports/access-credentials-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-secret"></a>
## Save your new credential

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; read/control surface; ready, loading, error, permission, pending, success, conflict, copy-failed | [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx) | [Composed screen](workflow-prototype.html?screen=access-secret); [specification](workflow-specification.md#access-secret) | [Desktop EN](workflow-exports/access-secret-cyan-en.jpg), [phone ES](workflow-exports/access-secret-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-disable"></a>
## Remove account protection

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; access.confirm, access.current_password; ready, loading, error, permission, dirty, pending, success, conflict | [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx) | [Composed screen](workflow-prototype.html?screen=access-disable); [specification](workflow-specification.md#access-disable) | [Desktop EN](workflow-exports/access-disable-cyan-en.jpg), [phone ES](workflow-exports/access-disable-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="access-transport"></a>
## Use a supported connection

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=access`; read/control surface; ready, loading, error, permission | [AccountTransportNotice.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccountTransportNotice.tsx) | [Composed screen](workflow-prototype.html?screen=access-transport); [specification](workflow-specification.md#access-transport) | [Desktop EN](workflow-exports/access-transport-cyan-en.jpg), [phone ES](workflow-exports/access-transport-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="channels"></a>
## TV channels

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/tv-channels`; filter.search, filter.category, filter.status, filter.favorite, filter.country, filter.language, filter.epg, filter.epg_source_id, filter.streams, filter.signal, filter.number, filter.logo_url, filter.website, filter.description, filter.min_number, filter.max_number, filter.min_streams, filter.max_streams, filter.sort, filter.page_size; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [TVChannels.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/TVChannels.tsx); [TVChannelFilters.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelFilters.tsx); [TVChannelsTable.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelsTable.tsx) | [Composed screen](workflow-prototype.html?screen=channels); [specification](workflow-specification.md#channels) | [Desktop EN](workflow-exports/channels-cyan-en.jpg), [phone ES](workflow-exports/channels-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="channel-edit"></a>
## Edit TV channel

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/tv-channels/:id`; tv.name, tv.channel_number, tv.category, tv.is_active, tv.is_favorite, tv.description, tv.logo_url, tv.country, tv.language, tv.website, tv.epg_id, tv.epg_source_id; ready, loading, error, permission, dirty, pending, success, conflict | [TVChannelFormDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelFormDialog.tsx) | [Composed screen](workflow-prototype.html?screen=channel-edit); [specification](workflow-specification.md#channel-edit) | [Desktop EN](workflow-exports/channel-edit-cyan-en.jpg), [phone ES](workflow-exports/channel-edit-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="channel-detail"></a>
## Northlight

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/tv-channels/:id`; read/control surface; ready, loading, error, permission, empty, filtered, partial, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [TVChannelDetail.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/TVChannelDetail.tsx) | [Composed screen](workflow-prototype.html?screen=channel-detail); [specification](workflow-specification.md#channel-detail) | [Desktop EN](workflow-exports/channel-detail-cyan-en.jpg), [phone ES](workflow-exports/channel-detail-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="channel-reorder"></a>
## Reorder all TV channels

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/tv-channels`; read/control surface; ready, loading, error, permission, pending, success, conflict | [TVChannelReorder.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelReorder.tsx) | [Composed screen](workflow-prototype.html?screen=channel-reorder); [specification](workflow-specification.md#channel-reorder) | [Desktop EN](workflow-exports/channel-reorder-cyan-en.jpg), [phone ES](workflow-exports/channel-reorder-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="channel-preferences"></a>
## Preferred streams for Northlight

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/tv-channels`; read/control surface; ready, loading, error, permission, pending, success, conflict | [TVChannelDetail.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/TVChannelDetail.tsx) | [Composed screen](workflow-prototype.html?screen=channel-preferences); [specification](workflow-specification.md#channel-preferences) | [Desktop EN](workflow-exports/channel-preferences-cyan-en.jpg), [phone ES](workflow-exports/channel-preferences-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="streams"></a>
## Streams

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/acestream-channels`; filter.search, filter.category, filter.status, streams.source, streams.group, streams.active, streams.assigned; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [AcestreamChannels.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/AcestreamChannels.tsx); [ChannelFilterBar.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/channels/ChannelFilterBar.tsx) | [Composed screen](workflow-prototype.html?screen=streams); [specification](workflow-specification.md#streams) | [Desktop EN](workflow-exports/streams-cyan-en.jpg), [phone ES](workflow-exports/streams-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="stream-stats"></a>
## Northlight HD · observations

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/acestream-channels`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, unknown, not-found | [StreamStatistics.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/channels/StreamStatistics.tsx); [ChannelActivityLogDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ChannelActivityLogDialog.tsx) | [Composed screen](workflow-prototype.html?screen=stream-stats); [specification](workflow-specification.md#stream-stats) | [Desktop EN](workflow-exports/stream-stats-cyan-en.jpg), [phone ES](workflow-exports/stream-stats-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="stream-edit"></a>
## Add and link a stream

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/acestream-channels`; stream.name, stream.id, stream.tv_channel_id, stream.group, stream.logo, stream.tvg_id, stream.tvg_name, stream.is_active, stream.epg_update_protected, stream.allow_excluded; ready, loading, error, permission, dirty, pending, success, conflict, excluded | [QuickEditDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/QuickEditDialog.tsx); [TVChannelLinkField.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelLinkField.tsx) | [Composed screen](workflow-prototype.html?screen=stream-edit); [specification](workflow-specification.md#stream-edit) | [Desktop EN](workflow-exports/stream-edit-cyan-en.jpg), [phone ES](workflow-exports/stream-edit-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="stream-bulk"></a>
## Bulk stream actions

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/acestream-channels`; bulk.action, bulk.group, bulk.tv_channel_id; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [BulkOperations.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/BulkOperations.tsx); [BatchAssignDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/BatchAssignDialog.tsx) | [Composed screen](workflow-prototype.html?screen=stream-bulk); [specification](workflow-specification.md#stream-bulk) | [Desktop EN](workflow-exports/stream-bulk-cyan-en.jpg), [phone ES](workflow-exports/stream-bulk-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="channel-assign"></a>
## Assign existing streams

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/tv-channels/:id`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict | [BatchAcestreamAssignment.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/BatchAcestreamAssignment.tsx) | [Composed screen](workflow-prototype.html?screen=channel-assign); [specification](workflow-specification.md#channel-assign) | [Desktop EN](workflow-exports/channel-assign-cyan-en.jpg), [phone ES](workflow-exports/channel-assign-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="stream-match"></a>
## Match streams to TV channels

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/tv-channels`; matching.include_similar, matching.assumed_country; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, ambiguous | [TVAutoMatchDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVAutoMatchDialog.tsx) | [Composed screen](workflow-prototype.html?screen=stream-match); [specification](workflow-specification.md#stream-match) | [Desktop EN](workflow-exports/stream-match-cyan-en.jpg), [phone ES](workflow-exports/stream-match-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="channel-delete"></a>
## Delete Northlight?

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/tv-channels`; read/control surface; ready, loading, error, permission, pending, success, conflict | [TVChannelDeleteDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelDeleteDialog.tsx) | [Composed screen](workflow-prototype.html?screen=channel-delete); [specification](workflow-specification.md#channel-delete) | [Desktop EN](workflow-exports/channel-delete-cyan-en.jpg), [phone ES](workflow-exports/channel-delete-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-sources"></a>
## Programme guides

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/epg?tab=sources`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [EPGSourcesTable.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGSourcesTable.tsx) | [Composed screen](workflow-prototype.html?screen=guide-sources); [specification](workflow-specification.md#guide-sources) | [Desktop EN](workflow-exports/guide-sources-cyan-en.jpg), [phone ES](workflow-exports/guide-sources-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-source"></a>
## Edit guide source

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/epg?tab=sources`; epg.name, epg.url, epg.enabled; ready, loading, error, permission, dirty, pending, success, conflict | [EPGSourceDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGSourceDialog.tsx) | [Composed screen](workflow-prototype.html?screen=guide-source); [specification](workflow-specification.md#guide-source) | [Desktop EN](workflow-exports/guide-source-cyan-en.jpg), [phone ES](workflow-exports/guide-source-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-detail"></a>
## Northlight · Sample guide

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/epg/channels/:id`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [EPGChannelDetail.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/EPGChannelDetail.tsx) | [Composed screen](workflow-prototype.html?screen=guide-detail); [specification](workflow-specification.md#guide-detail) | [Desktop EN](workflow-exports/guide-detail-cyan-en.jpg), [phone ES](workflow-exports/guide-detail-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-choice"></a>
## Choose the correct guide source

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/epg?tab=matching`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict | [EPGMatchAnalysisPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGMatchAnalysisPanel.tsx) | [Composed screen](workflow-prototype.html?screen=guide-choice); [specification](workflow-specification.md#guide-choice) | [Desktop EN](workflow-exports/guide-choice-cyan-en.jpg), [phone ES](workflow-exports/guide-choice-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-match"></a>
## Review guide matches

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/epg?tab=matching`; guide.source_id, guide.strictness; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [EPGMatchAnalysisPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGMatchAnalysisPanel.tsx) | [Composed screen](workflow-prototype.html?screen=guide-match); [specification](workflow-specification.md#guide-match) | [Desktop EN](workflow-exports/guide-match-cyan-en.jpg), [phone ES](workflow-exports/guide-match-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-rule"></a>
## Guide matching rule

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/epg/channels/:id`; rule.search_pattern, rule.is_exclusion; ready, loading, error, permission, dirty, pending, success, conflict | [EPGChannelDetail.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/EPGChannelDetail.tsx) | [Composed screen](workflow-prototype.html?screen=guide-rule); [specification](workflow-specification.md#guide-rule) | [Desktop EN](workflow-exports/guide-rule-cyan-en.jpg), [phone ES](workflow-exports/guide-rule-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-auto"></a>
## Automatic exact matching

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=automation`; epg_matching.enabled; ready, loading, error, permission, dirty, pending, success, conflict | [GuideMatchingFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/GuideMatchingFields.tsx) | [Composed screen](workflow-prototype.html?screen=guide-auto); [specification](workflow-specification.md#guide-auto) | [Desktop EN](workflow-exports/guide-auto-cyan-en.jpg), [phone ES](workflow-exports/guide-auto-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-export"></a>
## Export programme guide

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/epg?tab=export`; xml.search_term, xml.favorites_only, xml.days_back, xml.days_forward; ready, loading, error, permission, dirty, pending, success, conflict | [EPGXmlOutputPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGXmlOutputPanel.tsx) | [Composed screen](workflow-prototype.html?screen=guide-export); [specification](workflow-specification.md#guide-export) | [Desktop EN](workflow-exports/guide-export-cyan-en.jpg), [phone ES](workflow-exports/guide-export-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-coverage"></a>
## Guide coverage

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/epg`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [GuideCoverage.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/GuideCoverage.tsx) | [Composed screen](workflow-prototype.html?screen=guide-coverage); [specification](workflow-specification.md#guide-coverage) | [Desktop EN](workflow-exports/guide-coverage-cyan-en.jpg), [phone ES](workflow-exports/guide-coverage-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="playlist"></a>
## Your playlist

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/playlist`; playlist.search, playlist.only_online, playlist.favorites_only, playlist.include_unassigned, playlist.format, playlist.per_source, playlist.include_groups, playlist.exclude_groups; ready, loading, error, permission, dirty, pending, success, conflict, credential, managed, filtered | [PlaylistOptionsForm.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/playlist/PlaylistOptionsForm.tsx); [PlaylistLinkPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/playlist/PlaylistLinkPanel.tsx) | [Composed screen](workflow-prototype.html?screen=playlist); [specification](workflow-specification.md#playlist) | [Desktop EN](workflow-exports/playlist-cyan-en.jpg), [phone ES](workflow-exports/playlist-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="formats"></a>
## Stream link formats

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=links`; format.name, format.pattern, format.is_default, links.add_pid, links.app_id; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [StreamLinkFormatsSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StreamLinkFormatsSection.tsx) | [Composed screen](workflow-prototype.html?screen=formats); [specification](workflow-specification.md#formats) | [Desktop EN](workflow-exports/formats-cyan-en.jpg), [phone ES](workflow-exports/formats-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="format-edit"></a>
## Edit Demo relay

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=links`; format.name, format.pattern; ready, loading, error, permission, dirty, pending, success, conflict | [StreamLinkFormatsSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StreamLinkFormatsSection.tsx) | [Composed screen](workflow-prototype.html?screen=format-edit); [specification](workflow-specification.md#format-edit) | [Desktop EN](workflow-exports/format-edit-cyan-en.jpg), [phone ES](workflow-exports/format-edit-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="source-web"></a>
## Web or playlist source

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=sources`; source.name, source.url, source.url_type, source.enabled, source.scrape_bare_ids; ready, loading, error, permission, dirty, pending, success, conflict, import-failed | [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx) | [Composed screen](workflow-prototype.html?screen=source-web); [specification](workflow-specification.md#source-web) | [Desktop EN](workflow-exports/source-web-cyan-en.jpg), [phone ES](workflow-exports/source-web-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="source-auto"></a>
## Automatic source detection

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=sources`; source.name, source.url, source.url_type, source.enabled, source.scrape_bare_ids; ready, loading, error, permission, dirty, pending, success, conflict, import-failed | [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx) | [Composed screen](workflow-prototype.html?screen=source-auto); [specification](workflow-specification.md#source-auto) | [Desktop EN](workflow-exports/source-auto-cyan-en.jpg), [phone ES](workflow-exports/source-auto-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="source-zeronet"></a>
## ZeroNet source

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=sources`; source.name, source.url, source.url_type, source.enabled, source.scrape_bare_ids; ready, loading, error, permission, dirty, pending, success, conflict, import-failed | [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx) | [Composed screen](workflow-prototype.html?screen=source-zeronet); [specification](workflow-specification.md#source-zeronet) | [Desktop EN](workflow-exports/source-zeronet-cyan-en.jpg), [phone ES](workflow-exports/source-zeronet-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="source-ipfs"></a>
## IPFS source

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=sources`; source.name, source.url, source.url_type, source.enabled, source.scrape_bare_ids; ready, loading, error, permission, dirty, pending, success, conflict, import-failed | [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx) | [Composed screen](workflow-prototype.html?screen=source-ipfs); [specification](workflow-specification.md#source-ipfs) | [Desktop EN](workflow-exports/source-ipfs-cyan-en.jpg), [phone ES](workflow-exports/source-ipfs-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="source-provider"></a>
## Built-in broadcaster

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=sources`; source.provider, source.name, source.url_type, source.url, source.enabled, source.scrape_bare_ids; ready, loading, error, permission, dirty, pending, success, conflict, import-failed | [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx) | [Composed screen](workflow-prototype.html?screen=source-provider); [specification](workflow-specification.md#source-provider) | [Desktop EN](workflow-exports/source-provider-cyan-en.jpg), [phone ES](workflow-exports/source-provider-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="source-results"></a>
## Import result

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper`; read/control surface; ready, loading, error, permission, waiting, partial | [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx) | [Composed screen](workflow-prototype.html?screen=source-results); [specification](workflow-specification.md#source-results) | [Desktop EN](workflow-exports/source-results-cyan-en.jpg), [phone ES](workflow-exports/source-results-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="source-remove"></a>
## Remove Family channels?

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper`; source.delete_streams; ready, loading, error, permission, dirty, pending, success, conflict | [DeleteSourceDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/scraper/DeleteSourceDialog.tsx) | [Composed screen](workflow-prototype.html?screen=source-remove); [specification](workflow-specification.md#source-remove) | [Desktop EN](workflow-exports/source-remove-cyan-en.jpg), [phone ES](workflow-exports/source-remove-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="sources-orphans"></a>
## Streams without a saved source

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict | [OrphanedSourcesDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/scraper/OrphanedSourcesDialog.tsx) | [Composed screen](workflow-prototype.html?screen=sources-orphans); [specification](workflow-specification.md#sources-orphans) | [Desktop EN](workflow-exports/sources-orphans-cyan-en.jpg), [phone ES](workflow-exports/sources-orphans-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="w3u"></a>
## Review W3U catalogue

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=w3u`; catalogue.url; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, expired | [Catalogues.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Catalogues.tsx) | [Composed screen](workflow-prototype.html?screen=w3u); [specification](workflow-specification.md#w3u) | [Desktop EN](workflow-exports/w3u-cyan-en.jpg), [phone ES](workflow-exports/w3u-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="w3u-save"></a>
## Save reviewed catalogue

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=w3u`; catalogue.name, catalogue.mode, catalogue.confirm_live, catalogue.refresh_enabled; ready, loading, error, permission, dirty, pending, success, conflict | [Catalogues.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Catalogues.tsx) | [Composed screen](workflow-prototype.html?screen=w3u-save); [specification](workflow-specification.md#w3u-save) | [Desktop EN](workflow-exports/w3u-save-cyan-en.jpg), [phone ES](workflow-exports/w3u-save-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="w3u-detail"></a>
## Catalogue entry details

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=w3u`; catalogue.search, catalogue.content_type, catalogue.show, catalogue.artwork; ready, loading, error, permission, dirty, pending, success, conflict | [Catalogues.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Catalogues.tsx) | [Composed screen](workflow-prototype.html?screen=w3u-detail); [specification](workflow-specification.md#w3u-detail) | [Desktop EN](workflow-exports/w3u-detail-cyan-en.jpg), [phone ES](workflow-exports/w3u-detail-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="w3u-folder"></a>
## Assign a catalogue folder

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=w3u`; folder.tv_channel_id, folder.create_name, folder.reassign; ready, loading, error, permission, dirty, pending, success, conflict | [FolderMatchDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/catalogues/FolderMatchDialog.tsx) | [Composed screen](workflow-prototype.html?screen=w3u-folder); [specification](workflow-specification.md#w3u-folder) | [Desktop EN](workflow-exports/w3u-folder-cyan-en.jpg), [phone ES](workflow-exports/w3u-folder-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="saved-search"></a>
## Saved search

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=searches`; saved_search.name, saved_search.query, saved_search.category, saved_search.refresh_enabled; ready, loading, error, permission, dirty, pending, success, conflict | [SavedSearchDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/imports/SavedSearchDialog.tsx) | [Composed screen](workflow-prototype.html?screen=saved-search); [specification](workflow-specification.md#saved-search) | [Desktop EN](workflow-exports/saved-search-cyan-en.jpg), [phone ES](workflow-exports/saved-search-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="saved-search-preview"></a>
## Preview a saved search

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=searches`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict | [SavedSearches.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/imports/SavedSearches.tsx) | [Composed screen](workflow-prototype.html?screen=saved-search-preview); [specification](workflow-specification.md#saved-search-preview) | [Desktop EN](workflow-exports/saved-search-preview-cyan-en.jpg), [phone ES](workflow-exports/saved-search-preview-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="exclusion"></a>
## Import exclusion rule

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper?tab=exclusions`; exclusion.kind, exclusion.value, exclusion.enabled, exclusion.note; ready, loading, error, permission, dirty, pending, success, conflict | [ImportExclusions.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/imports/ImportExclusions.tsx) | [Composed screen](workflow-prototype.html?screen=exclusion); [specification](workflow-specification.md#exclusion) | [Desktop EN](workflow-exports/exclusion-cyan-en.jpg), [phone ES](workflow-exports/exclusion-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="search"></a>
## Find new streams

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/search`; search.query, search.category; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, engine | [Search.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Search.tsx) | [Composed screen](workflow-prototype.html?screen=search); [specification](workflow-specification.md#search) | [Desktop EN](workflow-exports/search-cyan-en.jpg), [phone ES](workflow-exports/search-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="search-add-link"></a>
## Add and link Northlight HD

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/search`; add_link.tv_channel_id; ready, loading, error, permission, dirty, pending, success, conflict, unresolved, excluded, catalogue-unavailable | [AddAndLinkDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/search/AddAndLinkDialog.tsx) | [Composed screen](workflow-prototype.html?screen=search-add-link); [specification](workflow-specification.md#search-add-link) | [Desktop EN](workflow-exports/search-add-link-cyan-en.jpg), [phone ES](workflow-exports/search-add-link-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="helper-installed"></a>
## Test a source recipe

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper/builder`; fetch.url, fetch.url_type; ready, loading, error, permission, dirty, pending, success, conflict | [ExtractionBuilder.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/ExtractionBuilder.tsx) | [Composed screen](workflow-prototype.html?screen=helper-installed); [specification](workflow-specification.md#helper-installed) | [Desktop EN](workflow-exports/helper-installed-cyan-en.jpg), [phone ES](workflow-exports/helper-installed-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="helper-standalone"></a>
## Build a recipe offline

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `standalone helper`; sample.file, sample.text, recipe.catalogue, recipe.pasted; ready, loading, error, permission, dirty, pending, success, conflict | [standalone.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/standalone.tsx) | [Composed screen](workflow-prototype.html?screen=helper-standalone); [specification](workflow-specification.md#helper-standalone) | [Desktop EN](workflow-exports/helper-standalone-cyan-en.jpg), [phone ES](workflow-exports/helper-standalone-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="helper-html"></a>
## Pick fields in HTML

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper/builder`; recipe.name, recipe.version, recipe.mode, recipe.records, recipe.fields.name.selector, recipe.fields.name.attribute, recipe.fields.name.pattern, recipe.fields.id.selector, recipe.fields.id.attribute, recipe.fields.id.pattern, recipe.fields.group.selector, recipe.fields.group.attribute, recipe.fields.group.pattern, recipe.fields.logo.selector, recipe.fields.logo.attribute, recipe.fields.logo.pattern, recipe.fields.epg_id.selector, recipe.fields.epg_id.attribute, recipe.fields.epg_id.pattern, recipe.flags; ready, loading, error, permission, dirty, pending, success, conflict, timeout, invalid | [RecipeFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeFields.tsx) | [Composed screen](workflow-prototype.html?screen=helper-html); [specification](workflow-specification.md#helper-html) | [Desktop EN](workflow-exports/helper-html-cyan-en.jpg), [phone ES](workflow-exports/helper-html-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="helper-json"></a>
## Read fields from JSON

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper/builder`; recipe.name, recipe.version, recipe.mode, recipe.records, recipe.fields.name.path, recipe.fields.name.pattern, recipe.fields.id.path, recipe.fields.id.pattern, recipe.fields.group.path, recipe.fields.group.pattern, recipe.fields.logo.path, recipe.fields.logo.pattern, recipe.fields.epg_id.path, recipe.fields.epg_id.pattern, recipe.flags; ready, loading, error, permission, dirty, pending, success, conflict, timeout, invalid | [RecipeFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeFields.tsx) | [Composed screen](workflow-prototype.html?screen=helper-json); [specification](workflow-specification.md#helper-json) | [Desktop EN](workflow-exports/helper-json-cyan-en.jpg), [phone ES](workflow-exports/helper-json-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="helper-regex"></a>
## Read paired text records

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper/builder`; recipe.name, recipe.version, recipe.mode, recipe.records, recipe.fields.name.pattern, recipe.fields.id.pattern, recipe.fields.group.pattern, recipe.fields.logo.pattern, recipe.fields.epg_id.pattern, recipe.flags; ready, loading, error, permission, dirty, pending, success, conflict, timeout, invalid | [RecipeFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeFields.tsx) | [Composed screen](workflow-prototype.html?screen=helper-regex); [specification](workflow-specification.md#helper-regex) | [Desktop EN](workflow-exports/helper-regex-cyan-en.jpg), [phone ES](workflow-exports/helper-regex-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="helper-manual"></a>
## Select fields manually

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper/builder`; manual.target, manual.selection; ready, loading, error, permission, dirty, pending, success, conflict | [RecipeBuilder.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeBuilder.tsx) | [Composed screen](workflow-prototype.html?screen=helper-manual); [specification](workflow-specification.md#helper-manual) | [Desktop EN](workflow-exports/helper-manual-cyan-en.jpg), [phone ES](workflow-exports/helper-manual-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="helper-large"></a>
## This sample is too large to draw safely

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper/builder`; read/control surface; ready, loading, error, permission, empty, filtered, partial, too-large | [VisualPicker.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/VisualPicker.tsx) | [Composed screen](workflow-prototype.html?screen=helper-large); [specification](workflow-specification.md#helper-large) | [Desktop EN](workflow-exports/helper-large-cyan-en.jpg), [phone ES](workflow-exports/helper-large-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="helper-results"></a>
## Review extraction results

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/scraper/builder`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, stale | [RecipeResults.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeResults.tsx) | [Composed screen](workflow-prototype.html?screen=helper-results); [specification](workflow-specification.md#helper-results) | [Desktop EN](workflow-exports/helper-results-cyan-en.jpg), [phone ES](workflow-exports/helper-results-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="dashboard"></a>
## Watch

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/`; read/control surface; ready, loading, error, permission, first-use, partial, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [TVDashboard.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/TVDashboard.tsx) | [Composed screen](workflow-prototype.html?screen=dashboard); [specification](workflow-specification.md#dashboard) | [Desktop EN](workflow-exports/dashboard-cyan-en.jpg), [phone ES](workflow-exports/dashboard-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="live"></a>
## Watch

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/live-tv`; live.list, live.q, live.online_only; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, refreshing, failed, stalled, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [LiveTV.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/LiveTV.tsx) | [Composed screen](workflow-prototype.html?screen=live); [specification](workflow-specification.md#live) | [Desktop EN](workflow-exports/live-cyan-en.jpg), [phone ES](workflow-exports/live-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="player-tracks"></a>
## Playback options

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `player dialog`; player.audio_index, player.subtitle_index, player.source; ready, loading, error, permission, dirty, pending, success, conflict, capacity | [StreamPlayerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/StreamPlayerDialog.tsx) | [Composed screen](workflow-prototype.html?screen=player-tracks); [specification](workflow-specification.md#player-tracks) | [Desktop EN](workflow-exports/player-tracks-cyan-en.jpg), [phone ES](workflow-exports/player-tracks-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="viewer"></a>
## Your viewing access

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/watch`; read/control surface; ready, loading, error, permission, empty, filtered, partial, denied | [Watch.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Watch.tsx) | [Composed screen](workflow-prototype.html?screen=viewer); [specification](workflow-specification.md#viewer) | [Desktop EN](workflow-exports/viewer-cyan-en.jpg), [phone ES](workflow-exports/viewer-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="events"></a>
## Event agenda

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events`; agenda.zone, agenda.sports, agenda.competitions, agenda.teams, agenda.following, agenda.when, agenda.day, agenda.search, agenda.window_days, agenda.sport, agenda.competition, agenda.source; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [EventAgenda.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventAgenda.tsx); [Events.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Events.tsx) | [Composed screen](workflow-prototype.html?screen=events); [specification](workflow-specification.md#events) | [Desktop EN](workflow-exports/events-cyan-en.jpg), [phone ES](workflow-exports/events-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="event-detail"></a>
## Northlight Cup

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events?event=demo&zone=Europe/Madrid`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, unknown, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [EventDetails.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventDetails.tsx) | [Composed screen](workflow-prototype.html?screen=event-detail); [specification](workflow-specification.md#event-detail) | [Desktop EN](workflow-exports/event-detail-cyan-en.jpg), [phone ES](workflow-exports/event-detail-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="event-provider"></a>
## Add provider events

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events`; provider.provider, provider.feeds, provider.football_competitions, provider.league, provider.season, provider.window_days, provider.timezone, provider.interests.sports, provider.interests.competitions, provider.interests.teams; ready, loading, error, permission, dirty, pending, success, conflict | [EventProviderFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventProviderFields.tsx) | [Composed screen](workflow-prototype.html?screen=event-provider); [specification](workflow-specification.md#event-provider) | [Desktop EN](workflow-exports/event-provider-cyan-en.jpg), [phone ES](workflow-exports/event-provider-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="event-import"></a>
## Add events

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events`; event.input, event.title, event.sport, event.competition, event.starts_at, event.timezone, event.broadcaster, event.url, event.schedule_url, event.format, event.json, event.timeout_seconds; ready, loading, error, permission, dirty, pending, success, conflict | [EventImportPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventImportPanel.tsx) | [Composed screen](workflow-prototype.html?screen=event-import); [specification](workflow-specification.md#event-import) | [Desktop EN](workflow-exports/event-import-cyan-en.jpg), [phone ES](workflow-exports/event-import-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="event-review"></a>
## Review new events

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events`; event.refresh_source; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [EventImportPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventImportPanel.tsx) | [Composed screen](workflow-prototype.html?screen=event-review); [specification](workflow-specification.md#event-review) | [Desktop EN](workflow-exports/event-review-cyan-en.jpg), [phone ES](workflow-exports/event-review-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="event-correct"></a>
## Correct Northlight Cup

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events?event=demo`; event.title, event.sport, event.competition, event.starts_at, event.timezone, event.participants, event.ends_at, event.time_notes, event.state; ready, loading, error, permission, dirty, pending, success, conflict | [EventDetails.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventDetails.tsx) | [Composed screen](workflow-prototype.html?screen=event-correct); [specification](workflow-specification.md#event-correct) | [Desktop EN](workflow-exports/event-correct-cyan-en.jpg), [phone ES](workflow-exports/event-correct-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="event-mapping"></a>
## Link the broadcaster Atelier

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events?event=demo`; broadcast.apply_to_source, broadcast.mode, broadcast.target; ready, loading, error, permission, dirty, pending, success, conflict | [EventBroadcastMapper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventBroadcastMapper.tsx) | [Composed screen](workflow-prototype.html?screen=event-mapping); [specification](workflow-specification.md#event-mapping) | [Desktop EN](workflow-exports/event-mapping-cyan-en.jpg), [phone ES](workflow-exports/event-mapping-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="event-overlay"></a>
## Review XMLTV overlay

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events?event=demo`; overlay.broadcast_id, overlay.ends_at; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [EventGuideOverlay.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventGuideOverlay.tsx) | [Composed screen](workflow-prototype.html?screen=event-overlay); [specification](workflow-specification.md#event-overlay) | [Desktop EN](workflow-exports/event-overlay-cyan-en.jpg), [phone ES](workflow-exports/event-overlay-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="event-sources"></a>
## Event sources and retention

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events`; events.ended_days, events.archived_days; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [EventSourcesPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventSourcesPanel.tsx) | [Composed screen](workflow-prototype.html?screen=event-sources); [specification](workflow-specification.md#event-sources) | [Desktop EN](workflow-exports/event-sources-cyan-en.jpg), [phone ES](workflow-exports/event-sources-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="connections"></a>
## Where would you like to watch?

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `proposed orientation layer`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [IntegrationPage.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/IntegrationPage.tsx) | [Composed screen](workflow-prototype.html?screen=connections); [specification](workflow-specification.md#connections) | [Desktop EN](workflow-exports/connections-cyan-en.jpg), [phone ES](workflow-exports/connections-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="browser-player"></a>
## Browser player

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/web-player`; read/control surface; ready, loading, error, permission, empty, filtered, partial, unavailable | [WebPlayerSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/WebPlayerSection.tsx) | [Composed screen](workflow-prototype.html?screen=browser-player); [specification](workflow-specification.md#browser-player) | [Desktop EN](workflow-exports/browser-player-cyan-en.jpg), [phone ES](workflow-exports/browser-player-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="public-address"></a>
## Address for players

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/public-address`; address.public_base_url; ready, loading, error, permission, dirty, pending, success, conflict | [PublicAddressSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/PublicAddressSection.tsx) | [Composed screen](workflow-prototype.html?screen=public-address); [specification](workflow-specification.md#public-address) | [Desktop EN](workflow-exports/public-address-cyan-en.jpg), [phone ES](workflow-exports/public-address-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="casting"></a>
## TV casting

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/tv-casting`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, denied | [TvCasting.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/integrations/TvCasting.tsx) | [Composed screen](workflow-prototype.html?screen=casting); [specification](workflow-specification.md#casting) | [Desktop EN](workflow-exports/casting-cyan-en.jpg), [phone ES](workflow-exports/casting-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="casting-settings"></a>
## Casting settings

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/tv-casting`; cast.compatibility_conversion, cast.cast_media_url, cast.home_networks, cast.remote_casting; ready, loading, error, permission, dirty, pending, success, conflict | [TvCasting.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/integrations/TvCasting.tsx) | [Composed screen](workflow-prototype.html?screen=casting-settings); [specification](workflow-specification.md#casting-settings) | [Desktop EN](workflow-exports/casting-settings-cyan-en.jpg), [phone ES](workflow-exports/casting-settings-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="casting-trust"></a>
## Public HTTPS at home

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/tv-casting`; cast.trust_home; ready, loading, error, permission, dirty, pending, success, conflict | [TvCasting.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/integrations/TvCasting.tsx) | [Composed screen](workflow-prototype.html?screen=casting-trust); [specification](workflow-specification.md#casting-trust) | [Desktop EN](workflow-exports/casting-trust-cyan-en.jpg), [phone ES](workflow-exports/casting-trust-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="casting-control"></a>
## Living room DEMO

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `player casting options`; cast.compatibility, cast.volume; ready, loading, error, permission, dirty, pending, success, conflict, ownership-lost, recording-priority | [CastControls.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/CastControls.tsx) | [Composed screen](workflow-prototype.html?screen=casting-control); [specification](workflow-specification.md#casting-control) | [Desktop EN](workflow-exports/casting-control-cyan-en.jpg), [phone ES](workflow-exports/casting-control-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="remote-player"></a>
## Set up VLC or Kodi

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/remote-players`; remote.name, remote.kind, remote.host, remote.port, remote.username, remote.password, remote.base_url_id; ready, loading, error, permission, dirty, pending, success, conflict | [RemotePlayerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/RemotePlayerDialog.tsx) | [Composed screen](workflow-prototype.html?screen=remote-player); [specification](workflow-specification.md#remote-player) | [Desktop EN](workflow-exports/remote-player-cyan-en.jpg), [phone ES](workflow-exports/remote-player-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="remote-android"></a>
## Pair VLC Android

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/remote-players`; android.code; ready, loading, error, permission, dirty, pending, success, conflict, expired, changed-host | [RemotePlayerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/RemotePlayerDialog.tsx) | [Composed screen](workflow-prototype.html?screen=remote-android); [specification](workflow-specification.md#remote-android) | [Desktop EN](workflow-exports/remote-android-cyan-en.jpg), [phone ES](workflow-exports/remote-android-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="remote-discovery"></a>
## Find remote players

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/remote-players`; scan.cidr, scan.ports, scan.timeout_ms; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [FindPlayersDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/FindPlayersDialog.tsx) | [Composed screen](workflow-prototype.html?screen=remote-discovery); [specification](workflow-specification.md#remote-discovery) | [Desktop EN](workflow-exports/remote-discovery-cyan-en.jpg), [phone ES](workflow-exports/remote-discovery-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="remote-control"></a>
## Send to a player

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `PlayOnMenu`; remote.command, remote.volume; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, denied, handoff | [PlayOnMenu.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/PlayOnMenu.tsx) | [Composed screen](workflow-prototype.html?screen=remote-control); [specification](workflow-specification.md#remote-control) | [Desktop EN](workflow-exports/remote-control-cyan-en.jpg), [phone ES](workflow-exports/remote-control-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="media-server"></a>
## Connect a media server

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/media-servers`; media.kind, media.name, media.base_url, media.api_key, media.tuner_mode, media.auto_refresh, media.enabled; ready, loading, error, permission, dirty, pending, success, conflict | [MediaServerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/MediaServerDialog.tsx) | [Composed screen](workflow-prototype.html?screen=media-server); [specification](workflow-specification.md#media-server) | [Desktop EN](workflow-exports/media-server-cyan-en.jpg), [phone ES](workflow-exports/media-server-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="tuner"></a>
## Tuner settings

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/media-servers`; tuner.friendly_name, tuner.tuner_count, tuner.max_channels, tuner.source_start_seconds, tuner.startup_budget_seconds, tuner.only_online, tuner.hide_unusable, tuner.plex_compatible_audio, tuner.experimental_transcoding; ready, loading, error, permission, dirty, pending, success, conflict | [MediaServersSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/MediaServersSection.tsx) | [Composed screen](workflow-prototype.html?screen=tuner); [specification](workflow-specification.md#tuner) | [Desktop EN](workflow-exports/tuner-cyan-en.jpg), [phone ES](workflow-exports/tuner-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="telegram-auth"></a>
## Authorize Telegram sources

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/telegram`; telegram.admin_token, telegram.api_id, telegram.api_hash, telegram.phone; ready, loading, error, permission, dirty, pending, success, conflict, unavailable, flood | [TelegramSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/TelegramSection.tsx) | [Composed screen](workflow-prototype.html?screen=telegram-auth); [specification](workflow-specification.md#telegram-auth) | [Desktop EN](workflow-exports/telegram-auth-cyan-en.jpg), [phone ES](workflow-exports/telegram-auth-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="telegram-code"></a>
## Complete Telegram sign-in

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/telegram`; telegram.code, telegram.password; ready, loading, error, permission, dirty, pending, success, conflict | [TelegramSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/TelegramSection.tsx) | [Composed screen](workflow-prototype.html?screen=telegram-code); [specification](workflow-specification.md#telegram-code) | [Desktop EN](workflow-exports/telegram-code-cyan-en.jpg), [phone ES](workflow-exports/telegram-code-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="telegram-source"></a>
## Telegram source

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/integrations/telegram`; telegram_source.name, telegram_source.chat_id, telegram_source.topic_id, telegram_source.username, telegram_source.sender_ids, telegram_source.include_forwards, telegram_source.sender_rule, telegram_source.filter_mode, telegram_source.include, telegram_source.exclude, telegram_source.bare_ids, telegram_source.history_count, telegram_source.history_since, telegram_source.enabled; ready, loading, error, permission, dirty, pending, success, conflict | [TelegramSourceEditor.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/TelegramSourceEditor.tsx) | [Composed screen](workflow-prototype.html?screen=telegram-source); [specification](workflow-specification.md#telegram-source) | [Desktop EN](workflow-exports/telegram-source-cyan-en.jpg), [phone ES](workflow-exports/telegram-source-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="notifications"></a>
## Notifications

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=automation`; notifications.url; ready, loading, error, permission, dirty, pending, success, conflict, masked-invalid | [NotificationsSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/NotificationsSection.tsx) | [Composed screen](workflow-prototype.html?screen=notifications); [specification](workflow-specification.md#notifications) | [Desktop EN](workflow-exports/notifications-cyan-en.jpg), [phone ES](workflow-exports/notifications-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="warp"></a>
## WARP

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/warp`; warp.mode, warp.license_key; ready, loading, error, permission, dirty, pending, success, conflict | [WARP.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/WARP.tsx) | [Composed screen](workflow-prototype.html?screen=warp); [specification](workflow-specification.md#warp) | [Desktop EN](workflow-exports/warp-cyan-en.jpg), [phone ES](workflow-exports/warp-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="warp-exclusions"></a>
## WARP excluded hosts

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/warp`; warp.hosts; ready, loading, error, permission, dirty, pending, success, conflict, partial | [WarpExclusionsSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/WarpExclusionsSection.tsx) | [Composed screen](workflow-prototype.html?screen=warp-exclusions); [specification](workflow-specification.md#warp-exclusions) | [Desktop EN](workflow-exports/warp-exclusions-cyan-en.jpg), [phone ES](workflow-exports/warp-exclusions-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="warp-startup"></a>
## WARP at startup

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/warp`; runtime.ENABLE_WARP, runtime.WARP_DNS_ONLY, runtime.WARP_ENABLE_NAT, runtime.WARP_FORCE_IPV4; ready, loading, error, permission, dirty, pending, success, conflict | [WarpStartupSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/WarpStartupSection.tsx) | [Composed screen](workflow-prototype.html?screen=warp-startup); [specification](workflow-specification.md#warp-startup) | [Desktop EN](workflow-exports/warp-startup-cyan-en.jpg), [phone ES](workflow-exports/warp-startup-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="settings"></a>
## Settings

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [Settings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Settings.tsx) | [Composed screen](workflow-prototype.html?screen=settings); [specification](workflow-specification.md#settings) | [Desktop EN](workflow-exports/settings-cyan-en.jpg), [phone ES](workflow-exports/settings-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="playback-settings"></a>
## Playback settings

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=playback`; engine.url, routing.use_acexy, routing.acexy_url; ready, loading, error, permission, dirty, pending, success, conflict | [PlaybackRoutingFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/PlaybackRoutingFields.tsx) | [Composed screen](workflow-prototype.html?screen=playback-settings); [specification](workflow-specification.md#playback-settings) | [Desktop EN](workflow-exports/playback-settings-cyan-en.jpg), [phone ES](workflow-exports/playback-settings-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="automation"></a>
## Background updates

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=automation`; schedule.rescrape_interval, schedule.epg_refresh_interval, schedule.channel_status_interval, checker.use_dedicated, checker.url, checks.scope; ready, loading, error, permission, dirty, pending, success, conflict | [Settings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Settings.tsx) | [Composed screen](workflow-prototype.html?screen=automation); [specification](workflow-specification.md#automation) | [Desktop EN](workflow-exports/automation-cyan-en.jpg), [phone ES](workflow-exports/automation-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="schedule-anchors"></a>
## Schedule start times

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=automation`; anchors.timezone, anchors.url_scraping, anchors.epg_refresh, anchors.channel_status, anchors.offline_stream_cleanup; ready, loading, error, permission, dirty, pending, success, conflict | [ScheduleAnchorFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ScheduleAnchorFields.tsx) | [Composed screen](workflow-prototype.html?screen=schedule-anchors); [specification](workflow-specification.md#schedule-anchors) | [Desktop EN](workflow-exports/schedule-anchors-cyan-en.jpg), [phone ES](workflow-exports/schedule-anchors-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="offline-cleanup"></a>
## Offline stream cleanup

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=automation`; offline.enabled, offline.offline_days, offline.interval_days, offline.remove_linked, offline.rescrape; ready, loading, error, permission, dirty, pending, success, conflict, deferred, refresh-failed | [OfflineCleanupFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/settings/OfflineCleanupFields.tsx) | [Composed screen](workflow-prototype.html?screen=offline-cleanup); [specification](workflow-specification.md#offline-cleanup) | [Desktop EN](workflow-exports/offline-cleanup-cyan-en.jpg), [phone ES](workflow-exports/offline-cleanup-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="network"></a>
## Network settings

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/settings?tab=network`; read/control surface; ready, loading, error, permission | [NetworkSettingsFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/settings/NetworkSettingsFields.tsx) | [Composed screen](workflow-prototype.html?screen=network); [specification](workflow-specification.md#network) | [Desktop EN](workflow-exports/network-cyan-en.jpg), [phone ES](workflow-exports/network-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="system"></a>
## System status

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/system`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [SystemDashboard.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/SystemDashboard.tsx) | [Composed screen](workflow-prototype.html?screen=system); [specification](workflow-specification.md#system) | [Desktop EN](workflow-exports/system-cyan-en.jpg), [phone ES](workflow-exports/system-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="services"></a>
## Service controls

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/system`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, external | [ServicesPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ServicesPanel.tsx) | [Composed screen](workflow-prototype.html?screen=services); [specification](workflow-specification.md#services) | [Desktop EN](workflow-exports/services-cyan-en.jpg), [phone ES](workflow-exports/services-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="jobs"></a>
## Scheduled job history

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/system`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [ScheduledJobs.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/overview/ScheduledJobs.tsx) | [Composed screen](workflow-prototype.html?screen=jobs); [specification](workflow-specification.md#jobs) | [Desktop EN](workflow-exports/jobs-cyan-en.jpg), [phone ES](workflow-exports/jobs-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="job-detail"></a>
## Job run details

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/system`; read/control surface; ready, loading, error, permission | [ScheduledJobs.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/overview/ScheduledJobs.tsx) | [Composed screen](workflow-prototype.html?screen=job-detail); [specification](workflow-specification.md#job-detail) | [Desktop EN](workflow-exports/job-detail-cyan-en.jpg), [phone ES](workflow-exports/job-detail-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="storage"></a>
## Storage details

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/system`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict | [StoragePanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/overview/StoragePanel.tsx) | [Composed screen](workflow-prototype.html?screen=storage); [specification](workflow-specification.md#storage) | [Desktop EN](workflow-exports/storage-cyan-en.jpg), [phone ES](workflow-exports/storage-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="diagnostics"></a>
## Logs and diagnostics

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/system`; read/control surface; ready, loading, error, permission, pending, success, conflict, denied, partial | [DiagnosticsDownload.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/DiagnosticsDownload.tsx) | [Composed screen](workflow-prototype.html?screen=diagnostics); [specification](workflow-specification.md#diagnostics) | [Desktop EN](workflow-exports/diagnostics-cyan-en.jpg), [phone ES](workflow-exports/diagnostics-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="setup"></a>
## Start with channels

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/setup`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict | [Setup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Setup.tsx) | [Composed screen](workflow-prototype.html?screen=setup); [specification](workflow-specification.md#setup) | [Desktop EN](workflow-exports/setup-cyan-en.jpg), [phone ES](workflow-exports/setup-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="startup"></a>
## Starting AceStream Scraper

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `outer startup gate`; read/control surface; ready, loading, error, permission, deferred, connection, token | [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx) | [Composed screen](workflow-prototype.html?screen=startup); [specification](workflow-specification.md#startup) | [Desktop EN](workflow-exports/startup-cyan-en.jpg), [phone ES](workflow-exports/startup-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recovery"></a>
## Startup needs attention

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `startup failure gate`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, busy, interrupted | [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx) | [Composed screen](workflow-prototype.html?screen=recovery); [specification](workflow-specification.md#recovery) | [Desktop EN](workflow-exports/recovery-cyan-en.jpg), [phone ES](workflow-exports/recovery-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recovery-readable"></a>
## Recover readable catalogue

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `startup recovery`; recovery.confirm; ready, loading, error, permission, dirty, pending, success, conflict | [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx) | [Composed screen](workflow-prototype.html?screen=recovery-readable); [specification](workflow-specification.md#recovery-readable) | [Desktop EN](workflow-exports/recovery-readable-cyan-en.jpg), [phone ES](workflow-exports/recovery-readable-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recovery-fresh"></a>
## Start a fresh catalogue

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `startup recovery`; recovery.confirm; ready, loading, error, permission, dirty, pending, success, conflict | [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx) | [Composed screen](workflow-prototype.html?screen=recovery-fresh); [specification](workflow-specification.md#recovery-fresh) | [Desktop EN](workflow-exports/recovery-fresh-cyan-en.jpg), [phone ES](workflow-exports/recovery-fresh-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recovery-result"></a>
## Recovery result

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `startup recovery`; read/control surface; ready, loading, error, permission, failed | [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx) | [Composed screen](workflow-prototype.html?screen=recovery-result); [specification](workflow-specification.md#recovery-result) | [Desktop EN](workflow-exports/recovery-result-cyan-en.jpg), [phone ES](workflow-exports/recovery-result-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="preferences"></a>
## Language and appearance

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `shared shell preferences`; preference.language, preference.theme; ready, loading, error, permission, dirty, pending, success, conflict, storage-failed | [AppShell.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/layout/AppShell.tsx) | [Composed screen](workflow-prototype.html?screen=preferences); [specification](workflow-specification.md#preferences) | [Desktop EN](workflow-exports/preferences-cyan-en.jpg), [phone ES](workflow-exports/preferences-cyan-es.jpg); [run](verification-review-06.md) | #317: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="notices"></a>
## Notices and session feedback

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `shared shell`; legacy.token; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [ApiTokenNotice.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ApiTokenNotice.tsx) | [Composed screen](workflow-prototype.html?screen=notices); [specification](workflow-specification.md#notices) | [Desktop EN](workflow-exports/notices-cyan-en.jpg), [phone ES](workflow-exports/notices-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="not-found"></a>
## This page is not available

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `*`; read/control surface; ready, loading, error, permission | [NotFound.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/NotFound.tsx) | [Composed screen](workflow-prototype.html?screen=not-found); [specification](workflow-specification.md#not-found) | [Desktop EN](workflow-exports/not-found-cyan-en.jpg), [phone ES](workflow-exports/not-found-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="changelog"></a>
## What changed

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/changelog`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [Changelog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Changelog.tsx) | [Composed screen](workflow-prototype.html?screen=changelog); [specification](workflow-specification.md#changelog) | [Desktop EN](workflow-exports/changelog-cyan-en.jpg), [phone ES](workflow-exports/changelog-cyan-es.jpg); [run](verification-review-06.md) | #322: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="unsaved"></a>
## Leave with unsaved changes?

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `shared dirty guard`; draft.source_name; ready, loading, error, permission, dirty, pending, success, conflict | [ConfirmDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ConfirmDialog.tsx) | [Composed screen](workflow-prototype.html?screen=unsaved); [specification](workflow-specification.md#unsaved) | [Desktop EN](workflow-exports/unsaved-cyan-en.jpg), [phone ES](workflow-exports/unsaved-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="runtime-playback"></a>
## Playback runtime

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/setup · Connection settings (advanced)`; runtime.ACE_ENGINE_URL, runtime.ACE_CHECK_ENGINE_URL, runtime.PLAYER_MAX_SESSIONS, runtime.PLAYER_START_TIMEOUT_SECONDS; ready, loading, error, permission, dirty, pending, success, conflict, managed | [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json) | [Composed screen](workflow-prototype.html?screen=runtime-playback); [specification](workflow-specification.md#runtime-playback) | [Desktop EN](workflow-exports/runtime-playback-cyan-en.jpg), [phone ES](workflow-exports/runtime-playback-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="runtime-network"></a>
## Network runtime

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/setup · Connection settings (advanced)`; runtime.PUBLIC_BASE_URL, runtime.ALLOW_PRIVATE_SCRAPE_TARGETS, runtime.TUNER_ALLOWED_NETWORKS, runtime.FORWARDED_ALLOW_IPS, runtime.CORS_ORIGINS; ready, loading, error, permission, dirty, pending, success, conflict, managed | [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json) | [Composed screen](workflow-prototype.html?screen=runtime-network); [specification](workflow-specification.md#runtime-network) | [Desktop EN](workflow-exports/runtime-network-cyan-en.jpg), [phone ES](workflow-exports/runtime-network-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="runtime-services"></a>
## Installed services

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/setup · Connection settings (advanced)`; runtime.ENABLE_ACESTREAM_ENGINE, runtime.ENABLE_ACESTREAM_CHECK_ENGINE, runtime.ENABLE_ACEXY, runtime.ENABLE_IPFS, runtime.ENABLE_ZERONET, runtime.ENABLE_TOR, runtime.ENABLE_WARP, runtime.ACESTREAM_BIND_ALL, runtime.WARP_DNS_ONLY, runtime.WARP_ENABLE_NAT, runtime.WARP_FORCE_IPV4; ready, loading, error, permission, dirty, pending, success, conflict, managed | [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json) | [Composed screen](workflow-prototype.html?screen=runtime-services); [specification](workflow-specification.md#runtime-services) | [Desktop EN](workflow-exports/runtime-services-cyan-en.jpg), [phone ES](workflow-exports/runtime-services-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="runtime-advanced"></a>
## Advanced source runtime

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/setup · Connection settings (advanced)`; runtime.ZERONET_URL, runtime.IPFS_GATEWAY_URL, runtime.SCRAPER_TIMEOUT, runtime.SCRAPER_RETRIES, runtime.ZERONET_TIMEOUT, runtime.ZERONET_RETRIES, runtime.IPFS_TIMEOUT, runtime.IPFS_RETRIES, runtime.CHANNEL_CLEANUP_DAYS, runtime.MEDIA_SERVER_MIN_REFRESH_MINUTES, runtime.ACESTREAM_STATUS_TIMEOUT, runtime.EPG_PROGRAM_RETENTION_HOURS, runtime.TZ; ready, loading, error, permission, dirty, pending, success, conflict, managed | [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json) | [Composed screen](workflow-prototype.html?screen=runtime-advanced); [specification](workflow-specification.md#runtime-advanced) | [Desktop EN](workflow-exports/runtime-advanced-cyan-en.jpg), [phone ES](workflow-exports/runtime-advanced-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="runtime-engine-ports"></a>
## Engine and Acexy connections

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/setup · Connection settings (advanced)`; runtime.ACESTREAM_HTTP_HOST, runtime.ACESTREAM_HTTP_PORT, runtime.ACEXY_HOST, runtime.ACEXY_PORT, runtime.ACEXY_LISTEN_ADDR, runtime.ACEXY_NO_RESPONSE_TIMEOUT, runtime.ACEXY_BUFFER_SIZE; ready, loading, error, permission, dirty, pending, success, conflict, managed | [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json) | [Composed screen](workflow-prototype.html?screen=runtime-engine-ports); [specification](workflow-specification.md#runtime-engine-ports) | [Desktop EN](workflow-exports/runtime-engine-ports-cyan-en.jpg), [phone ES](workflow-exports/runtime-engine-ports-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="runtime-gateway-ports"></a>
## ZeroNet and IPFS connections

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/setup · Connection settings (advanced)`; runtime.ZERONET_UI_PORT, runtime.ZERONET_FILESERVER_PORT, runtime.ZERONET_UI_HOST, runtime.IPFS_API_HOST, runtime.IPFS_API_PORT, runtime.IPFS_GATEWAY_PORT, runtime.IPFS_SWARM_PORT; ready, loading, error, permission, dirty, pending, success, conflict, managed | [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json) | [Composed screen](workflow-prototype.html?screen=runtime-gateway-ports); [specification](workflow-specification.md#runtime-gateway-ports) | [Desktop EN](workflow-exports/runtime-gateway-ports-cyan-en.jpg), [phone ES](workflow-exports/runtime-gateway-ports-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="recordings"></a>
## Your recordings

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/recordings`; recording.search, recording.state; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx) | [Composed screen](workflow-prototype.html?screen=recordings); [specification](workflow-specification.md#recordings) | [Desktop EN](workflow-exports/recordings-cyan-en.jpg), [phone ES](workflow-exports/recordings-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="channel-activity"></a>
## Stream activity

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/acestream-channels`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [ChannelActivityLogDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ChannelActivityLogDialog.tsx) | [Composed screen](workflow-prototype.html?screen=channel-activity); [specification](workflow-specification.md#channel-activity) | [Desktop EN](workflow-exports/channel-activity-cyan-en.jpg), [phone ES](workflow-exports/channel-activity-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="stream-bulk-fields"></a>
## Bulk metadata changes

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/acestream-channels`; bulk.apply_name, bulk.name, bulk.apply_group, bulk.group, bulk.apply_logo, bulk.logo, bulk.apply_tvg_id, bulk.tvg_id, bulk.apply_tvg_name, bulk.tvg_name, bulk.apply_source_url, bulk.source_url, bulk.is_active, bulk.epg_update_protected, bulk.category, bulk.country, bulk.language; ready, loading, error, permission, dirty, pending, success, conflict | [AcestreamChannels.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/AcestreamChannels.tsx); [BulkOperations.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/BulkOperations.tsx); [channelService.ts](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/services/channelService.ts); [channel.py](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py); [channels.py](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/api/endpoints/channels.py) | [Composed screen](workflow-prototype.html?screen=stream-bulk-fields); [specification](workflow-specification.md#stream-bulk-fields) | [Desktop EN](workflow-exports/stream-bulk-fields-cyan-en.jpg), [phone ES](workflow-exports/stream-bulk-fields-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="guide-inventory"></a>
## Browse guide channels

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/epg?tab=channels`; guide.filter_source, guide.search, guide.day; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [EPGChannelInventoryTable.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGChannelInventoryTable.tsx); [ScheduleView.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/epg/ScheduleView.tsx); [EPG.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/EPG.tsx) | [Composed screen](workflow-prototype.html?screen=guide-inventory); [specification](workflow-specification.md#guide-inventory) | [Desktop EN](workflow-exports/guide-inventory-cyan-en.jpg), [phone ES](workflow-exports/guide-inventory-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="player-picker"></a>
## Choose what to play

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `shared player dialog`; picker.mode, picker.search; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial | [ChannelPickerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/ChannelPickerDialog.tsx) | [Composed screen](workflow-prototype.html?screen=player-picker); [specification](workflow-specification.md#player-picker) | [Desktop EN](workflow-exports/player-picker-cyan-en.jpg), [phone ES](workflow-exports/player-picker-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="player-sessions"></a>
## Playback sessions

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `shared player controls`; read/control surface; ready, loading, error, permission, empty, filtered, partial, pending, success, conflict | [ActiveStreamsList.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/ActiveStreamsList.tsx) | [Composed screen](workflow-prototype.html?screen=player-sessions); [specification](workflow-specification.md#player-sessions) | [Desktop EN](workflow-exports/player-sessions-cyan-en.jpg), [phone ES](workflow-exports/player-sessions-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="dashboard-events"></a>
## Events on your home page

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/`; dashboard.events, dashboard.zone, dashboard.sports, dashboard.competitions, dashboard.teams; ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, storage-failed | [UpcomingEvents.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/overview/UpcomingEvents.tsx) | [Composed screen](workflow-prototype.html?screen=dashboard-events); [specification](workflow-specification.md#dashboard-events) | [Desktop EN](workflow-exports/dashboard-events-cyan-en.jpg), [phone ES](workflow-exports/dashboard-events-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="event-broadcasters"></a>
## Broadcaster links

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/events`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [BroadcasterLinks.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/BroadcasterLinks.tsx) | [Composed screen](workflow-prototype.html?screen=event-broadcasters); [specification](workflow-specification.md#event-broadcasters) | [Desktop EN](workflow-exports/event-broadcasters-cyan-en.jpg), [phone ES](workflow-exports/event-broadcasters-cyan-es.jpg); [run](verification-review-06.md) | #319: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="setup-source"></a>
## Add your first channel source

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/setup`; setup.url, setup.provider; ready, loading, error, permission, dirty, pending, success, conflict | [SetupSources.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/setup/SetupSources.tsx) | [Composed screen](workflow-prototype.html?screen=setup-source); [specification](workflow-specification.md#setup-source) | [Desktop EN](workflow-exports/setup-source-cyan-en.jpg), [phone ES](workflow-exports/setup-source-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="setup-guide"></a>
## Optional programme guide

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/setup`; setup.guide_name, setup.guide_url, setup.saved_guide; ready, loading, error, permission, dirty, pending, success, conflict | [SetupGuide.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/setup/SetupGuide.tsx) | [Composed screen](workflow-prototype.html?screen=setup-guide); [specification](workflow-specification.md#setup-guide) | [Desktop EN](workflow-exports/setup-guide-cyan-en.jpg), [phone ES](workflow-exports/setup-guide-cyan-es.jpg); [run](verification-review-06.md) | #318: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="channel-inline"></a>
## Number and favorite

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/tv-channels`; inline.number, inline.favorite; ready, loading, error, permission, dirty, pending, success, conflict | [ChannelNumberField.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ChannelNumberField.tsx); [TVChannelsTable.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelsTable.tsx) | [Composed screen](workflow-prototype.html?screen=channel-inline); [specification](workflow-specification.md#channel-inline) | [Desktop EN](workflow-exports/channel-inline-cyan-en.jpg), [phone ES](workflow-exports/channel-inline-cyan-es.jpg); [run](verification-review-06.md) | #320: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="sources"></a>
## Channel sources

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/sources`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx) | [Composed screen](workflow-prototype.html?screen=sources); [specification](workflow-specification.md#sources) | [Desktop EN](workflow-exports/sources-cyan-en.jpg), [phone ES](workflow-exports/sources-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

<a id="add-channels"></a>
## Add channels

| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |
|---|---|---|---|---|
| `/sources`; read/control surface; ready, loading, error, permission, empty, filtered, partial | [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx) | [Composed screen](workflow-prototype.html?screen=add-channels); [specification](workflow-specification.md#add-channels) | [Desktop EN](workflow-exports/add-channels-cyan-en.jpg), [phone ES](workflow-exports/add-channels-cyan-es.jpg); [run](verification-review-06.md) | #321: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |

## Preset parity and simplified location

Every row above maps to the exact location, canonical editor and independent save boundary in [before/after map](before-after-map.md). The [gallery](workflow-gallery.html) links all three presets and the new exports. See [OpenAPI references](openapi-contracts-06.md) for endpoint evidence. Rendered checks are design evidence only. Owner-approved: three presets, one shared product, seven-destination plan, Watch consolidation and immersive default. Individual final palettes/assets and participant acceptance remain proposed. Implemented: none.
