# SDD ledger — plan: docs/superpowers/plans/2026-09-03-media-integrations-3-remote-players.md

Spec: docs/superpowers/specs/2026-09-03-media-integrations-design.md (binding authority, sections 6, 8, 10).
Branch: feature/media-integrations, checkout /Users/pipepito/Code/acestream-scraper-alt. Plans 1-2 complete; origin/develop merged at f88e458 (arm64 engine now `oci-image`).

## Preflight conflict scan (2026-09-03)

| Pair / task | Produces vs consumes | Finding |
|---|---|---|
| T1 → T3, T4 | `RemotePlayer` / `MediaServer` models + revision `20260903_1200_add_media_integrations` (down `20260824_1200`) | Verify the real Alembic head before writing down_revision — develop added no migration, but the implementer must confirm |
| T1 → Plan 4 T4 | `MediaServer` columns consumed by `MediaServerService`/`MediaServerRepository` in Plan 4 | Consistent if T1 ships every column Plan 4 lists (kind, name, base_url, api_key, tuner_mode, enabled, auto_refresh, tuner_host_id, listing_provider_id, dvr_key, last_sync_at, last_sync_status, last_error, last_lineup_fingerprint, last_guide_fingerprint, server_version, timestamps) — checked, all present in T1 |
| T2 → T3 | `make_driver`, `PlayerProbe`, `PlayerStatus`, `PlayerUnreachable`, `PlayerAuthError(kind)`, `PlayerCommandError`, `guard` | Consistent |
| T3 → T4 | `RemotePlayerService.validate_host/tuner_access/probe/status/resolve_stream_url/play/command`, `scan_network`, `validate_scan_request`, `default_scan_cidr` | Consistent |
| T3 ↔ Plan 1 | consumes `validate_lan_target(host, *, resolve)`, `resolve_public_base_url`, `TunerNetworkGate`/`get_tuner_gate`, `/tuner/stream/{id}.ts` | All landed in Plan 1; `tuner_access` is also consumed by Plan 4 T5 |
| T4 → T5 | `/api/v1/remote-players` CRUD + `/test`, `/{id}/test|status|play|command`, `/scan`, `/scan/default`; `_client_factory` monkeypatch target | Consistent |
| T5 → T6 | `remotePlayerService`, `useRemotePlayers` hooks | Consistent |
| T6 ↔ Plan 2 | reuses `StreamPlayerDialog`, `usePlayer`, `usePlayerSessions`, `describePlayerError`; adds `PlayOnMenu`/`ChannelPickerDialog` and `ChannelActionHandlers.onPlayOn` | Plan 2 shipped those; T6 extends the row actions it created — same files, sequential, no conflict |
| T6 ↔ Plan 4 T6 | both edit `pages/Integrations.tsx`; T6 creates it with three sections, Plan 4 appends a fourth | Sequential; Plan 4's brief says extend, not rewrite |
| T7 ↔ Plan 2 T9 | both touch `backend/tests/contracts/test_integrations_contracts.py` and regenerate OpenAPI/types | Plan 2 created the file; T7 extends it |

Ruling: T1's `down_revision` is whatever `PYTHONPATH=backend alembic -c backend/migrations/alembic.ini heads` reports at implementation time, not the literal in the plan, if the two differ — the plan's value was written before the develop merge. Cost if wrong: a broken migration chain caught by test_schema_parity.
Ruling: the Integrations page is created by Plan 3 Task 6 and only extended by Plan 4 Task 6; if Plan 4's section list disagrees with what Task 6 built, Plan 4 adapts.
Task 1: implementer DONE (commits 063d37c..5a6b10e) — 751 backend tests passing (full suite minus docker), new test_media_integration_tables_match_models red then green.
Task 1: review APPROVED — spec ok; critical 0, important 0, minor 5
Task 2: implementer DONE (commits 5a6b10e..6d1b9e9) — 17/17 driver tests pass; wider backend suite 768 passed (docker tests excluded).
Task 2: review APPROVED — spec ok; critical 0, important 0, minor 8
Task 3: implementer DONE_WITH_CONCERNS (commits 6d1b9e9..a69069d) — 23/23 new tests pass; wider backend suite 791 passed in 103s, no new warnings.
Task 3: review NEEDS FIXES — spec ok; critical 0, important 2, minor 8
Task 3: fix round 1 implementer — scan budget now enforced (deadline checked inside the semaphore, and classify() honours it), validate_host brackets/normalises IPv6 literals and rejects host:port so driver URLs parse instead of escaping as httpx.InvalidURL; 4 regression tests added (commits 9d3446b..9d3446b)

