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
