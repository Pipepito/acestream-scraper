# SDD ledger — plan: docs/superpowers/plans/2026-09-03-media-integrations-2-web-player.md

Spec: docs/superpowers/specs/2026-09-03-media-integrations-design.md (read; binding authority, sections 4.5, 5, 8, 10).
Branch: feature/media-integrations, checkout /Users/pipepito/Code/acestream-scraper-alt. Plan 1 complete at 06ad6f3 (+ final fix wave 4a9dbf4..690e3ac). Base commit before Task 1: see Task 1 line.

## Preflight conflict scan (2026-09-03)

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T1 → T2 | `docker/vendor/ffmpeg/ffmpeg-8.1.2.tar.xz` + `docker/manifests/ffmpeg.json` (version, sha256, file) consumed by `build-ffmpeg.sh`/`ffmpeg-builder` stage | Consistent (same file name and sha256 in both tasks) |
| T2 ↔ Plan 1 T2 guard | T2 adds `IMAGE_HAS_FFMPEG` export to entrypoint.sh; Plan 1's `test_entrypoint_defaults_match_settings_defaults` derives the media knob set from Settings and checks both ways | Conflict risk: an extra export inside the media block would fail the guard |
| T2 → T3 | runtime-base sets `FFMPEG_BINARY_PATH=/usr/local/bin/ffmpeg`; T3 `PlayerService` resolves `settings.FFMPEG_BINARY_PATH` then `shutil.which("ffmpeg")` | Consistent |
| T3 → T4 | `PlayerService.start/stop/get/list`, `PlayerSession` fields, `PlayerLimitReached`, error codes; T4 endpoints map them to DTOs and 409/502 | Consistent (names fixed in T3 brief Interfaces) |
| T4 → T5 | `/api/v1/player/sessions` (POST 201 body with `id`, `playlist_url`, `state`, `error`), `GET /capabilities`, `DELETE /{id}` 204 | Consistent |
| T5 → T6, T7 | `StreamPlayerDialog {open, contentId, title, onClose, extraActions?}`, `usePlayer` | Consistent |
| T6 ↔ T7 | T6 edits ChannelRowActions/ChannelCardList/ChannelTable/AcestreamChannels + e2e channels page object; T7 edits TVChannelDetail/TVChannelsTable/TVChannels/Search | Disjoint files |
| T8 ↔ T2 | both touch docs: T2 the Docker docs contract phrases, T8 wiki/builder | Disjoint pages; T8 must keep validate_docker_docs_contract.py green |
| T9 ↔ T4/T5 | contracts file asserts exact key sets of the T4 DTOs | Consistent if T4 DTO fields are unchanged; verify at T9 review |
| T3 test helper | `backend/tests/fake_ffmpeg.py` writes segments; T4 tests reuse it | Consistent |

