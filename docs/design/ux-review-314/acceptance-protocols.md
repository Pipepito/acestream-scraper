# Remaining acceptance protocols · review 04

The design package can be reviewed now. It is not proof of implementation, whole-app accessibility conformance, usability, media reliability or measured performance. The following work stays in the existing issues; no participant results or equipment checks are invented.

## Confirmed implementation direction · #316 with #314

The owner has confirmed implementation of all three referenced designs—lime, coral/navy and cyan—with a user-facing interface selector. Use the [implementation scope](task-refinements-04.md#implementation-scope-confirmed-by-the-owner). Choosing one winning direction is no longer a prerequisite. Complete and refine their foundations during #316, retain the application identity and licensing requirements, and verify equal workflow coverage. The current prototypes cover coral/lime comparison variables; they do not already implement or validate cyan or the production selector.

Review the proposed Watch grouping for Events, outcome links under Integrations, all existing Settings deep links, and the shared editor ownership during implementation. Confirm consequential staged Save changes where source currently saves immediately. Independent API transactions remain separate. Remaining design refinement and research stay inside the existing implementation/acceptance tasks; no further standalone audit is required before starting.

## Implementation and regression ownership

| Existing task | Remaining work and observable exit evidence |
|---|---|
| #315 | Fix the private-HTTP recording opener, actual status contrast, Network/pagination phone clipping and guide-slider names. Investigate the new bulk-edit schema/repeated-batch source finding. Reproduce each at the implementation SHA; no claim from replacement screenshots. |
| #316 | Implement three coherent interface foundations and shared component variants; complete cyan coverage and define selector presets with #318. Refine IA and explicit-save proposals without removing capabilities. |
| #317 | Typed EN/ES resources, native error mapping, fluent Spanish review, plural/zero/unknown formatting, pseudo-locale expansion, unchanged original content and stable real-player/draft/selection state across preference changes. |
| #318 | Implement the three-interface selector and remembered preference, shell, deep links, shared settings/access/setup/recovery. Verify switching/persistence/fallback, permissions, transports, last-admin cases, stale runtime revisions and explicit proxy overrides. |
| #319 | Implement dashboard/Live TV/events/recordings. Use controlled media fixtures for DST, source changes, parts/gaps, cancellation, protection, recording priority, session leases and event fingerprint conflicts. |
| #320 | Implement channels/streams/guides/playlists; validate complete-catalogue and stream ordering, atomic Add and Link, optional reviewed similar names, source-qualified guides, exports, format/token/address dependencies and bulk contract correction. |
| #321 | Implement source/provider/W3U/search/exclusion/orphan/helper workflows; preserve guarded fetches, reviewed imports and installed/standalone isolation. Exercise real bounded workers with adversarial synthetic samples. |
| #322 | Implement integrations/system/WARP; validate capabilities and real owned device/media actions, jobs, diagnostics, storage bounds and saved/applied/startup distinctions. |
| #323 | Establish measured browser/network/media baselines and budgets at a known application SHA. Profile before choosing virtualization, memoization or lazy-loading changes. No performance regression was proved by this design audit. |
| #324 | Integrate all surfaces across three interfaces × EN/ES × light/dark × responsive layouts; verify switching/state continuity, supporting backend fixes and the normal application/Docker/browser matrix plus manual/participant evidence below. |

Every feature owner (#319–#322) delivers all three interfaces and the backend or incomplete-feature corrections needed for its workflows. #315/#320 retain the source-only F15 reproduction. #323 measures each interface and switching cost; a general slowdown remains unproven. Backend/API/schema changes require the normal contract, generated-client, migration and integration checks.

## Manual assistive technology protocol · #315/#317/#324

Equipment: keyboard plus a supported browser with VoiceOver on macOS/Safari, and NVDA on Windows/Firefox or Chrome; iOS VoiceOver and Android TalkBack for the phone flows. Record OS, AT/browser versions, exact build, route, language and theme. The isolated Chromium automation cannot hear or evaluate spoken output; an accessibility tree/axe result is not a screen-reader pass.

1. Start at the skip link, traverse landmarks/navigation, open and close the phone drawer, and follow a deep link. Confirm correct current-page announcement and focus return.
2. Open recording scheduling, identify every label/help/error, choose a repeated DST instant, submit invalid and valid times, cancel. Check that announcement identifies the error once and opening never creates a recording.
3. Create a draft, change language/theme, navigate away, Stay, then Discard. Confirm reading position and focus, preserved field values, clear modal title and trapped traversal. Inspect the real player for continuity while changing preferences.
4. Use only keyboard to select guide rows, resolve an ambiguous source-qualified result, handle a changed preview, reorder the complete catalogue and cancel. Confirm selection counts, order announcements and unchanged saved state.
5. Traverse both named export range controls with arrow/Home/End keys. Verify spoken names, values, valid zero and correct API date window.
6. Review permissions and one-time credential copy/revocation, service-stop consequences and both recovery confirmations. Confirm safe initial focus; no automatic destructive submit or leaked secret in announcements.

Exit: record pass/fail per step and issue-owned fixes. A blocker in a safety-critical step must be fixed and rerun. Fluent Spanish listening is required; English AT output with translated visible labels is insufficient.

## Zoom, reflow and physical device protocol · #324

At 1280 desktop width test actual browser zoom 200% and 400%, both themes/languages. Verify no two-dimensional scrolling for ordinary content, reachable actions, visible focus, open dialogs, advanced errors and sticky areas. Native date/time/select popups require manual inspection. Text stress and 320 CSS-pixel automated checks are useful but different evidence.

Use one small iPhone and one small Android device in portrait and landscape. Exercise the virtual keyboard on the source URL, long secret field, time inputs and remote host editor; ensure fields and action bar remain reachable. Open browser Back with a dirty draft and on-screen keyboard. Check touch targets and reduced-motion behavior with real OS settings. Device casting/remote/recording actions must run only against a separately authorized test installation and owned receivers, with isolated data.

## Nontechnical usability sessions · #316/#324

Recruit 5–6 participants who regularly watch online TV and do not administer servers; include at least two Spanish-dominant participants and one keyboard/assistive-technology user if available. Use synthetic names and an isolated installation. Obtain consent; record observations without personal data in public artifacts. No participants were recruited for this design pass.

Tasks (counterbalance the three interface choices between participants):

1. Find a channel and explain whether “ID found”, “signal verified” and “not checked” mean the same thing; filter while watching and return to the selected channel.
2. Schedule a programme over the DST repeated hour; explain what Stop, Cancel schedule, Delete files and Disable recordings each do.
3. Give a household member viewing and casting access without administration. Explain what a permission change does to sessions and player credentials.
4. Add a source, understand a preview error, save W3U without importing, then review only live entries. Find the installed versus standalone helper boundary.
5. Resolve two identically named guide candidates; reorder all channels, handle a stale conflict, and export a filtered playlist with matching guide IDs.
6. Identify a failed checker versus failed playback, a queued maintenance job, partially measured storage and saved-but-unapplied WARP exclusions. Explain the two recovery choices without executing either.

Capture unaided completion, wrong/destructive choices, recovery from errors, hesitation points, task time and 1–7 confidence. Test switching interfaces with a dirty form and active playback, explain the separate language/light-dark controls, and reopen to check the remembered choice. Ask which information helped, not only which style is prettier. Proposed acceptance target for owner review: no consequential mistaken action; at least 80% unaided completion on the core viewing/source/recording tasks; correct explanation of all destructive consequences. Small-sample findings are qualitative, not population statistics. Revise implementation from observed failures and rerun affected tasks.

## Performance protocol · #323

Use a known implementation SHA, fixed device/browser and network, with small and large synthetic catalogues. Record cold/warm route timing, transferred bytes, interaction latency while filtering/reordering, long tasks, memory growth and real player interruptions over refresh/language changes. Repeat comparable runs; separate backend delay, source availability, browser work and media startup. Preserve baseline traces privately. Set budgets from evidence and the target devices before optimizing. This design package establishes no numeric performance claim.
