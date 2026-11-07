# Import exclusions and saved searches

Scraper has deep-linked `sources`, `searches` and `exclusions` tabs. Old `/scraper`
links still open Sources. Search remains the interactive discovery screen.

## Import policy

Exclusions prevent future permanent-channel imports. They never delete channels,
filter playlists, deny playback, or establish signal. Name contains and Name equals
use Unicode NFKC, case folding and collapsed whitespace. Accents, punctuation and
country markers remain significant. Contains is a literal substring, including
`%`, `_`, brackets and regex-looking text. Stream ID equals accepts a canonical
40-hex content ID or the existing `url:` plus SHA-1 identity. An infohash must be
resolved before testing an exact content-ID rule. Enabled rules combine with OR;
matching IDs are returned in stable rule order.

Rules are unique by kind and normalized value, including disabled rules. Limits:
500 rules, 256 characters per value, 500 per optional note. Empty normalized values
and control characters are rejected. Rule edits and deletes require the current
row revision. Every mutation increments the singleton policy revision in the same
transaction. A no-op SQL write to the policy singleton serializes rule changes
with final admission and channel writes; process locks are not the consistency
boundary. No network operation or FIFO wait occurs inside that boundary.

The inventory preview scans at most 10,000 rows or two seconds in keyset batches,
returns at most 50 examples and labels incomplete counts “at least”. Explicit
sample previews accept at most 200 candidates, each with a bounded ID/name; no
URLs are fetched. Preview and policy CRUD do not mutate channels. Outcome links
use `#rule-<id>` and an exact `rule_id` list filter, so they also find rules beyond
the first page and show a clear message for deleted rules.

| Import path | Admission and preservation |
| --- | --- |
| HTTP, M3U, ZeroNet, IPFS and recipes | Capture raw IDs before admission. Skip excluded candidates before TV assignment/upsert. Protect incoming excluded IDs and stored matching source rows from ordinary source pruning. Empty, failed, partial and all-excluded results do not prune; recipes remain additive. TV creation/assignment flushes inside the caller's transaction. |
| Search, including legacy add routes | Server resolves selected catalogue infohashes, applies current policy, then creates only missing channels. Existing names, source ownership, guide assignments, hidden state and observations remain unchanged. |
| Saved searches | Same resolution/admission. Update only separate membership discovery times for existing rows. No TV auto-assignment or deletion for missing results. |
| W3U | Keep all preview entries visible. Bind reviewed save to policy and catalogue revisions. Store explicit reviewed identities separately from successful imports; excluded entries are not marked imported. Background refresh re-evaluates current policy while preserving prior review scope. |
| Telegram | Service-owned transaction commits admission, observed IDs, revision, cursor and counters together. All-excluded valid messages advance. Rule removal does not replay retained messages. |
| Manual Add | A matching rule returns `IMPORT_EXCLUDED` with rule IDs. Only explicit `allow_excluded=true` bypasses it. The UI offers a separate Add anyway confirmation. Existing metadata edit routes are unaffected. |

EPG/event-only observations, VOD and the public recipe helper do not import
permanent channels. Import rules do not alter those workflows. Automatic guide
assignment following ingestion also avoids blocked stored channels and the
excluded incoming IDs, even if their saved operator names differ.

## Saved definitions and import results

Saving a search stores configuration only. Automatic refresh is off by default.
Run now authorizes a one-shot additive import even while automatic refresh is
paused. Query/category edits increment the definition revision and pause automatic
refresh. Enable it again deliberately. Names and queries are bounded at 100 and
256 characters; categories at 100. There are at most 100 definitions. The unique
fingerprint uses NFKC and whitespace normalization, preserving case and punctuation.
Renaming does not change identity. Deleting a definition removes its memberships,
never its channels or another search's memberships.

Search uses only the configured playback/catalogue engine. It never chooses the
dedicated checker, Acexy or an implicit localhost engine. `get_content_id` resolves
infohashes without starting playback. Failed resolution never saves a raw infohash.
New channels have unknown signal; catalogue status is not a media probe. Creation
provenance is `saved-search:<id>`, an opaque label, not an outbound URL. This label
may outlive the definition; the channel remains independently manageable.

`POST /search/import` accepts at most 100 selected infohash/name/category items and
returns typed per-item added/existing/excluded/unresolved/duplicate/deferred results.
Legacy `/search/add` and `/search/add_multiple` delegate to this contract: their
`id` now explicitly requires an infohash, and responses use the typed import result.
They no longer generate UUIDs, trust browser-resolved IDs, replace metadata, or
implicitly associate TV channels. Use the normal TV assignment controls afterward.
Play still uses `/search/{infohash}/resolve`; Check broadcast remains independent.