Ruling: Task 2 places `IMAGE_HAS_FFMPEG` next to `IMAGE_HAS_ACESTREAM`/`IMAGE_HAS_ACEXY` (image-flag block), NOT inside the media knob block that `test_entrypoint_defaults_match_settings_defaults` derives from Settings; if the guard still trips, extend the guard's exclusion list rather than moving the flag — cost if wrong: one test edit.
Ruling: the FFmpeg source tarball already downloaded in the session scratchpad is reused for Task 1 (hash verified against the plan's sha256) — no re-download.
Task 1: implementer DONE (commits 690e3ac..7305397) — 684/684 backend tests passing (excl. docker daemon tests); ffmpeg vendor tests: 2/2 green for this task's scope, 2 intentionally still red pending Task 2.
Task 1: review APPROVED — spec ok; critical 0, important 0, minor 5
Task 2: implementer DONE (commits 7305397..ae34cf4) — 686/686 backend tests passing (excl. docker daemon tests); ffmpeg_build docker smoke green on all three platforms (amd64 1:52, arm64 0:59 cold, arm/v7 1:04) plus a runtime-base image check (IMAGE_HAS_FFMPEG=true, static ffmpeg 8.1.2).
Task 2: review NEEDS FIXES — spec ok; critical 0, important 1, minor 7
Task 2: fix round 1 implementer — entrypoint.sh now clears FFMPEG_BINARY_PATH when nothing executable sits at the resolved path (so the app gets Settings' empty default and falls back to shutil.which instead of a dead path), the substring guard was replaced by two tests that actually run entrypoint.sh and assert the exported env in both states, and the ffmpeg section of docs/ops/multiarch-manifest-updates.md records the contract (commits ce31928..ce31928)

Task 2: re-review round 1 — 1 addressed, 0 open
Ruling (Task 2 deviations, accepted): ffprobe JSON writer instead of the brief's `split() == ["h264","ac3"]` (the csv/flat writers duplicate streams for a container with programs — the brief's assertion cannot pass); the extra spec-4.5 argv smoke case stays (it is what catches a missing muxer/encoder before Task 3) with a keep-in-sync comment; install-metadata.txt under /opt/ffmpeg/bin/ stays because Task 1's test pins the COPY line. Cost if wrong: one test edit.
Ruling (Task 1/2 minors): the .gitattributes diffability fix (`text diff` so vendored SHA256SUMS/README render in PRs), the `--user $(id -u):$(id -g)` on the ffmpeg smoke bind mount, the static-binary assertion, and the native-only execution default for the three-platform ffmpeg smoke are carried to Task 9's carry-forward wave. Recorded so they are not lost.
Interruption 2026-09-03: the run died at Task 3 (impl:3 hit a 500, its escalation hit the Fable usage limit). Escalation/fix-round model switched from fable to opus in the workflow script; resumed from run wf_a33512a1-bb7 (tasks 1-2 replay from cache).
Task 1: review APPROVED — spec ok; critical 0, important 0, minor 4
Task 2: implementer DONE (commits 7305397..ce31928) — replay dispatch: work already committed at HEAD, re-verified file-by-file against the brief, no new commit needed; 688/688 backend tests passing (excl. docker), ffmpeg docker smoke 4/4, cold cross-builds arm64 0:59.6 / amd64 1:22.9 / arm-v7 1:03.1 (no platform skipped, sizes match spec 10.0/7.4/5.3 MB), test_settings_env guard untouched and green.
Task 2: review APPROVED — spec ok; critical 0, important 0, minor 7
Task 3: implementer DONE (commits ce31928..cba624e) — 705/705 backend tests passing (excl. docker daemon tests); player service 14/14 green (fake-ffmpeg child process, mutation-checked), plus the carry-forwards: .gitattributes diffability + git check-attr test, ffmpeg docker smoke re-run green on arm64 with --user and a busybox static-binary check, and the ARM mod_detected refusal pinned in test_engine_client.
Task 3: review NEEDS FIXES — spec ok; critical 0, important 2, minor 8
Task 3: fix round 1 implementer — _launch now aborts (releasing the engine handle, killing/removing anything it created) when the reaper stopped the session mid-launch, teardown's kill/engine-stop extracted into _terminate/_stop_engine_session, and open_session joins only starting/ready sessions so reopening a failed channel retires it and really retries; 2 new tests (commits cba624e..45eccd0)
Task 3: re-review round 1 — 2 addressed, 0 open
Task 4: implementer DONE (commits 45eccd0..32936db) — 716/716 backend tests passing (excl. docker); new test_player_endpoints.py 8/8 green over 5 consecutive runs with no orphaned ffmpeg, plus test_api_token_auth/test_error_contracts/test_player_service.
Task 4: review NEEDS FIXES — spec ok; critical 0, important 1, minor 6
Task 4: fix round 1 implementer — segment handler now stats once in try/except OSError and passes stat_result= to FileResponse (plus an explicit S_ISREG 404), closing the TOCTOU that surfaced deleted/non-regular segments as a 500 instead of 404; regression test added (commits 32936db..4a1792c)
Task 4: re-review round 1 — 1 addressed, 0 open
Task 5: implementer DONE (commits f88e458..f987ff2) — frontend 49 suites / 282 tests pass (8 new), lint + typecheck clean, backend 726 passed.
Task 5: review NEEDS FIXES — spec ok; critical 0, important 1, minor 7
Task 5: fix round 1 implementer — split the StreamPlayerDialog release test so the pagehide listener, the Close-path release and the exactly-once guard each fail on their own (mutation-verified); no production code changed (commits f987ff2..7b899b4)
Task 5: re-review round 1 — 1 addressed, 0 open
Task 6: implementer DONE (commits 7b899b4..98e57a3) — frontend 50 suites / 287 tests pass (ChannelRowActions/Table/CardList/page: 23/23), lint + typecheck clean, e2e tsc clean, backend 726 passed.
Task 6: review APPROVED — spec ok; critical 0, important 0, minor 4
Task 7: implementer DONE (commits 98e57a3..5eea19b) — frontend 50 suites / 293 tests pass (the 4 touched suites 57/57, 7 new assertions RED first), lint + typecheck clean, backend 726 passed.
Task 7: review APPROVED — spec ok; critical 0, important 0, minor 6
Task 8: implementer DONE (commits 5eea19b..da1f825) — new runtime-guards test green (RED confirmed first), full guards file 38/38, command-builder validator + wiki dry-run green, full backend suite 727/727 passing (excl. docker).
Task 8: review NEEDS FIXES — spec ok; critical 0, important 2, minor 2

Task 8: fix round 1 implementer — corrected wiki/Web-Player.md's API-token paragraph (the hls.js path sends X-Api-Token as a header, Safari/iOS native HLS gets ?token= on the stream address and on each segment line); left notes.publicBaseUrl's "Integrations → Public address" wording as is (spec- and plan-mandated; the page lands in plan 3 task 6 on this same branch before any docs publish) with the reasoning in the report (commits da1f825..574016a)
Task 8: re-review round 1 — 2 addressed, 0 open
Task 9: implementer DONE (commits 574016a..c2bbf46) — full backend suite 747/747 passing (excl. docker) plus ffmpeg vendor 4/4; frontend 50 suites / 293 tests, lint+typecheck+build clean; quick profile, docker-manifest and command-builder validators all green; new contracts file 14/14 (mutation-checked).
Task 9: review APPROVED — spec ok; critical 0, important 0, minor 5
Task 1: complete (690e3ac..7305397)
Task 2: complete (7305397..ce31928)
Task 3: complete (ce31928..45eccd0, fix round 1)
Task 4: complete (45eccd0..4a1792c, fix round 1)
Task 5: complete (f88e458..7b899b4, fix round 1) — re-run after the develop merge
Task 6: complete (7b899b4..98e57a3)
Task 7: complete (98e57a3..5eea19b)
Task 8: complete (5eea19b..574016a, fix round 1)
Task 9: complete (574016a..c2bbf46)
Plan 2 tasks all complete at c2bbf46; 0 parked findings. Next: whole-plan review over 690e3ac..c2bbf46 (the range includes merge f88e458 of origin/develop).
Final review — ready: with fixes; critical 0, important 5, minor 20
Final fix wave — 5 Important review findings: error sessions now release their ffmpeg + engine stream (PLAYER_MAX_SESSIONS overshoot), startup sweep tolerates an unreadable PLAYER_HLS_DIR and player start moved inside the lifespan try, fatal hls.js errors recovered or surfaced, Retry offered for every problem but ffmpeg_missing, CLAUDE.md engine-error contract corrected (commits 5829c1d..063d37c)
Final re-review — 5 addressed, 0 open
Plan 2 COMPLETE at 063d37c (9 tasks + whole-plan review + one fix wave + re-review; 0 critical, 0 open).
Ruling (re-review breakage 1): the narrow `_launch` vs `_tick_session` race (state re-checks at player_service.py:296,313 should read `in ("stopped","error")`) is real but unreachable on defaults; carried to the Plan 4 carry-forward wave. Breakage 2 was a test-count slip in the fix report, no code impact.
