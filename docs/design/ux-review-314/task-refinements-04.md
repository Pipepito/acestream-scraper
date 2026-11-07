# Ten existing tasks · review 04 refinements

7 November 2026. This supplements the existing bodies of #315–#324 without creating issues or marking implementation complete. [Coverage](coverage-review-04.md), [gallery](workflow-gallery.html), [fields](workflow-specification.md), [contracts](interaction-contracts.md), [verification](verification-review-04.md) and [acceptance protocols](acceptance-protocols.md) form the reviewable package. The owner has confirmed the implementation scope below; detailed mockups are references, not completed production acceptance.

## Implementation scope confirmed by the owner

The design-only phase is closed. The next run starts implementing epic #314 and its existing ten tasks, including **all three referenced interface designs with a user-facing selector**, plus backend and incomplete-feature fixes needed to support the experience. Remaining design refinement, research and validation belong within implementation and acceptance; another standalone design-audit round is not a prerequisite.

The three references are the original **lime** direction, **coral/navy “Open Interval”**, and **cyan “Signal Pitch”**, as documented in the [supplier assessment](designer-frontend-assessment.md#three-different-visual-directions-are-present). These are working reference names, not a product rebrand. The older instruction to choose one winning direction is superseded. Calm/expressive and coral/lime prototype controls are comparison tools, not the finished production selector. Cyan currently has a reference proposal; completing and validating its production treatment across the app belongs to #316 and the feature rollout. Existing exports do not establish cyan coverage.

**Later owner confirmation, 7 November 2026:** keep three and make the third more immersive, using the cyan reference as its starting point. Deliver meaningful artwork and distinct composition, including photographic/illustrative banners, category art and richer programme cards, while keeping administration calm and complete. The [visual-resource brief](visual-resources-05.md) specifies the initial assets, fallback/security contracts, current backend support and ownership. Final assets and their rendered use still need production and review during implementation.

### Selector and parity contract

- Offer three coherent, recognizable interface choices on the shared appearance/preferences surface, with an accessible **Interface / Interfaz** selector and preview/description. Develop each design's appropriate layout, typography, spacing and color treatment; changing only an accent swatch does not complete this scope.
- All three expose the same existing capabilities, fields, permissions, states, deep links and operational consequences across the whole application, in EN/ES, light/dark and phone/desktop layouts. Keep interface choice independent of language, light/dark/system appearance and reduced-motion preferences.
- Share application state, services, canonical editors and business rules. Interface switching must preserve playback and recording ownership, in-flight operations, drafts, selections, route/query context and focus; it must not reload the app or duplicate requests.
- Remember the user's choice with a documented default, safe handling of missing/unknown values and migration of existing preferences. A storage failure keeps the current choice usable for the tab and offers a retry. Browser-local preference works without accounts; any justified account synchronization must have separate user-scoped persistence, not a server-wide setting or new global atomic Save.

### Backend and incomplete-feature scope

Backend work is explicitly in scope when a feature is incomplete, incorrectly implemented or needs support for these interfaces. Reproduce source-only findings with isolated data, then fix the actual behavior across frontend/backend boundaries within the owning existing task. Do not hide a broken capability behind a redesigned screen or treat a synthetic success as completion. Start with the confirmed #315 defects and [F15](source-findings-04.md) in #315/#320; inspect other affected workflows as they are implemented. Keep observed defects, source inferences and new hypotheses distinct.

API changes include schemas, generated client, services and integration tests; schema changes include Alembic and upgrade-path coverage. Preserve security, media ownership, recovery isolation and independent transaction contracts. The design-only validation waiver ends at application implementation: use the full repository completion gate for product changes. This amendment changes scope and task acceptance only; application code/runtime remain unchanged in this run.

Start implementation from freshly checked `develop` in an appropriate feature branch/worktree, using this design branch as the reference. Its earlier application base is not the implementation starting point. Work in reviewable increments targeting `develop`, with #315 and shared foundations/selector first, feature migrations and supporting backend fixes next, and integrated acceptance across all three interfaces. Deployment, merging and release remain separate actions.

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
