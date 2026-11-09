# Design verification · review 04

> Review 06 is the current design-only continuation: [package](README.md), [simplified ownership](before-after-map.md), [shared presets](shared-foundations-06.md), [graphics](asset-selection-06.md) and [new evidence](verification-review-06.md). Earlier closure/implementation-next language and historical passing counts do not authorize application work or establish current acceptance.
Final design-only evidence recorded 2026-11-07 18:30 UTC. Worktree: `/tmp/acestream-ux-review-314`, branch `design/ux-review-314`, starting design commit `c545de3b58ccac03686add849289ccf944a9b6cc`. The commit containing this report records the tested final design files; hashes below identify the browser inputs without a circular self-reference.

Application evidence remains pinned to develop `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`. Remote develop/main/design were rechecked during this pass: `cf952af` / `7fe2a4c` / starting `c545de3`. No newer application delta was found. The design branch retains its earlier application tree; no implementation was merged into it. The main checkout remains at `7ccf16d383758aeeb78845e20e3716ddf97df10d`, with no user/app changes made by this work.

The live installation's exact SHA is unknown. **No installation request or live action was made in this pass.** All current browser evidence uses synthetic local fixtures and intercepted requests. No supplier code was executed. Earlier live observations are retained as historical evidence, not re-certified at a new installation revision.

## Owner scope amendment · documentation only

