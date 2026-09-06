# Mobile viewing review — 2026-09-06

## Scope and findings

Reviewed the built SPA against an isolated backend with seeded TV channels,
alternative streams, EPG programmes, a long channel name and a long source URL.
The existing local operator database was not modified.

| Pages | Finding and change |
| --- | --- |
| All routes | Nested shell padding reduced usable phone width; flatten the outer surface on phones. Keep the current destination visible in the app bar and enlarge buttons, icon actions and input text. Compact header overflow menus no longer consume half the action row. |
| Live TV (new) | Separate watching from channel management: searchable/favorite channel list, current/next programmes, stream counts, explicit missing-guide/no-stream states and direct channel links. |
| TV Channels, channel detail, Acestream Channels, Search | Keep or discover TV context in the player; show stream alternatives and the schedule. Copy/remote playback follow the selected stream. Release late session starts after closing/switching. |
| TV channel detail | Long stream names were squeezed alongside absolute-positioned actions; move actions below the stream on phones. |
| Overview, Scraper, EPG sources | Wide tables required sideways panning to reach status/actions. Stack labelled fields on phones; retain desktop tables. |
| EPG and guide details | Make scrollable day/section tabs visibly scrollable on phones, name the viewing timezone, refresh programmes and advance the on-air marker while idle. |
| Playlist, Integrations, WARP | Checked populated/available states and shared layout at phone, landscape and desktop sizes. |
| Settings | A long stream-template example was clipped; allow wrapping within it. Shared dialog and input changes also apply here. |

## Verification

- Read-only browser sweep: 13 routes (including TV and EPG detail pages) at
  320, 390, 844 landscape and 1440 pixels. Checked headings, screenshots, document
  overflow and uncaught browser errors. Screenshots are local ignored artifacts.
- `cd e2e && npm run test:mobile`: deterministic tests using Chromium, WebKit and
  Firefox; small phone, phone, tablet and desktop; light/dark themes and four
  device timezones. See `e2e/README.md` for setup and limitations.
- Frontend Jest includes assigned/unassigned IDs, stream selection, late session
  cleanup and the daylight-saving transition with an advancing clock.
- Frontend typecheck/lint/build, E2E typecheck, the quick canonical cross-stack
  gate and strict legacy-path guard.

## Remaining validation

The browser suite simulates player responses and the isolated backend has no
live AceStream engine. Actual stream decoding, buffering, device rotation during
live playback and physical iOS/Android device behavior still require hardware and
the live-stack suite. The UI does not infer video quality from metadata or claim
that a stale online check guarantees playback.
