# Ten existing tasks · review 04 refinements

7 November 2026. This supplements the existing bodies of #315–#324 without creating issues or marking implementation complete. [Coverage](coverage-review-04.md), [gallery](workflow-gallery.html), [fields](workflow-specification.md), [contracts](interaction-contracts.md), [verification](verification-review-04.md) and [acceptance protocols](acceptance-protocols.md) form the reviewable package. All designs remain unapproved proposals.

## #315 — Reliability and accessibility

- [ ] Retain the four previously observed defects: private-HTTP recording opener, success-text contrast, phone Network/pagination clipping and unnamed export sliders. Reproduce and fix in application code; prototype passes do not resolve them.
- [ ] Reproduce [F15 bulk metadata/repeated-batch risk](source-findings-04.md) in isolated data. One deliberately scoped batch, valid property owner and truthful results; coordinate #320.
- [ ] Validate actual control bounds, named ranges, safe modal focus and AT output, including errors inside advanced disclosures. Use the [protocol](acceptance-protocols.md), not document-overflow checks alone.

## #316 — Design decisions and approved handoff

- [ ] Review the [144 composed workflows](workflow-gallery.html) and [traceability](traceability-matrix.md). This replaces the prior composition backlog; it does not remove design review.
- [ ] Approve/revise palette, type roles, calm/expressive emphasis, Events grouping and shared editor ownership against comparable alternatives. Existing IBM Plex/teal remains authoritative until decided.
- [ ] Explicitly approve any staged Save replacing an immediate save. Retain independent transactions and existing number/favorite timing.
- [ ] Resolve the bulk TV-property boundary proposal with #320. Record accepted/rejected decisions, without treating all composed copy as approved.

## #317 — EN/ES and state preservation

- [ ] Use [all field copy](workflow-specification.md), generated runtime fields, custom states and non-color status labels as draft resources. Implement typed localization; do not ship the disposable two-string engine or supplier translation helper.
- [ ] Obtain fluent Spanish and pseudo-locale review, zero/unknown/plural/date/timezone evidence, and actual spoken feedback. Preserve original channel/programme/source names and machine enums.
- [ ] Verify real draft, selection, focus, scroll, deep-link context and media-session continuity across preference changes, including storage failure.

## #318 — Shell, settings, access and recovery

- [ ] Implement [shared settings](workflow-prototype.html?screen=settings), [accounts](workflow-prototype.html?screen=access-activate), all runtime groups, setup, startup/recovery, 404, notices and drawer against their field/state specs.
- [ ] Preserve private-HTTP account access and Docker NAT support without browser pairing; public HTTP restrictions, last-admin guards, one-time credentials and session/permission consequences remain enforced server-side.
- [ ] Preserve deep-link aliases, settings precedence and explicit proxy overrides. Reuse canonical editors; runtime group saves retain the whole revision resource.
- [ ] Offline cleanup policy and schedule anchors remain separate saves; recovery never replaces accounts or the fail-closed marker.

## #319 — Viewing, events and recordings

- [ ] Implement the [recording family](workflow-gallery.html#recordings), [viewing family](workflow-gallery.html#viewing) and [event family](workflow-gallery.html#events), including all composed adverse states and original media contracts.
- [ ] Test exact programme instants, repeated/nonexistent DST time, stable retry key, active time locks, multipart gaps, original/copy/protection/storage states and distinct stop/cancel/delete/disable consequences.
- [ ] Verify online-only viewing, Show all, timed refresh and selected-player continuity; state/locale changes cannot release another viewer or steal playback ownership.
- [ ] Preserve event provider-specific fields, unknown/date-only times, source-qualified mapping, reviewed imports, source refresh and overlay revision/fingerprint checks.

## #320 — Channels, guides and playlists

- [ ] Implement [channels](workflow-gallery.html#channels), [guides](workflow-gallery.html#guides) and [playlists](workflow-gallery.html#playlists) from the composed fields, not generic table templates.
- [ ] Preserve complete-catalogue atomic reorder and stale conflicts, number Enter/blur and favorite timing, source preference order, atomic Add and Link and optional unselected similar-name review.
- [ ] Keep stream matching, source-qualified guide matching and conservative exact automation distinct; revalidate full guide scope and preview before Apply.
- [ ] Correct the bulk-field/request ownership and repeated-batch problem with #315. Preserve capability access through the correct editor; no silent successful no-op.
- [ ] Reuse formats inline, preserve relay/account/address/token/guide-ID dependencies and export date-offset conversion. Test filtered/empty/partial/download/copy failures.

## #321 — Sources, discovery and extraction

- [ ] Implement [17 source/search workflows](workflow-gallery.html#sources) and [8 extraction workflows](workflow-gallery.html#extraction), including provider registry, source types, W3U save-only/import/favorites/recent, saved search review, exclusions and orphan cleanup.
- [ ] Share installed/standalone recipe editors and preserve manual/HTML/JSON/regex modes, all fields and bounded large-source fallback. Standalone has no installation connection or source Save.
- [ ] Keep read-only preview, stale token/policy recheck, guarded source fetches and disposable regex worker limits. Failures retain existing channels and draft inputs.

## #322 — Integrations and system

- [ ] Implement [individual integration flows](workflow-gallery.html#integrations) and [system/WARP](workflow-gallery.html#system), not a single generic Connections template.
- [ ] Remove the unsupported manual Cast concept; manual VLC/Kodi setup and VLC Android pairing remain separate. Preserve account/opt-in/trust/ownership restrictions and bounded discovery.
- [ ] Keep Telegram transport/header requirements, notification test, media-server operations, tuner settings/hiding, WARP mode/licence/exclusions/startup and current/applied state distinct.
- [ ] Validate persistent engine supervision, dedicated checker independence, FIFO full job history, scalar/interrupted results, bounded partial storage and authenticated masked diagnostics.

## #323 — Evidence-driven performance

- [ ] Run the [performance protocol](acceptance-protocols.md#performance-protocol--323) at a known app SHA and target devices. Synthetic design rendering is not a performance benchmark.
- [ ] Investigate repeated bulk work as a specific source finding; do not generalize it to unmeasured whole-app slowdown. Record baselines before selecting optimizations.

## #324 — Integrated acceptance

- [ ] Consume the [surface → field → state → evidence matrix](traceability-matrix.md); verify final implementation rather than counting design artifacts as passes.
- [ ] Complete actual AT/native zoom/physical-device and participant protocols, fluent Spanish review and cross-feature media/security integration. Native desktop checks in this pass were blocked by a locked Mac; no AT or device result is claimed.
- [ ] Run full application/Docker/browser validation for implementation. The current explicit design-only waiver is not transferable to product code.
- [ ] Keep the epic and ten tasks open until their actual acceptance criteria are met. No new issue is needed for these refinements.
