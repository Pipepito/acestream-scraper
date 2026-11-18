# Source findings · review 04

> Review 06 is the current design-only continuation: [package](README.md), [simplified ownership](before-after-map.md), [shared presets](shared-foundations-06.md), [graphics](asset-selection-06.md) and [new evidence](verification-review-06.md). Earlier closure/implementation-next language and historical passing counts do not authorize application work or establish current acceptance.
Evidence type: source inspection at `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`, 7 November 2026. This is separate from the earlier live [observed defects](evidence.md). No mutation was attempted on the live installation; its revision remains unknown.

## F15 — Bulk stream edits can misrepresent success and repeat batch work

**Provisional severity: P1 for result reliability; exact user impact requires isolated integration reproduction.** Owners: #315 and #320. This is not evidence of a general performance slowdown or corruption.

- [BulkOperations.tsx, fields and per-row loop](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/BulkOperations.tsx#L39) offers category, country, language and active. Its edit callback is invoked once per selected row, adding an `id` to each update object.
- [AcestreamChannels.tsx, bulk handler](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/AcestreamChannels.tsx#L270) passes the entire `selectedIds` array on every callback.
- [channelService.ts, batch request](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/services/channelService.ts#L248) sends that full array to `bulk_edit`.
- [AcestreamChannelUpdate](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py#L39) declares name/group/logo/TVG/source/active/online/TV-association/protection fields, not category/country/language or the per-row `id`. [The endpoint](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/api/endpoints/channels.py#L120) forwards the validated fields via `model_dump(exclude_unset=True)`.

Inference from this chain: selecting N rows invokes N requests for the whole N-row batch, while category/country/language do not survive as declared stream-update fields. A successful response can therefore be presented as a successful user edit even though the selected property has no corresponding stream update. Do not infer the exact database effects or timing without reproduction.

Concrete acceptance in an isolated synthetic fixture: select two raw streams attached to known TV channels; change category, then active status; capture request count and bodies; inspect stored raw-stream and TV-channel values after each operation. Expect a single deliberately scoped operation, valid canonical property ownership, and a truthful result. Test partial failure once; do not retry a whole successful batch per row. The design [bulk composition](workflow-prototype.html?screen=stream-bulk-fields) preserves fields and explicitly sends TV properties through their owning editor instead of pretending unsupported writes succeeded. This proposal itself needs #320 review.

## Corrections to earlier proposals, not application defects

The manual Cast entry in the older administration example was unsupported by current source. Manual host/port configuration belongs to remote VLC/Kodi, while Google Cast uses bounded discovery and trust. Telegram's authorization transport differs from normal account transport. W3U Save-only is a valid path. WARP mode and licence are separate commands. These corrections are incorporated in [review 04 coverage](coverage-review-04.md) and the detailed fields.

## Prior findings retained

The recording-opener crash on supported private HTTP, success-text contrast, phone control clipping and unnamed export sliders remain in #315. They were not retested merely because replacement mockups exist. Performance remains a hypothesis requiring #323 measurement. User preferences and unapproved direction choices remain in #316; they are not defects.
