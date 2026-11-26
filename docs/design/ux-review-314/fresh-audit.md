# Fresh UX/UI audit — review 03

> Review 06 is the current design-only continuation: [package](README.md), [simplified ownership](before-after-map.md), [shared presets](shared-foundations-06.md), [graphics](asset-selection-06.md) and [new evidence](verification-review-06.md). Earlier closure/implementation-next language and historical passing counts do not authorize application work or establish current acceptance.
> Review 04 update (7 November 2026): [expanded composed coverage](coverage-review-04.md), [workflow fields/interactions](workflow-specification.md), [current verification](verification-review-04.md) and [task refinements](task-refinements-04.md) supersede historical composition gaps. Prior live defects remain open. No user approval or application implementation is implied.

Reviewed 7 November 2026. **Design review only; no redesign implementation or approval.**

The largest problems are reliability, unclear consequences and task organization. A new palette will not fix them. The earlier assessment was useful but overvalued the supplier's visual system, treated several preferences as usability findings, and left most administration without composed examples.

Recommended direction: **calm, readable administration with restrained TV expression on viewing surfaces**. Compare both treatments with identical content in the [new prototype](admin-prototype.html). Neither lime/coral nor Inter/Barlow is approved. Existing IBM Plex/teal application standards remain in force until an explicit decision replaces them.

## Evidence and confidence

