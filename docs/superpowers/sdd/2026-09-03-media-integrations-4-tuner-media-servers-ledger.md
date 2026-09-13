# SDD ledger — plan: docs/superpowers/plans/2026-09-03-media-integrations-4-tuner-media-servers.md

Spec: docs/superpowers/specs/2026-09-03-media-integrations-design.md (binding authority, sections 4.4, 4.7, 7, 8, 10, 11).
Branch: feature/media-integrations. Plans 1-3 complete (Plan 3 head d08cca1); origin/develop merged at f88e458 (arm64 engine is now an `oci-image` from jopsis/acestream 3.2.17 — spec 4.7 rewritten accordingly, no engine task in this plan).

## Preflight conflict scan (2026-09-04)

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T1 → T2, T3 | `TunerService.settings/update_settings/device_id/build_lineup/lineup_fingerprint/guide_fingerprint`, `Lineup`/`LineupEntry`/`Renumbered` | Consistent |
| T1 ↔ Plan 1 | consumes `sort_streams_curated` and `ChannelRepository.get_playlist_tv_channels()` | Repository method name must be verified in code — the plan asserts an ordering the test depends on |
| T2 ↔ existing EPG output | refactor of `generate_epg_xml` must keep `/api/v1/epg/xml` byte-identical | Guarded by the new test plus `tests/parity`; the plan mandates running both |
| T2 → T3 | `build_guide_xml(lineup)`, `build_playlist_m3u(lineup, public)` | Consistent |
| T2 ↔ PlaylistService | reuses the M3U attribute escaper (`PlaylistService._attr` may not exist under that name) | Ruled below |
| T3 ↔ Plan 1 T11 | inserts routes above the catch-all `/tuner/{path:path}`; needs `relay_registry` active-count API | `count_active()` may not exist — the implementer adds it if missing |
| T3 → T5, T6 | `/api/v1/tuner/settings|status`, `TunerStatusResponse` | Consistent |
| T4 ↔ Plan 3 T1 | consumes the `MediaServer` model's 17 columns | Verified present in Plan 3's revision |
| T4 → T5 | `MediaServerService.test/connect/refresh/status/disconnect/sync_if_changed`, `RefreshResult` | Consistent |
| T5 ↔ Plan 3 T4 | reuses `RemotePlayerService.tuner_access(host)` and the endpoint/error-translation shape | Consistent |
| T6 ↔ Plan 3 T6 | both edit `pages/Integrations.tsx`; Plan 3 created it, T6 appends the Media servers section | Sequential; T6 extends, never rewrites |
| T7 ↔ Plan 2 T9 / Plan 3 T7 | all three touch `backend/tests/contracts/test_integrations_contracts.py` and regenerate OpenAPI/types | T7 extends the existing file |
| T7 ↔ develop | `docs/ops/acestream-arm-engine.md` was rewritten on develop for the 3.2.17 `oci-image` engine | T7's brief was regenerated after the merge and documents per-platform playback expectations, not an engine bump |

Ruling: T2 must find the existing M3U attribute-escaping helper in `app/services/playlist_service.py` and reuse it; if none exists under a reusable name, add one shared helper rather than duplicating the escaping in `TunerService`. Cost if wrong: one refactor.
Ruling: if `ChannelRepository` has no `get_playlist_tv_channels()`, T1 uses the repository method the playlist actually calls and adapts the test's expected ordering to that method's real ordering, recording which it used. Cost if wrong: a test that asserts the wrong order.
Ruling: the carry-forward wave from the Plan 2 and Plan 3 reviews (player `_launch` state re-check, scan classify deadline, best-effort DELETE `.catch`) rides on Task 1.

Task 1: implementer DONE_WITH_CONCERNS (commits eaeb8b4..72e3994) — 7/7 new tuner tests + 1 new player-launch test green; backend 841 passed, frontend 315 passed, tsc clean; brief's two sample HDHomeRun device ids were not checksum-valid and were corrected.
Task 1: review APPROVED — spec ok; critical 0, important 0, minor 9
Task 2: implementer DONE (commits 72e3994..278c7ff) — 3 new tuner-export tests + EPG byte-identity guard green; full backend suite 845 passed (docker excluded).
Task 2: review APPROVED — spec ok; critical 0, important 0, minor 6
Task 3: implementer DONE (commits 278c7ff..59cbf11) — 852 backend tests pass (--ignore=backend/tests/docker); 6 new tuner-route tests + 1 token-boundary test, output pristine.
Task 3: review NEEDS FIXES — spec ok; critical 0, important 1, minor 8
Task 3: fix round 1 implementer — tuner_count cap made atomic (RelayRegistry.try_open under a lock, claim taken before the engine start and adopted/released by relay_engine_stream, slot returned on every non-streaming path), 5 tests added incl. a two-thread route race test (commits 2255ec0..2255ec0)
Task 3: re-review round 1 — 1 addressed, 0 open
Task 4: implementer DONE (commits 2255ec0..255d13c) — 10/10 new media-server tests green; full backend suite 867 passed (--ignore=backend/tests/docker), output pristine.
Task 4: review NEEDS FIXES — spec ok; critical 0, important 2, minor 10
Task 4: fix round 1 implementer — sync_if_changed keeps the stored fingerprints when a refresh errors (so the next pass retries), and every Jellyfin/Plex JSON decode goes through base.decode_json(), which maps a non-JSON 200 onto MediaServerError; +2 tests (commits 255d13c..306adc1)
Task 4: re-review round 1 — 2 addressed, 0 open
Task 5: implementer DONE (commits 306adc1..dcc751a) — 6/6 new media-server API tests green; full backend suite 875 passed (--ignore=backend/tests/docker), frontend format.test.ts + Overview.test.tsx 9/9 and tsc clean.
Task 5: review NEEDS FIXES — spec ok; critical 0, important 1, minor 9
Task 5: fix round 1 implementer — moved the refresh bookkeeping into MediaServerService.record_result()/current_fingerprints(), used by both the manual refresh endpoint and sync_if_changed, so a manual refresh advances the fingerprints and the sync job no longer refreshes a second time; added test_manual_refresh_leaves_nothing_for_the_sync_job (commits dcc751a..0451efe)