Task 3: re-review round 1 — 1 addressed, 1 open
Task 3: fix round 2 implementer — capped every scan wait at the time left in the budget (connect gets min(timeout, left); both classify() requests get an httpx timeout capped by the remaining budget, floored at 0.0 so a lapsed deadline cannot raise ValueError past the HTTPError handlers); two regression tests (commits 9d3446b..e0bf4de)

Task 3: re-review round 2 — 1 addressed, 0 open
Task 4: implementer DONE (commits e0bf4de..bf894c2) — 6/6 new API tests pass; full backend suite 803 passed, 0 failed (docker tests excluded).
Task 4: review NEEDS FIXES — spec ok; critical 0, important 2, minor 7
Task 4: fix round 1 implementer — probe now answers reachable:false for non-player HTTP services instead of 500ing, and a stored password is reused only when the saved row already names the probed host and port; 2 new API tests + 2 service cases (commits 1191793..1191793)
Task 4: re-review round 1 — 2 addressed, 0 open
Task 5: implementer DONE (commits 1191793..9affd5d) — 1/1 new service test pass, lint/typecheck clean; wider backend suite 805 passed in 102s.
Task 5: review APPROVED — spec ok; critical 0, important 0, minor 2
Task 6: implementer DONE_WITH_CONCERNS (commits 9affd5d..e4a4ddd) — frontend 310/310 jest pass (9 new/updated suites, 51 tests), lint --max-warnings=0 + typecheck + vite build + e2e typecheck clean; backend 805 passed.
Task 6: review NEEDS FIXES — spec ok; critical 0, important 2, minor 13
Task 6: fix round 1 implementer — volume slider keeps a local drag draft (cleared by the first status read after the command lands); PlayOnMenu gained an optional notify prop so the Acestream Channels row action reports "Sent X to Y." in the page snackbar that outlives the closing dialog; 2 regression tests added (verified red first). Frontend 312/312 jest pass, lint --max-warnings=0 + typecheck clean (commits e4a4ddd..60cb027)
Task 6: re-review round 1 — 2 addressed, 0 open
Task 7: implementer DONE (commits 60cb027..d08cca1) — 19 new contract tests (verified red under two contract perturbations); backend 824 passed, frontend 312 passed + lint/typecheck/build clean, run_v2_test_suite.sh --profile quick and publish_wiki.sh --dry-run both exit 0.
Task 7: review APPROVED — spec ok; critical 0, important 0, minor 5
Task 1: complete (063d37c..5a6b10e)
Task 2: complete (5a6b10e..6d1b9e9)
Task 3: complete (6d1b9e9..e0bf4de, fix rounds 1-2)
Task 4: complete (e0bf4de..1191793, fix round 1)
Task 5: complete (1191793..9affd5d)
Task 6: complete (9affd5d..60cb027, fix round 1)
Task 7: complete (60cb027..d08cca1)
Plan 3 tasks all complete at d08cca1; 0 parked findings.
Ruling (Task 4 deviation, accepted): the model_validator turning `command=volume` without `value` into a 422 instead of a 500 is correct and stays — a client mistake must not be a server error.
Ruling (Task 3 concern, scan budget): the 30 s budget bounding only the TCP connect phase is carried to the Plan 4 carry-forward wave as a deadline check in classify(); a dense /22 scan can otherwise run well past its advertised budget. Cost if wrong: a slow scan, not a wrong one.
Ruling (Task 6 concern, snackbar flash): accepted as specified — the row-level "Play on…" dialog closing on success unmounts its own snackbar. Plan 4 Task 6 owns page-level feedback and can lift the message there if it is still felt.
Ruling (Task 1 concern, free-form kind/tuner_mode/last_sync_status): no CHECK constraints; the Pydantic Literals at the API boundary are the enforcement point, matching the rest of this codebase. Cost if wrong: a bad value can only enter through raw SQL.
Final review — ready: with fixes; critical 0, important 4, minor 13
Final fix wave — IPv6 scan brackets + LAN guard in classify(), a moved player forgets its password, and POST /{id}/play returns the warnings that say a sent link cannot reach the player (commits 5c9fb0f..eaeb8b4)

Final re-review — 4 addressed, 0 open
Plan 3 COMPLETE at eaeb8b4 (7 tasks + whole-plan review + one fix wave + re-review; 0 critical, 4 important all fixed, 0 open).
Ruling (spec amendment owed): the fix wave added `warnings` to RemotePlayerPlayResponse; spec 6.1/6.3 said that warning appears only on the probe. Spec amended by the controller (POST /{id}/play returns {url, warnings}).
Ruling (behaviour change, accepted): changing a saved player's host OR port clears its stored password, because `_same_target` is defined on (host, port). Documented in the dialog helper text and wiki/Remote-Players.md. Cost if wrong: a user retypes a password after moving a player.
