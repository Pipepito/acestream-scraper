# Handoff — media integrations (web player, remote players, Jellyfin/Plex tuner)

Written 2026-09-04, at the end of the build. The feature is complete and unpushed
on `feature/media-integrations`. This document is what the next agent needs to
pick it up.

## Where things stand

| | |
|---|---|
| Branch | `feature/media-integrations`, 94 commits and 201 files ahead of `origin/develop` (+24,317 / −3,431) |
| Working tree | clean |
| Pushed | no. No pull request exists. |
| Backend tests | 925 pass (`backend/tests`, Docker tests excluded) |
| Frontend | 55 suites / 334 tests, lint at `--max-warnings=0`, typecheck, and build all clean |
| CI guards | quick canonical suite, legacy-path guard, command builder, Docker manifest metadata, Docker docs contract, wiki dry run — all pass |
| Schema | single Alembic head `20260903_1200`; `test_schema_parity.py` passes |
| Generated artifacts | `backend/openapi.json` and `frontend/src/types/api-generated.ts` verified byte-identical to a fresh regeneration |

`origin/develop` was merged into this branch on 2026-09-03 at `f88e458`, so it is
current with the ARM64 engine change (`166b5cd`, the `oci-image` distribution).

## What was built

Three features the user asked for, plus one engine fix, built as four sequential
plans.

1. **Web player.** ffmpeg turns an AceStream engine stream into HLS on disk; the
   browser plays it with hls.js. One ffmpeg process per viewer, a session state
   machine with limits and stall detection, and a reaper. A visible Play button
   sits in Acestream channel rows, TV channel pages and search.
2. **Remote players.** VLC over its Lua HTTP interface and Kodi over JSON-RPC:
   add, test, play, pause, stop, volume, and a network scan that finds them.
3. **Tuner and media servers.** An HDHomeRun-style tuner at `/tuner/*` that
   Jellyfin and Plex consume, an XMLTV guide keyed to the tuner's channel
   numbers, Jellyfin registration and guide refresh over its API, paste-ready
   Plex instructions with optional token-driven reload, and a ten-minute sync job
   that acts only when the lineup or guide actually changed.
4. **Engine fix.** `ACESTREAM_BIND_ALL` defaults to true on amd64 so players on
   Tailscale, CGNAT or unusual Docker networks are not refused by the engine's
   own address filter.

## The design record, now tracked in the repo

These were local scratch files during the build. They are committed so the work
can be handed over. `.gitignore` still ignores everything else under
`docs/superpowers/`.

- `docs/superpowers/specs/2026-09-03-media-integrations-design.md` — the spec.
  **This is the binding authority.** When a plan and the spec disagree, the spec
  wins. Sections: 2 research facts, 3 architecture, 4 shared foundation
  (4.1 engine client, 4.2 relay, 4.3 proxy trust, 4.4 token and network policy,
  4.5 ffmpeg, 4.6 startup upgrade, 4.7 engine fixes), 5 web player, 6 remote
  players, 7 tuner and media servers, 8 UI, 9 wiring, 10 testing, 11 docs,
  12 decisions.
- `docs/superpowers/plans/2026-09-03-media-integrations-{1-foundation,2-web-player,3-remote-players,4-tuner-media-servers}.md`
  — the four implementation plans, all executed.
- `docs/superpowers/specs/engine-spike-results.md` — the research that settled the
  ARM question. Read it before anyone proposes an engine bump again.
- `docs/superpowers/sdd/*-ledger.md` — the execution ledgers, one per plan. Every
  ruling made during the build is in these, with its reasoning and what it costs
  if wrong. Read the rulings before reversing a decision that looks odd.
- `docs/superpowers/sdd/final-verification.md` — the merge-readiness write-up.

## Decisions the user made, which are settled

Do not reopen these without asking:

- The web player always transcodes to HLS with ffmpeg. No engine-side transcode
  (broken on amd64 3.2.11, premium-gated on ARM) and no direct MPEG-TS to the
  browser.
- Jellyfin gets both an HDHomeRun tuner (the default) and an opt-in M3U mode.
- The Play button is visible in channel rows; the TV-link action moved into the
  row overflow menu.
- Remote player drivers are VLC and Kodi. No Chromecast or DLNA.
- Everything streams through a backend byte relay rather than pointing clients at
  the engine, which sidesteps both the engine's address filter and Acexy's
  missing CORS headers.

## The ARM engine question, already answered

