# Ten existing tasks · review 04 refinements

7 November 2026. This supplements the existing bodies of #315–#324 without creating issues or marking implementation complete. [Coverage](coverage-review-04.md), [gallery](workflow-gallery.html), [fields](workflow-specification.md), [contracts](interaction-contracts.md), [verification](verification-review-04.md) and [acceptance protocols](acceptance-protocols.md) form the reviewable package. This is historical background; review 06 is the current design-only scope.

## Implementation scope confirmed by the owner

**Historical scope note, superseded by review 06.** The owner retained three interface directions but explicitly continued design-only work. Implementation is not authorized in this session. The earlier closed-design/implementation-next statements are withdrawn. See [current scope and owners](task-refinements-06.md), [shared architecture](shared-foundations-06.md) and [OpenAPI testing](openapi-contracts-06.md).

The checklists below record earlier future implementation acceptance. Cyan, the selector and whole-app compositions are now demonstrated in the current disposable prototype; they remain unimplemented in the application. Immediate saves were retained for guide automation and stream-check scope. No staged replacement is approved.

## #315 — Reliability and accessibility

- [ ] Retain the four previously observed defects: private-HTTP recording opener, success-text contrast, phone Network/pagination clipping and unnamed export sliders. Reproduce and fix in application code; prototype passes do not resolve them.
- [ ] Reproduce [F15 bulk metadata/repeated-batch risk](source-findings-04.md) in isolated data. One deliberately scoped batch, valid property owner and truthful results; coordinate #320.
- [ ] Fix supporting backend behavior and incomplete implementations identified during these reproductions; keep the correction shared across all three interfaces and assign further findings to their existing feature owner.
- [ ] Validate actual control bounds, named ranges, safe modal focus and AT output, including errors inside advanced disclosures. Use the [protocol](acceptance-protocols.md), not document-overflow checks alone.

## #316 — Three interface foundations

- [ ] Produce the selected visual-resource library and provenance manifest, and compose the immersive third interface using the [resource brief](visual-resources-05.md). Show representative viewing and management screens with real selected artwork and missing-art states; palette changes or placeholders alone do not complete this requirement.

- [ ] Review the [144 composed workflows](workflow-gallery.html) and [traceability](traceability-matrix.md). This replaces the prior composition backlog; it does not remove design review.
- [ ] Implement coherent lime, coral/navy and cyan foundations and shared component variants. Complete cyan's app-wide treatment as part of this task. Do not reduce the owner decision to a single selected palette or three accent swatches.
- [ ] Define three selectable interface presets, their preview/description, stable identifiers, default/fallback and preference migration with #318. Keep application branding and shared workflow semantics intact.
- [ ] Explicitly approve any staged Save replacing an immediate save. Retain independent transactions and existing number/favorite timing.
- [ ] Resolve the bulk TV-property boundary proposal with #320. Record accepted/rejected decisions, without treating all composed copy as approved.

## #317 — EN/ES and state preservation

- [ ] Use [all field copy](workflow-specification.md), generated runtime fields, custom states and non-color status labels as draft resources. Implement typed localization; do not ship the disposable two-string engine or supplier translation helper.
- [ ] Obtain fluent Spanish and pseudo-locale review, zero/unknown/plural/date/timezone evidence, and actual spoken feedback. Preserve original channel/programme/source names and machine enums.
- [ ] Verify real draft, selection, focus, scroll, deep-link context and media-session continuity across preference changes, including storage failure.
- [ ] Localize the interface selector and each preset's description. Verify EN/ES, original-content preservation and state continuity in all three interfaces and during switching.

## #318 — Shell, settings, access and recovery

- [ ] Implement [shared settings](workflow-prototype.html?screen=settings), [accounts](workflow-prototype.html?screen=access-activate), all runtime groups, setup, startup/recovery, 404, notices and drawer against their field/state specs.
- [ ] Preserve private-HTTP account access and Docker NAT support without browser pairing; public HTTP restrictions, last-admin guards, one-time credentials and session/permission consequences remain enforced server-side.
- [ ] Preserve deep-link aliases, settings precedence and explicit proxy overrides. Reuse canonical editors; runtime group saves retain the whole revision resource.
- [ ] Offline cleanup policy and schedule anchors remain separate saves; recovery never replaces accounts or the fail-closed marker.
- [ ] Implement the user-facing three-interface selector and persisted preference, independently of language and light/dark/system appearance. Test reload/default/fallback/storage failure and switching during playback, dirty forms and pending work. Any needed preference API is user-scoped and separately saved.

## #319 — Viewing, events and recordings

- [ ] Deliver the richer viewing compositions and trustworthy artwork fallbacks in [the visual brief](visual-resources-05.md). Connect current logo/programme/event metadata, preserve explicit event-artwork loading, and keep artwork changes independent of media ownership.