Task 5: re-review round 1 — 1 addressed, 0 open
Task 6: implementer DONE (commits 0451efe..207262c) — new mediaServerService.test.ts + extended Integrations.test.tsx 12/12 green (mutation-checked), full frontend suite 322/322, lint --max-warnings=0 and tsc clean, backend 876 passed (--ignore=backend/tests/docker).
Task 6: review NEEDS FIXES — spec ok; critical 0, important 2, minor 6
Task 6: fix round 1 implementer — connect toast now reports the returned server's connected state (Plex without a token/DVR gets a warning, not a success) and the tuner settings block keeps its two numbers as text with 1-16 / 1-1000 validation, an error-marked field and Save disabled instead of posting 0 (commits 207262c..94dcad3)

Task 6: re-review round 1 — 2 addressed, 0 open

Task 7: implementer DONE_WITH_CONCERNS (commits 94dcad3..bef8be0) — backend 897 passed (--ignore=backend/tests/docker) + 4 new docs-contract and 25 new integration-contract tests; frontend 325/325, lint/tsc/build clean; quick CI suite PASS; e2e journey 3 passed / 2 skipped (no ffmpeg on this host, so the two playback tests never ran).
Task 7: review NEEDS FIXES — spec ok; critical 0, important 2, minor 7
Task 7: fix round 1 implementer — wired the ARM docs contract guard into run_v2_test_suite.sh (both profiles, ahead of the profile split; it is the blocking cutover-quick check, and the guard was proven to bite by mutating wiki/Docker.md and watching the suite abort), and gave the real-engine playback e2e test the hls.js console allowance it was missing, as one shared named pattern so the two playback tests cannot drift apart (commits ca14f02..ca14f02)

Task 7: re-review round 1 — 2 addressed, 0 open
Task 1: complete (eaeb8b4..72e3994)
Task 2: complete (72e3994..278c7ff)
Task 3: complete (278c7ff..2255ec0, fix round 1)
Task 4: complete (2255ec0..306adc1, fix round 1)
Task 5: complete (306adc1..0451efe, fix round 1)
Task 6: complete (0451efe..94dcad3, fix round 1)
Task 7: complete (94dcad3..ca14f02, fix round 1)
Plan 4 tasks all complete at ca14f02; 0 parked findings.
Ruling (T1): the brief's two "known valid" HDHomeRun device ids were wrong (the worked checksum comes to 0xE, not 0); the implementer kept libhdhomerun's algorithm verbatim and corrected the test data to 10E1F2F8 / 12345674. Correct call — the algorithm is the authority, not the example.
Ruling (T2): PlaylistService._attr lifted into app/utils/m3u.py (m3u_attr) with _attr kept as a thin alias, mirroring the _score_acestream -> stream_ranking pattern. Matches the preflight ruling.
Ruling (T3): the relay cap reads tuner_count through a short-lived session helper rather than Depends(get_db), preserving Plan 1's decision that a request-scoped session must not be pinned for a relay's lifetime.
Ruling (T5): MEDIA_SERVER_NOT_CONNECTED (409) lives on POST /{id}/disconnect for an already-disconnected server; Jellyfin refresh after disconnect stays 200 as the brief's own test pins.
Ruling (T7): the two deterministic playback e2e tests skip on this host because it has no ffmpeg; the stub engine and the tuner relay were verified end to end instead (2.8 MB at ~470 KB/s). The assertions inside those two tests remain unexecuted here and must run on a machine with ffmpeg (or in the container) before the feature is called verified. Recorded as the one outstanding verification gap.
Final branch fix wave — the nine confirmed review findings (six distinct defects): a saved Jellyfin key / Plex token is now confined to the address the row already names (and a moved row forgets it, with its registration ids); the Plex paste values resolve the public origin per request instead of rendering "<public address>"; the Integrations sections report a failed load instead of showing an empty list or claiming ffmpeg is ready; automatic GuideNumbers no longer move when an unrelated channel leaves the lineup; a pre-upgrade backup is written atomically and only a real SQLite file counts as reusable; and startup creates the tables an older image's create_all never had before stamping head. 906 backend tests, 327 frontend tests, lint and typecheck all green (commits 9c7935f..a8ef289)
Final branch re-review — 9 addressed, 0 open
Polish (Backend) — 5 fixed, 0 declined (commits c7a6c29..0be1666)
Polish (Frontend) — 6 fixed, 0 declined (commits f57f7c4..cbb814a)
Polish (Contracts) — 4 fixed, 0 declined (commits 3583a17..1052226)

Final verification — 11 gates pass, 0 fail; branch clean
Controller fix (fcad6d7): the Docker ffmpeg build test's literal PLAYER_COMMAND had no guard tying it to PlayerService.ffmpeg_argv — the final verification named the drift risk and it was raised as a minor twice before. Guard added in backend/tests/test_player_service.py (outside the Docker-gated module so it always runs).
Branch state 2026-09-04: 94 commits ahead of origin/develop; all 11 verification gates pass; merge-readiness written to final-verification.md. NOT pushed, no PR — awaiting the user.