Someone will ask why ARM playback is not simply fixed by a newer engine. It was
investigated properly:

- The engine-only AceStreamCore download channel is frozen at 3.1.80 (2023).
- Newer official engines ship inside the Ace Stream Android app. 3.2.18 run
  headless answers every playback request with `mod_detected`, and with the APK's
  real identity it answers the same premium denial as 3.1.80.
- AceStream staff state the policy directly (forum threads t3928, t3945, t4002):
  on Android, live playback outside their own ad-supported player is Premium-only,
  in old and new versions.
- The user resolved arm64 separately on `develop` by moving to the community
  distribution `jopsis/acestream:v3.2.17-fix`, digest-pinned as an `oci-image`.
  Its API and startup are verified; **playback is not**. armv7 still runs the
  official premium-gated APK.

Never propose reporting a different app identity to pass the modified-version
check. It is a licensing grey area and it only leads to the premium gate anyway.

## Review history

Every task was reviewed as it landed, each plan got a whole-plan review with a
fix wave, and the branch got a final six-lens review whose findings were each
put to a three-seat adversarial panel that defaults to refuting. 33 findings,
9 refuted, 24 confirmed and all fixed. The most serious was a saved Jellyfin API
key or Plex token being sent to any address the caller named — the same hole that
was found and fixed for remote players one plan earlier, and not carried across
when the media-server code was written. If you add another integration that
stores a secret, check this class of bug first.

## What has never been executed — read this before promoting to `main`

The automated evidence is strong but narrower than it looks.

1. **No real Jellyfin, Plex, Kodi or VLC has ever been contacted.** All four are
   reached only through hand-written `httpx.MockTransport` fixtures that encode
   this implementation's *belief* about those APIs: paths, auth headers, DVR
   discovery, refresh semantics, error bodies. A wrong header or a differently
   nested response passes every test here and fails on first contact. Four
   independent chances to have shipped something that never worked.
2. **The two web player playback e2e tests have never run anywhere.** They skip
   when `/api/v1/player/capabilities` reports no ffmpeg, and the build machine had
   none. Unproven end to end: ffmpeg against a live engine stream, the HLS it
   writes, the backend serving it, hls.js reaching a playable state, and the
   reaper stopping the engine when the dialog closes.
3. **The HDHomeRun emulation has never been consumed by a real tuner client.**
   Only JSON shapes are asserted. "Plex does not see the tuner" is a plausible
   outcome that no current test can distinguish from success.
4. **The network scan has never run against a real LAN.**
5. **The browser journey has not re-run** against roughly 50 commits of frontend
   polish since its last recorded run.

Three tests under `backend/tests/docker` fail on Apple Silicon, all on one
host-architecture refusal: the amd64 ZeroNet payload cannot be built on aarch64.
Those files are byte-identical to `develop`, so this branch is not the cause.

## Suggested next steps

1. Push the branch and open a pull request into `develop` (needs the user's
   go-ahead; it had not been given as of this writing).
2. Run the e2e journey on a host with ffmpeg, or `npm run test:docker`, and make
   the two playback tests actually execute. Note the deterministic variant also
   self-skips under `E2E_TARGET=docker`, so that path covers only the real-engine
   variant.
3. Smoke against one real Jellyfin and one real Plex. This is the highest-value
   hour anyone can spend on this feature.
4. Only then consider promoting to `main`.

## Working conventions used here

- Backend tests from the repo root: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/<file>`.
  `backend/tests/docker` needs a Docker daemon and is excluded from normal runs.
- HTTP 401 is reserved for the API token. Upstream and engine failures are 502
  with a distinct error code.
- DB-touching handlers are sync `def`; relays are async and touch no DB. A
  request-scoped session must never be pinned for a stream's lifetime.
- The `/tuner/*` routes are deliberately token-free and gated by
  `TUNER_ALLOWED_NETWORKS`, checked against both the raw peer and the forwarded
  client. The catch-all `/tuner/{path:path}` must stay the last route in
  `tuner.py`.
- The app owns forwarded-header parsing; uvicorn runs with `--no-proxy-headers`.
- Frontend: TypeScript only, named prop interfaces, no `any`, at most two visible
  row action buttons with the rest in `RowActionsMenu`, `useConfirm` for
  destructive actions, plain language in user-facing copy.
- After a DTO change, regenerate `backend/openapi.json` and
  `frontend/src/types/api-generated.ts` and commit both.