- [ ] Implement the [recording family](workflow-gallery.html#recordings), [viewing family](workflow-gallery.html#viewing) and [event family](workflow-gallery.html#events), including all composed adverse states and original media contracts.
- [ ] Test exact programme instants, repeated/nonexistent DST time, stable retry key, active time locks, multipart gaps, original/copy/protection/storage states and distinct stop/cancel/delete/disable consequences.
- [ ] Verify online-only viewing, Show all, timed refresh and selected-player continuity; state/locale changes cannot release another viewer or steal playback ownership.
- [ ] Preserve event provider-specific fields, unknown/date-only times, source-qualified mapping, reviewed imports, source refresh and overlay revision/fingerprint checks.
- [ ] Deliver these workflows in all three interfaces and fix supporting recording/event/player backend defects or incomplete behavior, with integrated ownership and state-transition evidence.

## #320 — Channels, guides and playlists

- [ ] Implement [channels](workflow-gallery.html#channels), [guides](workflow-gallery.html#guides) and [playlists](workflow-gallery.html#playlists) from the composed fields, not generic table templates.
- [ ] Preserve complete-catalogue atomic reorder and stale conflicts, number Enter/blur and favorite timing, source preference order, atomic Add and Link and optional unselected similar-name review.
- [ ] Keep stream matching, source-qualified guide matching and conservative exact automation distinct; revalidate full guide scope and preview before Apply.
- [ ] Correct the bulk-field/request ownership and repeated-batch problem with #315. Preserve capability access through the correct editor; no silent successful no-op.
- [ ] Reuse formats inline, preserve relay/account/address/token/guide-ID dependencies and export date-offset conversion. Test filtered/empty/partial/download/copy failures.
- [ ] Deliver parity across all three interfaces; correct incomplete API/service behavior rather than disguising it in presentation. Contract changes include schemas, regenerated clients and integration coverage.

## #321 — Sources, discovery and extraction

- [ ] Implement [17 source/search workflows](workflow-gallery.html#sources) and [8 extraction workflows](workflow-gallery.html#extraction), including provider registry, source types, W3U save-only/import/favorites/recent, saved search review, exclusions and orphan cleanup.
- [ ] Share installed/standalone recipe editors and preserve manual/HTML/JSON/regex modes, all fields and bounded large-source fallback. Standalone has no installation connection or source Save.
- [ ] Keep read-only preview, stale token/policy recheck, guarded source fetches and disposable regex worker limits. Failures retain existing channels and draft inputs.
- [ ] Deliver all three interface treatments and complete missing source/import/extraction behavior in the backend where required, using bounded isolated fixtures and preserving existing data on failure.

## #322 — Integrations and system

- [ ] Implement [individual integration flows](workflow-gallery.html#integrations) and [system/WARP](workflow-gallery.html#system), not a single generic Connections template.
- [ ] Remove the unsupported manual Cast concept; manual VLC/Kodi setup and VLC Android pairing remain separate. Preserve account/opt-in/trust/ownership restrictions and bounded discovery.
- [ ] Keep Telegram transport/header requirements, notification test, media-server operations, tuner settings/hiding, WARP mode/licence/exclusions/startup and current/applied state distinct.
- [ ] Validate persistent engine supervision, dedicated checker independence, FIFO full job history, scalar/interrupted results, bounded partial storage and authenticated masked diagnostics.
- [ ] Deliver all three interfaces and fix supporting integration/system backend defects or incomplete implementations. Verify actual results and ownership, not only command acknowledgement or mock success.

## #323 — Evidence-driven performance

- [ ] Measure actual hero/card image transfer, decode, layout shift and lazy-loading behavior across all three interfaces, including failed/slow artwork and switching without duplicate downloads. Do not bundle the supplier's full image/video library.

- [ ] Run the [performance protocol](acceptance-protocols.md#performance-protocol--323) at a known app SHA and target devices. Synthetic design rendering is not a performance benchmark.
- [ ] Investigate repeated bulk work as a specific source finding; do not generalize it to unmeasured whole-app slowdown. Record baselines before selecting optimizations.
- [ ] Measure loading and switching cost for all three interfaces. Avoid duplicated app bundles, request work or media sessions; correct demonstrated frontend/backend bottlenecks with measured before/after evidence.

## #324 — Integrated acceptance

- [ ] Verify the selected asset set, provenance, readable crops/overlays and missing/blocked/oversized/decode-failed artwork across all three interfaces. The previous static preview passes do not validate the newly requested immersive composition or resources.

- [ ] Consume the [surface → field → state → evidence matrix](traceability-matrix.md); verify final implementation rather than counting design artifacts as passes.
- [ ] Complete actual AT/native zoom/physical-device and participant protocols, fluent Spanish review and cross-feature media/security integration. Native desktop checks in this pass were blocked by a locked Mac; no AT or device result is claimed.
- [ ] Run full application/Docker/browser validation for implementation. The current explicit design-only waiver is not transferable to product code.
- [ ] Add interface choice to the acceptance matrix: three designs × EN/ES × light/dark × responsive layouts, plus switching, preference persistence/fallback and cross-feature state continuity. Validate supporting backend corrections and upgrade paths at the final implementation revision.
- [ ] Keep the epic and ten tasks open until their actual acceptance criteria are met. No new issue is needed for these refinements.
