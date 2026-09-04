# SDD ledger — plan: docs/superpowers/plans/2026-09-03-media-integrations-1-foundation.md

Spec: docs/superpowers/specs/2026-09-03-media-integrations-design.md (read; binding authority).
Branch: feature/media-integrations (off develop), checkout /Users/pipepito/Code/acestream-scraper-alt. Base commit before Task 1: 9f5ad4b.

## Preflight conflict scan (2026-09-03)

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T1 ↔ T2 | T1 test `test_entrypoint_defaults_match_settings_defaults` asserts entrypoint exports that T2 adds | Conflict: T1 commit would carry a failing test |
| T4 → T5, T11 | `request.state.peer`/`forwarded` (T4) consumed via getattr defaults (T5, T11) | Consistent |
| T9 → T10 → T11 | `EngineClient(engine_url, client=)`, `engine_url_from_settings`, `relay_engine_stream(engine, content_id, client_label, *, client_factory, registry)`, `_relay_client_factory` monkeypatch target | Consistent |
| T10 → T11 | `ClosingStreamingResponse` acloses `body()`; `body()` finally acloses the relay iterator → engine stop | Consistent |
| T12 ↔ existing tests | `PlaylistService._score_acestream` kept as alias | Consistent |
| T3 ↔ existing startup tests | fresh-db message text changes; plan tells implementer to grep/update assertions | Consistent (verify in review) |
| T5 / T11 tests | mutate `main.app.user_middleware` kwargs + `middleware_stack=None` to re-trust `testclient` | Fragile but self-contained; acceptable |
| T2 | exact `APP_COMMAND=(...)` literal asserted; plan gives it verbatim | Consistent |
| T6 | `getAbsolutePlaylistUrl(filters, publicBaseUrl?)` only caller is Playlist.tsx | Consistent |

Ruling: T1 adds only the two `Settings` tests; `test_entrypoint_defaults_match_settings_defaults` is added by T2 (same file, same content) — keeps every commit green. Costs nothing if wrong beyond a moved test.
Ruling: `docs/superpowers/` is gitignored; plan/spec stay local files, never force-added.

Task 1: implementer DONE (commits 9f5ad4b..6dac75d) — 566/566 backend tests passing (7/7 in test_settings_env.py, 2 new), output pristine.
Task 1: review APPROVED — spec ok; critical 0, important 0, minor 0
Task 2: implementer DONE (commits 6dac75d..fcbb0ba) — 40/40 runtime-guard + settings-env tests pass; wider backend suite 572 passed; docker smoke test compile+collect only.
Task 2: review NEEDS FIXES — spec gaps; critical 0, important 3, minor 8
Task 2: fix round 1 implementer — entrypoint.sh now exports all eight media knobs (added PLAYER_START_TIMEOUT_SECONDS, FFMPEG_BINARY_PATH, MEDIA_SERVER_MIN_REFRESH_MINUTES); the entrypoint/Settings drift guard derives its knob set from the Settings media block + model_fields defaults (mutation-checked both ways); --bind-all on the native amd64 engine verified by running the real x86_64 3.2.11 engine and the full entrypoint under emulation — parsed (allow_remote=1 vs 0 control), non-RFC1918 client admitted, no crash loop, app healthy (commits fcbb0ba..54b958e)
Task 2: re-review round 1 — 3 addressed, 0 open
Task 3: implementer DONE (commits 54b958e..59ca4e8) — 574/574 backend tests pass (non-docker); the 2 new startup tests went RED->GREEN, 18/18 in test_startup_db_init.py + test_migrate_database.py.
Task 3: review APPROVED — spec ok; critical 0, important 0, minor 7
Task 4: implementer DONE (commits 59ca4e8..d8a0256) — 13 new middleware tests green; brief set 27/27; full backend suite 587 passed, warnings pre-existing.
Task 4: review NEEDS FIXES — spec ok; critical 0, important 2, minor 7
Task 4: fix round 1 implementer — joined repeated X-Forwarded-* header lines in _header (RFC 9110 5.3) so a proxy-appended X-Forwarded-For beats a client-forged one, and added three tests: the repeated-header attack, main.app.user_middleware[0] is ForwardedHeadersMiddleware with trusted parsed from Settings, and an end-to-end request through main.app's registered stack (commits d8a0256..f293faf)
Task 4: re-review round 1 — 2 addressed, 0 open
Task 5: implementer DONE (commits f293faf..227d2c1) — 15/15 new public-URL tests green; brief subset 40/40; full backend suite 605 passed (docker excluded).
Task 5: review NEEDS FIXES — spec ok; critical 0, important 3, minor 7
Task 5: fix round 1 implementer — guarded urlsplit (422 not 500) via a shared pure normalize_public_base_url in public_url_service, normalized/dropped the PUBLIC_BASE_URL env seed, and made the forwarded test restore the real trusted lists in a finally block (commits 227d2c1..2b30bc7)
Task 5: re-review round 1 — 3 addressed, 0 open
Task 6: implementer DONE (commits 2b30bc7..7d73f98) — frontend 47 suites / 275 tests passed, lint+typecheck clean; backend 611 passed unchanged.
Task 6: review APPROVED — spec ok; critical 0, important 0, minor 8
Task 7: implementer DONE_WITH_CONCERNS (commits 7d73f98..d714b2f) — 33/33 test_url_guard.py passing (17 new validate_lan_target tests), full backend suite 628 passed.
Ruling (Task 7 concern): the `and not address.is_loopback` guard on the is_reserved branch is accepted — Python 3.12 marks ::1 as reserved, and the spec allow-list admits loopback; no plan change needed. Cost if wrong: one extra allowed address class (loopback), already intended.
Task 7: review APPROVED — spec ok; critical 0, important 0, minor 1
Task 8: implementer DONE (commits d714b2f..0584090) — 3/3 new tests passing (RED->GREEN per brief); full backend suite 631 passed, 0 failed
Task 8: review APPROVED — spec ok; critical 0, important 0, minor 2
Task 9: implementer DONE (commits 0584090..504497c) — 8/8 new test_engine_client.py tests passing (RED->GREEN per brief); full backend suite 639 passed, 0 failed.
Task 9: review NEEDS FIXES — spec ok; critical 0, important 1, minor 7

