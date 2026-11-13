# Canonical settings and unsaved changes

Settings owns only section navigation and feedback. PlaybackSettings,
AutomationSettings, LinkSettings, AccessSection and NetworkSettings own their
queries and save boundaries; selecting a tab mounts only that editor. Existing
`?tab=playback|automation|links|access|network` URLs preserve other query values.
StreamLinkFormatsSection remains shared with Playlist. RecordingSettingsFields
belongs to Recordings and is linked from Settings/Automation.

AppBootstrap creates one data router outside preference rendering. The
UnsavedChangesProvider registers dirty and pending state from canonical editors.
Route changes, query-string tabs and Back require discard confirmation when dirty;
an in-flight save must settle before navigation continues. A successful save may
complete the requested navigation; a failure leaves the draft and confirmation
available. Document unload uses the browser's native beforeunload warning.
Preference changes do not navigate or replace components and preserve drafts.

`useSettingDraft` keeps scalar edits independent of query refreshes. Persist each
field through its existing hook/service and acknowledge only that submitted value.
Disable editable controls while submitting so a late success cannot replace a
newer edit. Object editors keep their established revision/draft contracts and
register through `useUnsavedChanges`. Registration is separate from persistence.
Outside the application provider the hook is inert, allowing isolated editor tests.
Do not interpret this as permission to omit the provider from an app entry point.

The navigation guard does not intercept a local modal's state setter. Canonical
modal editors must also confirm discard on Cancel/Escape/backdrop, reject close
while submitting and restore focus. Stream link dialogs implement both boundaries.
Recording settings use a query-driven dialog and therefore the shared route guard.
Disabling recordings requires confirmation that active captures stop and future
recordings are cancelled while existing files remain. Stop, Cancel and Delete have
separate confirmations and retain server-side eligibility enforcement.

`UnsavedChanges.test.tsx` covers query navigation, Back, failures, pending saves,
browser unload and preference changes. Settings tests verify that unrelated tabs
are not queried. RuntimeLocalization verifies all 47 backend option labels/help
against the typed English catalogue and complete Spanish keys. The Jest browser
environment supplies Node's native Fetch primitives for real data-router navigation.

This is an incremental migration under #318/#319. Editors not yet registered and
other modal close paths remain in the epic acceptance ledger; this document is not
an assertion that every application form has completed migration.

Sources now share `SourceEditor` between setup and management: provider selection,
source type, friendly name, enabled state and bare-ID controls all use the same
fields and save controller. Choosing a provider only fills fields. Management
saves without fetching; setup explicitly follows a successful save with Find
channels. A retry reuses the saved source. Recipe state is omitted from these
updates and remains owned by the extraction editor. Guide sources share
`GuideSourceFields` and the existing create mutation; management guards its
pending state, inline errors and modal cancellation. Runtime, WARP, public-address
and notification editors also preserve/register their drafts.

The remote-player dialog registers dirty and pending state, guards modal close,
and snapshots its initial fields once per opening/player identity. Query refresh
does not overwrite an edited name, address, credentials or link format. Save,
probe and pairing share an immediate action guard; pending operations disable the
fields and close action. Failed saves retain the draft and inline error.

Account setup, password changes, individual accounts, access policy and credential
forms also register dirty/pending state. Their independent saves disable only the
relevant controls and retain raw failures so changing language preserves and
retranslates the same error. Issued credentials remain guarded until dismissed;
no preference writes credentials to browser storage.

Media-server and tuner forms preserve local edits when their queries refresh.
Telegram source editors remain mounted if account status changes during editing;
finish or explicitly discard an editor before locking or replacing it. Pending
requests have immediate duplicate guards. Secrets remain memory-only and retain
Telegram's explicit post-submission and lock clearing behavior.

Event retention keeps its editor mounted when its management panel is hidden;
Cancel restores the latest saved policy and failures retain both fields. Overlay
and broadcaster mapping operations retain the reviewed input/revision and guard
repeated submissions. Catalogue reviews survive folder browsing; only their
`folder` and `catalogue` query keys preserve the same editor. Host tabs and route
changes still pass through the unsaved-changes guard. Local catalogue replacement
and discard actions confirm before removing an unsaved review.

The installed extraction page receives draft/pending state from the shared recipe
component and guards navigation with the same provider. The standalone component
uses document-unload protection without importing the application router, query
client or API. A save records the recipe baseline only after its request succeeds;
changing source URL/type invalidates the prior test. Feedback is resolved in the
current language, and plural resources are included in the generated helper subset.

Recording dialogs pin the programme/recording and revision reviewed at opening.
Guide refreshes cannot silently substitute another programme. Modified times and
timezone register as a dirty draft and require explicit discard on close. Save
disables every time/ambiguity control until settlement; rejection retains values
and the original creation intent key, with feedback in the currently selected
language. Opening or cancelling an untouched dialog performs no recording write.

Disabling account protection first pauses the Access editor's administrative
queries and aborts their in-flight requests, then submits the disable operation.
The whole editor is disabled while it runs. A rejected disable retains its password,
confirmation and other drafts, and resumes reads; only success refreshes the access
gate. Keep the query AbortSignals attached to users, policy, credentials and sessions.
This prevents a delayed old read from arriving after its authorization is revoked.
