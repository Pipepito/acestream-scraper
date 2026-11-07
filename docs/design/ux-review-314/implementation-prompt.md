# Epic #314 · implementation prompt

Paste the prompt below into a new chat in **Plan mode**. Review the plan, then approve implementation. This prompt is a handoff; it does not start application work in the current design/publishing session.

---

Act as the senior product designer, full-stack engineer and QA owner for AceStream Scraper. Plan and then, after I approve the plan and switch to implementation mode, implement **the entire epic #314 and its existing tasks #315–#324**. This is the implementation phase. The design-only phase is closed; remaining design refinement and newly found gaps belong within implementation, not another standalone audit project.

## Repository and authoritative context

- Repository: `/Users/pipepito/Code/acestream-scraper-alt`; GitHub: `Pipepito/acestream-scraper`.
- Epic: https://github.com/Pipepito/acestream-scraper/issues/314. Read its current body, comments and all ten tasks #315–#324. Keep that backlog condensed; do not create issues by default.
- Design reference worktree: `/tmp/acestream-ux-review-314`, branch `design/ux-review-314`, directory `docs/design/ux-review-314/`. Inspect the actual latest tip; do not assume a previously reported SHA is current.
- Inspect all working trees first and preserve unrelated changes. Read repository `AGENTS.md`, `CLAUDE.md` and applicable layered instructions. Recheck remote branch tips and source. Start implementation in an appropriate feature branch/worktree from freshly checked `develop`; the design branch has an older application base and is only a reference. Do not merge that stale application base into the implementation.
- Supplier reference: `downloads/design/sportzz-frontend/` in the main checkout. Inspect before running. Reuse ideas deliberately; do not replace the canonical React/TypeScript app with supplier code or its translation helper.
- Use the live installation address only from private session context, never from a public artifact. Its exact revision is unknown. Inspection there remains read-only. All playback, recording, discovery, device control, notifications, imports, settings mutations and recovery tests must use isolated synthetic test environments unless separately authorized.
- Read `README.md`, `task-refinements-04.md` (especially the owner-confirmed scope), `coverage-review-04.md`, `interaction-contracts.md`, `workflow-specification.md`, `traceability-matrix.md`, `source-control-map.md`, `source-contracts.md`, `source-findings-04.md`, `current-source-delta.md`, `designer-frontend-assessment.md`, `acceptance-protocols.md` and `verification-review-04.md`. Consult the earlier field ledgers/coverage/evidence for history. Render and exercise the current gallery/prototypes. Historical `prototype.html` is a concept with known limitations, not a production specification. The public preview route, if published, is recorded in `pages-preview.md`.

## What to deliver

Implement all three recognizable interface designs: **original lime**, **coral/navy “Open Interval”**, and **cyan “Signal Pitch”**, with a user-facing **Interface / Interfaz** selector and remembered preference. These are complete layout, typography, spacing and color treatments, not three accent swatches or three independent application forks. Current prototypes demonstrate coral/lime comparisons; cyan and the production selector still need completion. Keep the AceStream identity; working reference names do not authorize a rebrand.

Use shared state, domain logic, API services, accessible components and canonical editors. Every design must expose the same workflows, fields, permissions, states and deep links, in EN/ES, light/dark and responsive phone/tablet/desktop layouts. Interface choice is independent of language, light/dark/system theme and reduced motion. Switching must preserve drafts, selection, route/query context, focus, scroll, pending operations and live media ownership without reloading or duplicating requests/sessions. Define migration/default/fallback behavior. Browser-local preference must work without accounts; storage failure keeps the chosen design usable in the tab and gives clear recovery. Any justified account sync must be user-scoped, not a global server setting.

Most users have very little technical knowledge. Use clear actions, concise help and progressive disclosure while preserving every capability and machine value. Preserve original channel/programme/source names. Cover actual labels, help, units, defaults, ranges, validation, permissions, dependencies, save timing and consequences. Keep meaningful empty, filtered-empty, loading, partial, error, permission, dirty, pending, success, stale/conflict and destructive states. Shared patterns must be composed for each materially different workflow; a generic template is not feature completion.

Cover the entire application:

- **Recordings:** exact programme times, DST ambiguity/nonexistent times, scheduling, active/recovering/finalizing states, multipart gaps/playback, settings, storage/retention, protection, compatible copies and distinct stop/cancel/delete/disable consequences.
- **Access:** activation, every permission, public-view policy, supported private HTTP/Docker NAT versus forbidden public HTTP, password/session/one-time-credential consequences, expiry/denial and last-admin safeguards.
- **Channels/streams:** detail/statistics, bulk actions, source preference, complete-catalogue atomic reorder/stale conflict, manual Add, atomic Search Add and Link, optional reviewed similar-name matching.
- **Guides/playlists:** source/editor/detail, source-qualified ambiguous guide identity, rules, coverage/export controls, separate stream-to-TV/guide/exact-automation workflows; filters, formats, shared format editor, address/credential context, collision-safe guide IDs and honest export states.
- **Sources/extraction:** provider-specific forms, W3U save/import/favorites/recent, saved search review, exclusions, orphan cleanup, installed/standalone helper, manual/HTML/JSON/regex modes, large samples and bounded errors.
- **Integrations/system:** individual browser-player, Cast, VLC/Kodi/Android pairing, media-server/tuner, public-address, Telegram and notification editors; WARP exclusions and saved/applied/startup distinctions; service controls, full job history, storage details, logs/diagnostics, runtime setup, migration/loading/failure gates and both recovery paths.
- **Viewing/events/shared:** dashboard first-use/partial data, Live TV availability/failure/player continuity; event agenda/provider/source/detail/overlay/mapping; every Settings section, navigation/deep links, phone drawer, 404, changelog, notices, preference failure, unsaved navigation and remaining dialogs.