Saved results contain a schema version, outcome, stop reason, timestamps, duration,
definition/policy revisions and bounded samples. `added`/`existing` count unique
canonical IDs; excluded/unresolved/deferred count candidate decisions. Duplicate
infohashes and duplicate canonical resolutions are distinct observations, so these
counts must not be forced into a single arithmetic inventory total. Samples stop
at 100 with `samples_truncated`. No raw upstream bodies/errors or media URLs are
stored. Fully complete runs alone update `last_success_at`.

Complete empty and all-excluded searches are successful, non-destructive runs.
Useful partial pages may add discoveries but stay partial. Unresolved candidates
are partial, never offline. Unconfigured engine is skipped; an unavailable engine
with no useful candidates is failed. Caps, repeated pages, malformed pages and
deadlines have explicit stop reasons. Shutdown is interrupted. Changed/deleted/
paused automatic definitions cannot apply stale results.

## Bounds and preview ownership

| Bound | Value |
| --- | --- |
| Page size / pages | 100 groups / 10 pages |
| Unique candidates | 1,000 per run; flattening has its own cap |
| Response size | 4 MiB per page, enforced while receiving before JSON parsing |
| Candidate/preview storage | 8 MiB |
| Network request | 10 seconds maximum, capped by remaining run budget |
| Whole run | 120 seconds, including engine slot admission and resolution |
| Shared engine admission | Two calls, shared by previews, interactive imports and saved runs |
| Resolution | Once per unique infohash per run; no persistent negative cache |
| Preview cache | Eight entries, 8 MiB aggregate, five-minute TTL |
| Scheduled saved-search substep | Five minutes |

Requests use a cancellable asynchronous HTTP client inside the worker, with no
environment proxies or redirects. Whole-request deadlines cancel socket IO and
close the client before releasing its shared slot. Partial responses never turn
malformed JSON into a successful empty catalogue.

Preview tokens refer to private process-local snapshots. A run with a token owns
a copy when admitted; expiry or cache eviction before admission is HTTP 410.
Definition/policy mismatches are HTTP 409, including at final execution. Browser
payloads cannot supply resolved candidates. Run now without a token explicitly
performs a fresh search. Preview never enters the maintenance FIFO and writes no
source/channel data.

## Queue and recovery

There is one recurring `url_scraping` job. Saved searches inherit its interval,
clock anchor, timezone and startup catch-up semantics. The scheduled wrapper
snapshots eligible definitions and reserves target keys before entering the shared
maintenance FIFO. Manual targeted runs reserve the same key and enqueue their own
ticket; duplicates return the current run. Scheduled work owns its enclosing ticket
and does not acquire it again. Manual runs do not refresh unrelated sources.

Lock order is target admission, then queue condition. Immutable snapshots and DB
work happen outside the queue condition. Waiting state is persisted before manual
admission returns 202. Workers own sessions, closing them before network/queue
waits. Final apply rechecks definition, automatic enablement, run identity and
policy under the DB write claim. Imports, memberships and results commit together;
unexpected failures roll back, then store a sanitized failure separately.

Target reservations release on success, failure, shutdown and batch deferral.
Completion-persistence failures are logged without stranding the FIFO or other
targets. Shutdown gives targeted workers a shared twelve-second join budget.
Never-attempted/oldest-attempted definitions run first with stable ID ties. Budget
deferrals do not advance attempt times, preventing starvation. Restart marks
orphaned waiting/running rows interrupted; accepted Run now requests are not a
crash-durable queue. Retry explicitly or wait for normal cadence/catch-up. The
existing single-app-worker lock is unchanged.

Scheduled scraping sends one aggregate notification; each manual targeted run
sends one summary. Existing top-level scrape counters and scalar job results remain
valid. New nested `saved_searches` and `import_exclusions` summaries distinguish
excluded, unresolved, skipped, partial and interrupted work. Deferred candidates
and whole searches deferred by the substep budget have separate units.

## Migrations and verification

`20261027_1200` adds policy storage and Telegram exclusion counts after
`20261026_1200`; `20261027_1300` adds saved searches/memberships. Both are additive.
No automatic subscriptions or channel changes are backfilled. SQLite foreign keys
specify cascade deletion; application deletion paths also clean memberships because
older installations do not enable foreign-key enforcement. Downgrading removes
only the feature's configuration/history/memberships, retaining channel inventory.
Production rollback should disable automatic refresh first, not auto-downgrade.

Focused regressions are `test_import_exclusions.py`, `test_saved_searches.py`,
`test_saved_search_queue.py`, migration and existing ingress/scheduler tests.
Frontend coverage includes Search's actual canonical import path, submitted-query
save, exclusion previews and queued runs. `e2e/mobile/import-management.spec.ts`
provides mocked, deterministic light/dark phone/tablet/desktop workflows. No live
swarm is needed for import semantics. Run the full application gate and strict
legacy-path guard; regenerate OpenAPI and TypeScript contracts deterministically.