Task 9: fix round 1 implementer — EngineClient now owns/closes its fallback httpx.Client (_owns_client flag, close(), __enter__/__exit__) with 3 added lifecycle tests; injected clients left untouched (commits 2ed7107..2ed7107)

Task 9: re-review round 1 — 1 addressed, 0 open
Task 10: implementer DONE_WITH_CONCERNS (commits 2ed7107..3ead4c8) — 11/11 in backend/tests/test_stream_relay.py, 0 flakes in 25 runs; wider suite 653 passed exit 0.
Task 10: review NEEDS FIXES — spec ok; critical 0, important 2, minor 7
Ruling (Task 10 concerns): reap_finished() wiring belongs to Task 11 (lifespan reaper, per plan) — verify at Task 11 review; host-only redirect check matches spec 4.2 text and stays; bytes_sent is a UI counter only. No plan change.
Task 10: fix round 1 implementer — httpx transport failures opening the engine stream now become EngineStreamError (so the route can answer 502, not 500), and the engine-host guard normalises loopback spellings/ports so the real playback_url (127.0.0.1:36879 vs ACE_ENGINE_URL localhost:6878) is accepted while off-engine redirects stay refused; 5 new tests (commits 3ead4c8..934833a)
Task 10: re-review round 1 — 2 addressed, 0 open
Task 11: implementer DONE (commits 934833a..6fc9787) — 30/30 new+token tests pass; wider backend suite 677 passed (docker excluded).
Task 11: review NEEDS FIXES — spec ok; critical 0, important 1, minor 7
Task 11: fix round 1 implementer — dropped `Depends(get_db)` from the unbounded `/tuner/stream/<id>.ts` handler so a relay no longer pins a pooled connection for its whole life; `_engine()` now opens and closes its own short-lived session inside `run_in_threadpool`, with two regression tests (commits 6fc9787..faa8c27)
Task 11: re-review round 1 — 1 addressed, 0 open
Task 12: implementer DONE (commits faa8c27..613ae57) — 83/83 focused tests pass (stream_ranking + tv_channels + curated_playlists + playlists); wider backend suite 682 passed (docker excluded).
Task 12: review APPROVED — spec ok; critical 0, important 0, minor 1
Task 13: implementer DONE_WITH_CONCERNS (commits 613ae57..06ad6f3) — backend 682 passed (docker excluded), frontend 47 suites/275 tests, lint+typecheck+build clean, run_v2_test_suite quick + validate_command_builder PASS.
Task 13: review APPROVED — spec ok; critical 0, important 0, minor 5
Ruling (Task 13 concerns): (1) wiki rows for PLAYER_*/MEDIA_SERVER_* knobs stay — all four plans ship in one PR from feature/media-integrations, and wiki publishes only from develop builds, so no reader sees knobs without features; (2) command-builder entries for PUBLIC_BASE_URL/TUNER_ALLOWED_NETWORKS/PLAYER_MAX_SESSIONS are Plan 2 Task 8; (3) /tuner/ proxy carve-outs are Plan 4 Task 7. No plan change.
Task 1: complete (9f5ad4b..6dac75d)
Task 2: complete (6dac75d..54b958e, fix round 1)
Task 3: complete (54b958e..59ca4e8)
Task 4: complete (59ca4e8..f293faf, fix round 1)
Task 5: complete (f293faf..2b30bc7, fix round 1)
Task 6: complete (2b30bc7..7d73f98)
Task 7: complete (7d73f98..d714b2f)
Task 8: complete (d714b2f..0584090)
Task 9: complete (0584090..2ed7107, fix round 1)
Task 10: complete (2ed7107..934833a, fix round 1)
Task 11: complete (934833a..faa8c27, fix round 1)
Task 12: complete (faa8c27..613ae57)
Task 13: complete (613ae57..06ad6f3)
Plan 1 tasks all complete at 06ad6f3; next: final whole-branch review (range 9f5ad4b..06ad6f3).
Final review — ready: with fixes; critical 0, important 3, minor 13
Final fix wave — backup_sqlite reuses the per-label pre-upgrade copy (restart loop no longer fills the volume, new double-boot test); command builder + 23 docs examples publish 0.0.0.0:8000:8000 with the IPv6/docker-proxy caveat and a new guard test; release notes + wiki document the startup schema upgrade, its backups and the restore-the-backup rollback (commits 4a9dbf4..690e3ac)
Final re-review — 3 addressed, 0 open
Plan 1 COMPLETE at 690e3ac (13 tasks + final review + one fix wave + re-review; 0 critical, 0 open findings).
Ruling (13 final-review minors): carried forward, not dropped. The five cheap correctness ones (CLAUDE.md dev command missing --no-proxy-headers; relay reaper without a per-iteration except; tuner.py 422 using {'detail'} instead of the APIError envelope; engine_client startswith('http') and command_url param merge; backend/Dockerfile CMD missing the uvicorn flags) are appended to Plan 2 Task 9 as a carry-forward wave. The rest (docker-gateway /12 heuristic, forwarded.py bare-token parsing, wiki wording, Playlist token display, docker smoke hygiene) are recorded here and revisited at the whole-branch review before the PR. Cost if wrong: a second cleanup pass on the same files.