After the completed composition delivery at `9618a6957c9fd528cd2b38aa0a62f0512145356e`, the owner closed the design-only phase and confirmed three selectable interface designs plus supporting backend/incomplete-feature fixes for the next implementation run. The [updated task scope](task-refinements-04.md#implementation-scope-confirmed-by-the-owner) supersedes the earlier single-direction decision.

This amendment changes seven Markdown handoff files only. HTML/CSS/JavaScript, fixtures, exports, source-contract appendices and application/runtime files are byte-identical to the composition baseline. Current amendment checks: **2,842 local links and 501 fragments, zero failures; seven generated files, zero drift; repository documentation validation and staged whitespace passed.** Commands: `python3 docs/design/ux-review-314/check_artifacts.py --output /tmp/ux-review-314-scope-checks`, `python3 scripts/ci/validate_documentation.py`, and `git diff --cached --check`. The browser results below remain evidence for the unchanged prototypes; they were not rerun or relabelled as validation of the new selector or cyan interface. Both, and any backend fixes, require implementation and the full application completion gate in the existing tasks. No new design-audit round is required before starting.

## Final results

| Check | Actual final result | Scope and limits |
|---|---|---|
| Workflow layout/state matrix | **8,260 passed; 0 failed** | All 144 workflows; EN/ES, light/dark, 320/390/768/1440 px ready layouts; advanced fields; calm/expressive × coral/lime phone comparisons; every declared state in both languages/themes at 390 px. Checks document overflow **and individual control bounds/clipping**, one main/H1 and document language. |
| Workflow axe | **289 scans; 0 violation cases** | Every workflow in desktop EN/light and phone ES/dark with advanced fields expanded, plus a destructive confirmation. WCAG 2 A/AA, 2.1 AA, 2.2 AA and best-practice rules in the new suite. Incomplete results retained below; this is not a conformance claim. |
| Interaction contracts | **69 passed; 0 failed** | Actual local input, selection, keyboard, focus, validation and navigation actions; no server/media simulation claimed as integration. |
| Reflow/text enlargement | **14 passed; 0 failed** | Seven demanding flows at 320 CSS px and seven with 200% CSS text enlargement. This is not native browser zoom. |
| Synthetic exports | **288 generated** | Each workflow: 1440 px EN/light and 390 px ES/dark, ready state. Other states remain executable through the selector; exports are not evidence that every state received a saved screenshot. |
| Direct local-file preview | **3 entry points opened offline; 0 script errors** | New gallery, workflow prototype and original index loaded through local file URLs; workflow scripts initialized. |
| Expanded gallery | **288 images decoded at 4 widths; 0 failures** | 320/390/768/1440 px; no broken images or document overflow. |
| Critical-state axe | **46 scans; 0 violation cases** | 23 materially different states × EN/light desktop and ES/dark phone. |
| Computed contrast | **52 pairs passed; 0 failed** | Both themes × coral/lime; text, semantic statuses, selection, focus and control boundaries. Minimum text **5.069:1**, minimum UI/focus **3.672:1**. |
| Existing administration regression | **928 layout/state cases, 72 axe scans, 14 interaction checks passed** | Rerun this pass after correcting the obsolete manual Cast action. The administration prototype is still historical, incomplete coverage on its own. |
| Historical viewing and gallery regression | **96 layout cases and 39 images at 4 widths passed** | Preserves older reference artifacts; known historical placeholder/state limitations remain. |
| Artifact links and coverage | **2,834 local links, 494 fragments; 0 failures** | Current HTML/Markdown/CSS links; 144 screens, 288 exports, 47 runtime options; all 95 inventoried control-bearing modules mapped. External GitHub links are source-pinned; this is not an HTTP crawl of every external link. |
| Generated drift | **7 files matched; 0 drift** | Regenerates data, per-field specification, matrix, schema appendix, module map and gallery from the pinned source. |
| Documentation, syntax and whitespace | **Passed** | Repository documentation validator, JavaScript syntax and staged whitespace check; no application gate was run under the explicit design-only waiver. |

Final new suites recorded **0 script errors, 0 console warnings/errors and 0 blocked unexpected requests**. No automated case was skipped inside the stated design matrices. Browser route interception would abort all nonlocal or non-GET requests, and the prototype additionally uses `connect-src 'none'` and contains no API, media, persistent storage or recovery client.

Environment: macOS, Python 3.12, cached Playwright 1.61.0, Chromium 149.0.7827.55, axe-core 4.14.0. No application dependency or lockfile was changed. Headless Chromium was launched with the required tool permission; no daemon or live service was started.

## What the interaction checks establish

The named checks include dirty navigation Stay/Discard; independent pending section saves; locale/theme draft, focus, selection and player-illustration preservation; safe modal initial focus, Tab/Shift+Tab containment, Escape and focus return; phone drawer; password confirmation/Unicode length; DST ordering; named export ranges and units; explicit row selection and stale-selection clearing; complete local reorder through buttons/keyboard with cancel; immediate favorite and Enter/blur number timing; similar-name opt-in; event input modes; standalone isolation and localized local-file input; initial/blocked/unknown states; reduced-motion preference; no local persistence or media element.

These are prototype behaviors. A retained static player node is **not** verified HLS continuity. Local reorder is **not** backend atomicity. A disabled command is **not** server authorization. A synthetic preview is **not** regex execution or a source import. Every integrated contract remains with its feature task.

## Visual author review and scanner triage

All 144 desktop/phone composition pairs were inspected as 12 contact sheets for structure, hierarchy and cross-screen consistency. Representative full-size screens were inspected, including recording schedule, access, reorder, standalone helper, empty home, blocked activation, unknown statistics, date-only event, oversized sample, finalizing recording, guide export, bulk properties, failed playback and destructive confirmation. This is author review, not a claim that every pixel was inspected at full resolution or that users approved the designs.

Visual review corrected contradictory empty-state headings, a mismatched event fixture title, unsupported manual Cast entry, standalone phone navigation, novice-facing adapter language and premature-looking result copy. Consequences now say “After this action” before submission. Native labels, range units/plurals and a missing review-notice landmark were corrected and rechecked. The staged whitespace check then found one trailing space on JavaScript line 201. It was removed with no other source-token or rendered-content change; syntax and the 69-interaction/14-reflow focused suite passed again, and staged whitespace was rechecked. The local normalization record preserves before/after hashes. Exploratory/interrupted runs are not included in the final counts above.

Axe left **5 workflow scan cases** incomplete for color contrast: the decorative, `aria-hidden` player triangle in the two player compositions/languages, and confirmation-body background inference under the modal. The critical-state suite retains the corresponding four player-triangle incomplete cases. The triangle is a noninteractive illustration; modal text was visually inspected and uses the measured muted/surface token pair. These are documented manual triage items, **not silently counted as axe passes**. They do not establish accessibility conformance; actual AT/zoom/device evidence remains outstanding.

## Commands and retained logs

From the design worktree root. `UX_REVIEW_AXE` below denotes the existing cached `frontend/node_modules/axe-core/axe.min.js` in the main checkout; it is an explicit path, not a dependency installation.

```bash
python3 docs/design/ux-review-314/compose_workflows.py
python3 docs/design/ux-review-314/check_design.py --workflows-only --screenshots --axe "$UX_REVIEW_AXE" --output /tmp/ux-review-04-completion
python3 docs/design/ux-review-314/check_gallery.py --axe "$UX_REVIEW_AXE" --output /tmp/ux-review-04-quality
python3 docs/design/ux-review-314/check_design.py --axe "$UX_REVIEW_AXE" --output /tmp/ux-review-04-historical
python3 docs/design/ux-review-314/check_artifacts.py --output /tmp/ux-review-04-artifacts
python3 scripts/ci/validate_documentation.py
node --check docs/design/ux-review-314/workflow-engine.js
git diff --check
git diff --cached --check
```

Machine logs remain local, outside Git: `/tmp/ux-review-04-completion/workflow-checks.json`, `workflow-layout-stage.json`; `/tmp/ux-review-04-quality/gallery-checks.json`; `/tmp/ux-review-04-historical/checks.json`; `/tmp/ux-review-04-artifacts/artifact-checks.json`; representative final state captures, scanner triage and `file-preview.json` in `/tmp/ux-review-04-final-visual/`. The committed 288 JPGs are deliberately synthetic gallery deliverables, not installation captures or temporary browser reports.

## Exact remaining evidence and ownership

- **#315/#320:** prior private-HTTP recording crash, actual app contrast/clipping/slider-name defects and new F15 bulk field/request mismatch remain unimplemented. F15 is source evidence, not a live reproduction.
- **#316:** owner approval of palette, typography, calm/expressive emphasis, IA and any staged-save changes. No rebrand or application-standard change is approved.
- **#317:** fluent Spanish review, production typed localization and actual state/media preservation. Draft bilingual copy is not participant validation.
- **#318–#322:** application implementation and all media, security, persistence, recovery, device and server integration evidence.
- **#323:** measured performance at a known implementation SHA and target devices. Whole-app slowdown remains unproven.
- **#324:** actual screen readers, native 200%/400% browser zoom, physical iPhone/Android and nontechnical participant sessions. The available native computer surface reported the Mac locked and automatic unlock failed; no accessible app/browser surface was available. No VoiceOver, NVDA, TalkBack, physical-device or native-zoom pass is claimed. Equipment, steps, observations and exit criteria are specified in [acceptance protocols](acceptance-protocols.md).

The maintainer explicitly authorized these design/docs/prototype checks instead of the full application/Docker/E2E matrix for **this design-only task**. That matrix was not executed and is not reported as passed. The waiver does not transfer to implementation. No deployment, merge, Jenkins action, image publication, application edit, live playback/recording, settings mutation, device discovery/control, notification or recovery occurred.

## Tested browser-input hashes

SHA-256 values for the final files exercised by the new matrix:

| File | SHA-256 |
|---|---|
| `workflow-prototype.html` | `dba02559e4f2fb1b17e3f01fd673e226b6171f226638c6a43e884902cb60d397` |
| `workflow-prototype.css` | `45312ab6b7fef9ee6b2ebd0a29eab93997671cdf70d2bf824a430a168e1e0823` |
| `workflow-engine.js` | `db6e5f70495604a1ac74ccaf913d2171d1287618df33601310a7947704e245c9` |
| `workflow-data.js` | `faef159e7ee8b73e1aa76e2e5f51ab0d861c17e8ade5f13acaeeaa9bcb967ddf` |
| `workflow-data.json` | `045cf601b5ae859cd3164e885175e9a7f97f7d4102d58b559a1fbf6cb6619f71` |
| `admin-prototype.css` | `29d476c655838916e41db0e30a4257d212eb92c807ee814af79532261167b588` |
| `compose_workflows.py` | `670d7a9ac208df5a4d36e64716af67afbb69abef59620681ab6e142ed1f0673d` |
| `check_workflows.py` | `b7573db5e5f3610e91340e67345be32947a3dce8c5a2b5c46aeb695b68b20319` |
| `check_gallery.py` | `81d31d8ea4c28933229d4c2a2eb03f93bcd9f88671545c3448b50dba6bbc33da` |
