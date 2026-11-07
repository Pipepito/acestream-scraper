# Sanitized audit evidence — review 03

Date: 7 November 2026. Initial source baseline: 7ccf16d383758aeeb78845e20e3716ddf97df10d; final remote cf952af is separately reconciled in the [current-source delta](current-source-delta.md). Live commit unknown. All live observations use English UI and reduced motion in a fresh Chromium context. Installation addresses, source identities, channel lists, account data and raw logs are intentionally omitted.

## E01 Recording opener

1. Open a supported private-IP HTTP installation → Live TV.
2. Open a channel's Record action. Do not confirm or submit.
3. Observe an uncaught “crypto.randomUUID is not a function” and an empty document body.
4. Browser reports isSecureContext=false; typeof crypto.randomUUID=undefined; typeof crypto.getRandomValues=function.
5. [RecordingDialog.tsx](../../../frontend/src/components/recordings/RecordingDialog.tsx), line 21: unguarded initializer. [RecordButton.tsx](../../../frontend/src/components/recordings/RecordButton.tsx) opens the form and reads the current programme before submission.

1440×1000 light. Body text length after failure: 0. No write request sent. Scope: opening/cancelling, not capture correctness. HTTPS behavior not re-tested.

## E02 Contrast and labels

Light status colors independently recomputed using sRGB relative luminance: white against #1f8f59 ≈4.09:1; #1f8f59 against #fbfdff ≈4.01:1. Fresh axe candidates occur on Sources, Guide, Playback, Media servers, WARP and System. Source: [theme.ts](../../../frontend/src/theme.ts), success icon token and palette mapping. These are normal-size text examples, not disabled text.

Guide → Export, 1440×1000 light: both range inputs have null aria-label, null aria-labelledby and zero associated labels. Values initially -1 and 7. Source: [EPGXmlOutputPanel.tsx](../../../frontend/src/components/EPGXmlOutputPanel.tsx), line 99. They need distinct start/end names and meaningful localized value text. A single ArrowRight trial did not establish a separate keyboard defect; full keyboard semantics remain a follow-up.

## E03 Reflow

- Settings → Network, 390×844 light. Tab bounds: x316.28, width 101.95, height 48. Nearest scroll viewport: x52, right 338; ancestor panel ends 378. Only about 22 px of the selected tab is visible. Horizontal scrolling is available; “unreachable” would overstate this.
- TV Channels, 320×740 light. Next control bounds: x268.45, width 64, height 44; right 332.45 exceeds the viewport by 12.45 px. Document overflow is false because ancestors clip. Current accessible name is “Go to next page”. Initial harness searched visible text “Next” as the accessible name and failed; corrected rerun passed the locator and measured the clipping.
- Live TV, 390 light. Scrolled guide control measured approximately 166×44 px. Offscreen content-visibility scanner candidates do not prove undersized visible controls.
- Phone TV-channel Search/Category/Status controls are in a collapsed panel. [TVChannels.tsx](../../../frontend/src/pages/TVChannels.tsx), lines 219/276/292. This differs from the repository's core-filter requirement.

## E04 Settings and navigation

Sources inspected: [Settings.tsx](../../../frontend/src/pages/Settings.tsx), [GuideMatchingFields.tsx](../../../frontend/src/components/GuideMatchingFields.tsx), [RecordingSettingsFields.tsx](../../../frontend/src/components/recordings/RecordingSettingsFields.tsx), [NetworkSettingsFields.tsx](../../../frontend/src/components/settings/NetworkSettingsFields.tsx), [navItems.tsx](../../../frontend/src/components/layout/navItems.tsx).

Automation mounts recording/guide/checker/schedule/notification settings. Guide matching mutates on toggle; recording has a separate Save; interval saves are independent; runtime changes require restart. Public address explicitly explains saved override but also exposes the fallback. Events currently belongs to Manage in navigation; Watch is a proposal, not current behavior.

## E05 Positive and bounded checks

Skip link is first keyboard focus and targets main-content. TV-channel detail, guide-channel detail and ready-state /startup were opened read-only. Fresh sweep: 49 cases, 33 without axe violations, 16 with candidates, 0 uncaught page errors during route loading. The separate recording opener produced the known exception. 100 off-installation GET requests were blocked during the sweep, principally optional assets; their absence is not a visual finding.

## Retained private evidence

Temporary local directory: /tmp/ux-review-fresh-314/private/. Contains survey JSON, individual DOM/axe records, screenshots and corrected targeted measurements. Do not commit or attach it to GitHub. Reproduction harnesses are local because they target the owner's installation. Public design checks in [check_design.py](check_design.py) are fully isolated and contain no live origin.

These observations are not real-device, screen-reader, performance, account-enabled role, security, playback or recording certification.