- Starting application baseline: 7ccf16d383758aeeb78845e20e3716ddf97df10d; original design head: ebadaaf17be1e4ba156db09ebf2a8c76d4ead7d8. Develop advanced to cf952afc6b4489c02b7a675ff3d634cc13d98e0b during the audit. Its new viewing, matching, linking and retention flows were source-inspected and reconciled in the [current-source delta](current-source-delta.md). The design worktree retains the original application base; no implementation merge was performed.
- All eleven GitHub issue bodies (#314–#324) were fetched again. They were open and proposed for refinement. This review adds dated corrections rather than presenting old evidence as new.
- The live installation's exact commit **remains unverified**. A displayed version is not a commit identity.
- Fresh read-only Chromium sweep: **49 route/theme/viewport cases**, covering ordinary routes, all settings/source/guide tabs, setup and 404. Additional detail/startup and targeted checks followed. 33 scans had no axe violations; 16 returned candidates. This is not a conformance rate.
- Contexts: English UI; 1440×1000 light, five desktop dark states, seven 390×844 light states, three 320×740 light states. No working Spanish application mode was found.
- Writes, media/discovery URLs and off-installation requests were blocked. No recording, import, setting save, credential operation, cast, service action or notification send occurred. External logos could be blocked, so missing images are not defects.
- Raw installation captures remain local. [Sanitized evidence](evidence.md) contains measurements, app-owned labels, code references and reproduction steps. New mockups use entirely synthetic data.

## Verification of the original thirteen findings

“Confirmed” describes the observation, not proof that the proposed fix improves task success. **None is classified resolved**: the new merge leaves the confirmed defect sites unchanged. Its separate usability improvements are recorded in the current-source delta.

| ID | Disposition / type | Reproduction and context | Impact / severity | Decision and evidence |
| --- | --- | --- | --- | --- |
| F01 | **Confirmed — defect** | Live TV → open a Record action without submitting. Private-IP HTTP; 1440×1000 light EN. | P0 for this workflow: entire app becomes blank. | Missing crypto.randomUUID, available getRandomValues, thrown initializer and empty body reproduced. Contain failure; one secure idempotency key per intent. [E01](evidence.md#e01-recording-opener). #315. |
| F02 | **Confirmed observation; usability hypothesis** | Sidebar: compare Scraper / Search / Acestream Channels / TV Channels / EPG. Desktop and phone EN. | P1 hypothesis: novices must distinguish unfamiliar concepts before acting. No participant result measured. | Rename labels without route changes; explain source → stream → TV channel. Twenty destinations alone is not a defect. [Coverage](coverage-review-03.md). #316/#318. |
| F03 | **Confirmed — IA problem** | Settings → Automation, then Network and Public address. 1440/390 light EN. | P1: recording, guide assignment, schedules and notifications lack clear ownership; address fallback competes with saved override. | One editor per capability; retain advanced fallback configuration with effective-source explanation. [Field ledger](field-ledger.md). #318–#322. |
| F04 | **Confirmed — interaction inconsistency** | Inspect Automation: guide switch saves immediately; recording and interval forms have separate saves; Network needs restart. No live edits. | P1: immediate, staged and restart-bound effects share a visual area. Recording disablement is consequential. | Save per real transaction boundary, not one fictional global atomic Save. Confirm actual stop/cancel impact. [Specification](design-specification.md#editing-and-consequences). #318/#319/#320. |
| F05 | **Confirmed — measured defect** | Light success text on Sources, Guide, Playback, Media servers, WARP and System. 1440 light EN. | P1: ordinary text below 4.5:1. | White/#1f8f59 ≈4.09:1; #1f8f59/#fbfdff ≈4.01:1. Use semantic text pairs, not icon tokens. [E02](evidence.md#e02-contrast-and-labels). #315. |
| F06a | **Confirmed — reflow defect** | Direct-load Settings ?tab=network, 390×844 light EN. | P2: active label mostly clipped; scrolling remains available. | Tab starts x316.28, width 101.95; scroll viewport ends 338. Use phone section selector; preserve deep links. [E03](evidence.md#e03-reflow). #315/#318. |
| F06b | **Confirmed with corrected selector — reflow defect** | TV Channels at 320, scroll to pagination. “Next” is visible text; accessible name is “Go to next page”. | P2: compare control with panel, not just document overflow. | Current bounds in E03. Initial fresh harness missed the accessible-name assumption; failed check rerun. #315/#320. |
| F07 | **Confirmed composition observation; hypothesis** | Home/Live TV first viewport, 390 light and 1440 dark EN. | P2: introductory/management content competes with browsing. No abandonment measured. | Clear viewing action and catalogue first. Do not prescribe recommendations/artwork without data. Keep home dashboard and independent failures. #319. |
| F08 | **Confirmed — hierarchy problem** | Recordings default view, 1440 light/dark and 390 light EN. | P2: “Recording history” mixes deleted entries, raw states and file operations with watching. | Saved / Upcoming / History. Partial recordings remain playable where files are ready; expose gaps. Completed is not automatically playable. [Mockup](admin-prototype.html?view=recordings). #319. |
| F09 | **Confirmed — task consistency problem** | Compare Setup source action and Sources editor, light EN. | P2: saving can be mistaken for importing; bare-ID options arrive too early. | Shared form; distinct “Add and find channels” and “Save source only”. Save→queue→result is not atomic. [Mockup](admin-prototype.html?view=sources). #321. |
| F10 | **Confirmed terminology observation; hypothesis** | Guide Sources/Channels/Matching/Rules/Export, 1440/390 light EN. | P2: technical tabs obscure add→review→apply. | Preserve explicit selection, source identity and stale-preview rejection. No preselection. “Exact” is a match type, not approval. [Mockup](admin-prototype.html?view=guide). #320. |
| F11 | **Confirmed — discoverability hypothesis** | Six integration pages, 1440 light EN. | P2: user outcomes distributed across mechanism names; separate security scopes are real. | Outcome links above existing independent pages. Never merge forms, queries or permissions. [Mockup](admin-prototype.html?view=connections). #322. |
| F12 | **Needs evidence — performance claim** | Eager imports remain in App.tsx; old transfer figure not reproduced under a controlled profile. | P2 investigation, not measured slowdown. | Withdraw any implication that 2.03 MB predicts poor performance. Five-run controlled production baseline before budgets. #323. |
| F13 | **Confirmed — preference, not defect** | Shell/panels and long phone pages, light/dark. | P3: nested surfaces/glow weaken the reviewer's preferred hierarchy. | Flatten one level; retain semantic theme system. User testing decides whether calmer is easier. #316. |

## New findings and corrections

| ID | Finding / evidence | Severity / action |
| --- | --- | --- |
| F14 | **Confirmed defect:** both Guide Export date-range inputs lack label, aria-label and aria-labelledby. EPGXmlOutputPanel.tsx:99; fresh DOM/axe check. | P1 #315/#320. Name start/end independently, localize value text and verify keyboard operation. Do not infer a keyboard defect from one inconclusive ArrowRight trial. |
| F15 | **Confirmed design-reference gap:** old prototype recreates fields on locale/theme changes without storing entered values; “2 unsaved changes” is hard-coded. Product text often 10–12 px; many apparent controls are placeholders. | P2 artifacts #316. Old boards are historical. New prototype retains demonstrated drafts/selection and labels simulations. It still does not implement the app state machine. |
| F16 | **Confirmed inventory discrepancy:** navItems.tsx places Events under Manage; narrative/coverage described Watch. Phone TV-channel core filters sit behind Show filters despite repository guidance. | P2 #318/#320. Distinguish observed from proposed navigation. Keep the four intended core filters visible in implementation. |
| F17 | **Confirmed localization gap:** labels, help, recording states, access/startup content, runtime metadata and standalone helper use English literals. | P1 product requirement gap #317 plus feature owners. Translate owned UI; preserve names, URLs and raw logs. A prototype language selector is not app localization. |

Desktop grid required-child candidates, duplicate unnamed main landmarks in the installed extraction builder, heading-order candidates and disabled-helper contrast still **need evidence** for assistive-technology impact and applicable exceptions. Prioritize confirmed range labels independently. Offscreen Live TV target-size failure was **not reproduced on the usable control**: a scrolled guide button measured about 166×44 px. Do not call 66 offscreen scanner nodes 66 user-visible failures.

Normal text needs at least 4.5:1 contrast; inactive controls have specific exceptions. [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html). Controls need programmatically available names. [W3C name/role/value guidance](https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html). Our 44 px target is a design goal; WCAG 2.2 AA minimum is 24 px with exceptions, not universally 44 px. [W3C target guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

## Complete journey critique

| Journey | Strength to preserve | Friction / design response | Not exercised live |
| --- | --- | --- | --- |
| First use → source → optional guide → watch/export | Skippable setup; engine-free catalogue use. | Save-as-added versus Finish: repeat persisted-source summary and actual effect. | Fresh-install mutation/resumption and novice sessions. |
| Find → watch → record → stop | Embedded catalogue, shared lifecycle, explicit Stop. | HTTP recording crash; overloaded first phone viewport. | Playback, tracks, casting, retained sessions. |
| Streams → TV channel → guide → playlist | Separate identities, number/favourite controls, reviewed matching, atomic reorder. | Staged terminology/IDs; show source-qualified identities in ambiguity review. | Reorder conflicts, credentials and saves. |
| Source → queue → results → delete/repair | Queue and preservation rules. | Saved/queued/imported/verified need distinct statuses. Delete impact includes assigned streams. | Fetch/import/write and Telegram authorization. |
| Record → find → protect/convert/delete | Original-file and protection contracts. | Saved/Upcoming/History; exact stop/cancel/delete consequences. | Lifecycle, storage limits and DST scheduling. |
| Accounts → viewing policy → credentials → TV | Separate scopes and private HTTP support. | Accounts are not a universal login switch. Permission changes sign out/revoke credentials. | Enabled roles, expiry, last admin and one-time secrets. |
| Connect player → address → troubleshoot | Independent routes and override explanation. | Route by outcome; preserve casting/remote/IPTV/admin distinctions. | Discovery/control and external-app handoff. |
| Fault → diagnose → retry/recover | DB-independent diagnostics and separate recovery paths. | Safe retry before replacement; partial storage stays partial. | Fault injection, backup/rebuild/fresh, fail-closed gates. |
| Extract → pair records → test/copy | Shared implementation and bounded preview. | Public helper cannot contact installation; retain raw/manual large-sample path. | Hostile/large input and worker timeouts. |

## Heuristic critique, not participant research

Anti-pattern verdict: **partial fail** for repeated panels, duplicate hierarchy and decorative glow. This does not establish AI authorship. The supplier's photographic hero/category system belongs only where imagery and discovery justify it; importing it into access/recovery would distract.

| Heuristic | /4 | Reason |
| --- | ---: | --- |
| System status | 3 | Rich queue/storage/service detail; raw outcomes need interpretation. |
| User language | 1 | Source/stream/channel and EPG jargon arrive early. |
| Control/freedom | 2 | Explicit stop/cancel; uneven draft handling. |
| Consistency | 2 | Save semantics and ownership vary. |
| Error prevention | 2 | Strong reviewed matching; consequential configuration needs review. |
| Recognition | 2 | Routes lack task orientation. |
| Efficiency | 3 | Bulk controls, filters, shared editors and expert paths. |
| Minimal presentation | 2 | Panels/metadata compete with the task. |
| Error recovery | 1 | Recording opener blanks app. |
| Help | 3 | Extensive but technical/distributed guidance. |
| **Total** | **21/40** | Significant improvement needed; no before/after user score claimed. |

Technical scores: accessibility 2/4; performance **unscored** without baseline; responsive 2/4; theming 3/4; visual restraint 2/4. **9/16 assessed**, no invented /20 total. Prior performance 2/4 was too confident.

Automation cognitive-load checklist: focus fail, chunking fail, grouping pass, hierarchy fail, one decision at a time fail, minimal choices fail, memory burden fail, progressive disclosure partial. Six failures suggest high load; this does not make every five-item menu defective.

First-timer: cannot predict whether Add saves or imports. Phone user: clipped current section and hidden core filters. Keyboard/low-vision user: working skip link, but unnamed sliders and low-contrast status text. These are expert walkthroughs, not participant observations.

## Reuse, design decisions and remaining scope

[Revised supplier assessment](designer-frontend-assessment.md#review-03-critical-reassessment): **selective pattern reuse**, not wholesale visual-system adoption. URL entry and progressive channel details help. Sports taxonomy, image-heavy hero, forced-dark overlay and DOM phrase replacement do not provide whole-app foundations.

The [new prototype](admin-prototype.html) composes nine families in EN/ES, light/dark, calm/expressive and coral/lime. Read the [specification](design-specification.md), [field ledger](field-ledger.md) and [coverage delta](coverage-review-03.md). New mockups are **in review**, never accepted by existence.

Open decisions: approve calm administration/expressive viewing or another consistent treatment; choose palette and font roles; validate terminology, Events placement and Connections overview. Existing application standards and URLs remain unchanged.

Pending: fluent Spanish review, VoiceOver/NVDA, representative novice sessions; unique compositions for events/overlays, W3U, searches/exclusions, stream/channel detail/reorder, guide rules/export/detail, playlist formats, individual integration editors, recording schedule/settings/parts, complete access activation/credentials/sessions, runtime setup and failure variants. Every item stays owned in the existing ten tasks.

**No complete whole-app design handoff or implementation is claimed.** The expanded matrix distinguishes source/live inspection from mockup and acceptance. Priorities remain #315 reliability/accessibility; #316/#318 ownership/state contracts; #317 localization; #319–#322 feature composition; #323 measured delivery; #324 integrated acceptance. No new issues or runtime/dependency changes are needed.