Preserve newer source behavior, including online-only viewing/Show all and refresh continuity, optional similar-name review, atomic manual/Search Add and Link, opt-in offline cleanup with its separate schedule transaction, and tuner hiding. Reconcile further source changes instead of restoring older mockup assumptions.

## Backend and non-negotiable contracts

Fix incomplete or incorrect backend behavior needed to deliver these workflows, not only their appearance. Reproduce source-only findings with isolated fixtures before claiming a defect. Start with the confirmed recording-opener private-HTTP crash, actual status contrast failures, phone Network/pagination clipping and unnamed guide-export sliders. Investigate **F15 bulk metadata ownership and repeated-batch behavior** under #315/#320. General performance slowdown remains unproven: measure it.

Keep settings ownership and independent API saves; never invent a global atomic Save. Preserve immediate-save semantics unless a concrete behavior change is reviewed. Preserve account/access-store isolation and fail-closed markers, default-deny aliases/prefixes, separate IPTV/admin/viewer permissions, trust/transport rules, SSRF protections, bounded fetching/regex/discovery, media ownership/leases, recording priority, direct versus Acexy routing, independent checker behavior, persistent service supervision, FIFO jobs, storage partial/unknown values and masked DB-independent diagnostics. Cast has bounded discovery; the obsolete manual Cast concept is not a capability. Manual VLC/Kodi and Android pairing are separate.

Keep endpoints thin. API changes require schemas, generated TypeScript clients, services and contract/integration tests. Schema changes require Alembic revisions and upgrade-path tests. Runtime/options changes require documentation and builder-contract checks. Preserve all supported architectures/image flavors. Never fabricate backend success to match a mockup or hide a broken capability behind disabled UI.

## Plan mode deliverable

Before changing application files, produce a decision-complete implementation plan based on current evidence:

1. Reconcile every current route/dialog/settings field/API transaction/state against the design matrix and existing issues. Identify omitted workflows, stale assumptions, backend gaps, contradictions and dependencies. Keep observed defects, source findings, preferences and hypotheses distinct.
2. Define the three-interface architecture, selector persistence/migration/default and continuity strategy, shared component/editor boundaries, localization and the order of feature migrations. Show concrete comparable interface examples where a remaining decision materially affects implementation. Ask only genuinely necessary questions; settle routine reversible details with sound judgment.
3. Map work and exit criteria to #315 reliability, #316 foundations, #317 localization, #318 shell/selector/settings/access/setup/recovery, #319 viewing/events/recordings, #320 channels/guides/playlists, #321 sources/extraction, #322 integrations/system, #323 measured performance and #324 integrated acceptance. Include supporting backend corrections in their feature owners.
4. Propose reviewable milestones/PR boundaries targeting `develop`, dependencies, compatibility/data migration risks, rollback strategy and tests at each step. Prioritize confirmed reliability fixes, then shared foundations/selector, then complete feature migrations and integrated acceptance. Keep the existing application usable during migration.
5. Specify coverage and validation for three interfaces × EN/ES × light/dark × responsive sizes, plus state switching and real API/media/security behavior. Check prerequisites early. Identify exact manual/hardware/participant evidence and owners; automated accessibility is not a screen-reader test.
6. Critically review the plan once for missing capabilities, unsafe transaction changes, unreachable states, backend/frontend drift, migration risks and false completion criteria. Resolve findings within the plan. Then wait for my plan approval; approval authorizes implementation, not deployment or merging.

## Execution after plan approval

Implement the approved plan end to end in reviewable increments. Do not stop after a scaffold, a selector, one interface, a few screens or another inventory. Maintain a durable milestone checklist and the traceable chain **surface/field/state → current source → implementation → tests/rendered evidence → remaining acceptance → existing issue owner**. Keep the epic/tasks updated precisely. Composed, reviewed, approved, implemented and verified are different statuses. Close tasks only when their actual acceptance is met.

Run focused tests while iterating, then the full repository completion gate on the final changes: current private infrastructure validation definitions plus application tests, lint/typechecks, generated-artifact drift, docs/runtime contracts, required Docker packaging/smokes and supported image/architecture checks, and complete browser/E2E suites. The previous design-only waiver **does not apply to implementation**. Follow instructions for missing Docker/dependencies and approved infrastructure access. Use isolated data; do not expose credentials/private captures or commit reports/runtime data.

Render and inspect all three interfaces and adverse states. Verify bounds, labels, contrast, focus/dialog behavior, keyboard use, reflow, localization and actual state/media continuity—not only document overflow. Obtain real screen-reader, browser zoom and device evidence where available. Execute the concrete participant/fluent-Spanish protocols when people are available; never invent results or call unavailable acceptance a pass. Fix failures and rerun affected/dependent checks. Record exact revisions, commands, pass/fail/skip/warning counts, measured performance and unresolved evidence.

Commit and push feature work, prepare/update reviewable PRs to `develop`, and update the existing epic/tasks with evidence. Do not merge, deploy the application, trigger/cancel Jenkins, publish images/releases, change infrastructure policy or mutate the live installation without separate authorization. Keep GitHub Pages preview maintenance separate from application deployment.

Finish with delivered scope across all three interfaces, backend corrections, PR/commit and artifact links, exact validation results and limits, migrations/compatibility consequences, and a candid list of anything still pending with its issue owner and required evidence. Do not claim the epic is complete while required functionality or acceptance remains outstanding.
