# Stream checks and PID isolation

## Verified behavior — 2026-09-06

Tested the locally built native Linux **AceStream 3.2.11** image under amd64
emulation on an ARM64 Docker host, in a disposable container with its own engine
state. ARM engine 3.2.17 was not runtime-tested in this investigation.

The existing checker already sent a random 32-character `pid` on every probe and
reused it for the timeout retry. The [official API reference](https://docs.acestream.net/developers/api-reference/)
lists this parameter; it does not promise that stopping one PID isolates another
viewer of the same source.

Live observations with two sessions for the same infohash:

- Starting twice without PID reused the command URL.
- Distinct PIDs returned distinct command URLs and initial playback-session IDs.
- Once both were running, both statistics URLs reported the same current
  playback-session ID.
- Sending `method=stop` to the probe command URL ended the original media reader.
  Bytes stayed at 8,911,200, and the original statistics URL reported
  `unknown playback session id`.
- With the new application guard, the actual `ChannelStatusService` returned
  `skipped` for a source registered as in use. The original reader remained open
  and bytes increased from 6,290,240 to 7,338,624 across the check.

**Conclusion:** keep unique PIDs, but do not rely on them for stop isolation.
The test confirms the active-source guard preserves playback; it does not establish
an engine CPU/memory saving attributable to PID.

## Reproduce against an isolated engine

1. Start a disposable engine with its own state and a loopback-only published API
   port. Use a currently broadcasting test source; catalogue availability alone
   does not prove it is live.
2. Call `/ace/getstream?infohash=<hash>&format=json&pid=<random-A>` and keep
   consuming the returned `playback_url`, following only engine-host redirects.
   Confirm the reader remains open and bytes increase over several seconds.
3. Start the same infohash with a different PID. Compare command URLs, initial
   session IDs, and both `stat_url` responses.
4. Stop only the second command URL with `method=stop`; observe the first reader
   and its statistics for several seconds. Distinct URLs alone are insufficient.
5. Repeat with the first source registered in `relay_registry`. Invoke
   `ChannelStatusService.check_channel_status(..., persist=False)` and verify it
   skips the engine call while the first reader continues receiving bytes.
6. Close readers, stop test sessions, and remove the disposable container.

Do not run the unguarded stop experiment against an engine serving real viewers.

## Application behavior

The scheduler defaults to 60 minutes and persists `channel_status_interval` in the
existing settings table (no schema migration). Settings saves reschedule the job
immediately. All status callers share one probe slot and serialize every source
ID across threads/event loops.

Stable TV-channel GETs enqueue background checks without waiting for completion
when online candidates already exist. Unknown/offline alternatives are checked
first, recently checked sources are skipped for 30 seconds, and newly verified
sources can join the same 45-second startup budget. The queue coalesces one task
per channel, bounds pending channels to 32, and runs one channel refresh at a time.
Shutdown drains the current bounded probe and skips queued work.

A relay reservation or starting/ready web-player session protects its source from
checks. Cleanup checks ownership again if playback began during a probe, avoiding
an explicit stop and leaving expiry to the engine. Skipped checks retain the stored
status and do not overwrite it with a guessed online/offline result.

This is protection for playback known to this app, by source ID. It cannot identify
players connected directly to an external engine, different identifiers for the
same underlying source, or provide atomic coordination with external engine calls.

### Engine recovery before probes

Every channel status probe checks the configured direct engine's status API before
starting a stream. It waits up to approximately 60 seconds for recovery, polling
every two seconds with a three-second request timeout. If the engine stays down,
the check is skipped and the stored channel status, error, and last-check timestamp
remain unchanged. A failed broadcast probe rechecks engine health before recording
offline, so a crash during the probe also preserves the previous status. Waiting
does not start an intentionally stopped engine. Existing playback ownership guards,
probe limits, unique PIDs, and session cleanup still apply.

### Priority and scan freshness

The process-wide queue is shared by HTTP handlers and scheduler/tuner worker
threads. It always selects waiting TV-playback checks first, then individual
manual/search checks, then scheduled and bulk scans. Requests within each class
keep arrival order. New interactive requests overtake already queued background
work. A running check finishes its bounded probe and session cleanup before any
other probe starts; it is not interrupted mid-session.

The two-second cooldown starts after cleanup and applies to every caller. Engine
unavailability extends that pause to ten seconds. A skipped fresh/in-use result
adds no cooldown. Bulk API concurrency remains accepted for compatibility but
cannot enable parallel engine probes.

Scheduled and bulk scans reread committed status just before probing, avoiding
stale ORM inventory. They skip anything checked within 30 seconds or since their
scan began, whichever window is longer. Playback refreshes reuse 30-second results;
individual manual checks can force a new check, but reuse a result that completed
while their request was queued. These skips preserve the check timestamp and use
the latest saved status. Sustained interactive demand can delay background scans.

Stable tuner GETs and browser playback of a stream assigned to a TV channel queue
playback-priority refreshes of that channel's candidates. Browser playback itself
starts immediately; owned active sources remain protected from status probes.

## ID lookup and signal verification

Channel checks report `network_status` independently of `is_online`:

- `found`: the engine recognized the ID and returned a verifiable session.
- `not_found`: the engine explicitly reported that the content ID was not found.
- `unknown` (or null before checking): lookup was inconclusive. A timeout, no peers,
  generic HTTP 404, or engine outage does not establish permanent network absence.

`is_online=true` now requires both increasing P2P downloads and a bounded HTTP
media sample containing packets from an identified audio/video stream. Peer counts,
prebuffering, stream declarations, or download speed alone are insufficient. A
failed media probe yields no verified signal, including when ffprobe is unavailable.
This is a snapshot at `last_checked`, not a continuous playback guarantee or a
browser codec-compatibility test. The configured engine remains the probe route;
existing active-playback guards and queue priorities still apply.

Catalogue imports leave new IDs unchecked and preserve an existing probe outcome.
The signal-status migration clears old online/check outcomes because earlier checks
and imports could mark an ID online without receiving media. Channel records and
historical audio/bitrate metadata remain. Run channel checks to populate fresh status.

## Dedicated checking engine (opt-in)

On `scraper-acestream` and `scraper-acestream-acexy`, set
`ENABLE_ACESTREAM_ENGINE=true` and `ENABLE_ACESTREAM_CHECK_ENGINE=true` to run
one persistent checking engine alongside playback. The default remains off.
Every status caller (manual, search verification, tuner refresh and scheduled
scan) uses `ACE_CHECK_ENGINE_URL`; the entrypoint supplies
`http://127.0.0.1:6880` for the bundled checker. Other flavors can set an external
`ACE_CHECK_ENGINE_URL` instead. Do not combine an external URL with the bundled
checker switch. The saved Engine URL, Acexy upstream and playback routing retain
their existing roles. Restart the container after changing these environment options.

The checker has separate state, identity, locks, cache and scratch storage under
`/var/lib/acestream-check` on every architecture. Its HTTP, legacy API and P2P
ports are 6880, 62063 and 8622 respectively (HTTPS reserves 6881); playback defaults
remain 6878, 62062 and 8621. No checking ports are published by the command builder. Reserve these
ports when customizing the playback command. The checker always uses the packaged
foreground launcher, independently of `ACESTREAM_START_COMMAND`. Never mount the
same host directory for playback and checking state. An optional separate mount
at `/var/lib/acestream-check` keeps its writes outside the writable image layer.

The checker uses a 256 MiB disk-cache limit and 64 MiB live-cache size; these are
engine cache settings, not a cap on total process RSS. Checks still share one
probe slot and cooldown. Both processes consume host CPU, RAM and bandwidth;
isolation prevents checker session stops/crashes from controlling playback, but
does not remove resource contention or prove that either engine can play a stream
continuously. Existing active-source guards remain conservative even on the
separate route, avoiding duplicate traffic for app-owned playback.

Overview → Services exposes **AceStream checking engine** with independent
Start/Stop/Restart controls. All exits are retried indefinitely, except after UI
Stop. Start/Restart or container restart resumes recovery. An unavailable checker
causes checks to be skipped and stored status/timestamps to be preserved. It never
falls back to the playback engine. Checker health appears in Services and probes;
it deliberately does not fail container health, which could cause an external
watchdog to restart healthy playback. Diagnostics include bounded
`acestream-check.log` tails and separate supervisor state.

## Shared direct-playback cleanup

Direct `EngineClient` sessions now hold a process-wide ownership lease keyed by
engine endpoint and source ID. Start and final Stop use the same per-source lock
in worker threads, so a viewer starting while another closes cannot slip between
the ownership check and the stop request. Closing a viewer releases its lease;
only the last owner sends the engine Stop command. Repeated cleanup is idempotent,
and each handle retains its original ownership through configuration changes.
Browser session sharing and unique PIDs for newly created sessions remain intact.
Acexy continues to own its sessions and receives no direct Stop commands.

This covers app-owned direct browser and relay sessions, including distinct audio
selections. It cannot track clients launched directly into an external player,
resolve arbitrary DNS aliases or map different IDs to the same underlying source.
Use server relays/Acexy for shared external viewing rather than assuming PID alone
isolates readers. Cleanup of a released reader while others remain is left to the
engine until the final owner's Stop; this is intentional.

### Verification — 2026-09-07 working-tree implementation

Implemented against base commit `3abe5ae`. Disposable containers used the existing
bundled native amd64 **3.2.11** and
ARM64 **3.2.17** binaries with the updated entrypoint/checker launcher mounted
read-only. Both engines answered independently. Killing the checker triggered
recovery; stopping it left the primary engine PID and API unchanged. Fresh ARM64
homes produce independent device IDs. The native engine reserves HTTPS 6879 by
default: using that as the second HTTP port makes it reset its port configuration.
The checker therefore uses HTTP 6880 and explicitly reserves HTTPS 6881.

A native live source (`is_live=1`) continued delivering bytes after the checker
stopped the same infohash: 17,760,256 → 21,954,560 bytes over eight seconds.
Using the updated `EngineClient` ownership implementation for two direct sessions
with distinct PIDs, closing the second viewer left the first receiving media:
14,614,528 → 18,808,832 bytes over eight seconds. This is a bounded reproduction,
not a sustained-load guarantee. ARM64 refused the media attempt with
`mod_detected`; its lifecycle isolation is verified, media isolation remains
unverified. ARMv7 still needs real hardware.

`backend/tests/docker/test_acestream_runtime_smoke.py` now exercises the dual-engine
lifecycle through `docker/testdata/check_engine_lifecycle.py` in each freshly built
runnable image. The full Docker build matrix was not rerun locally for this change.
Focused ownership, probe-routing, player, tuner, service-control and UI regression
checks accompany the implementation. The quick gate's committed-type comparison
requires the newly regenerated API snapshot to be committed; regeneration was
checked separately for byte-for-byte reproducibility, and the remaining quick
frontend tests, lint, typecheck and build were run directly.

### Optional engines and Settings

Settings → Automation → Stream status checks stores an optional dedicated engine
through `GET/PUT /api/v1/config/check-engine` (`use_dedicated`, `url`). With the
switch off, checks use the saved playback engine URL. Clearing the playback URL
and leaving the dedicated checker off disables status probes; scheduled runs
return a no-engine result and Run status check now does not queue a job. Previous
channel results remain unchanged. Scraping and catalogue management need no engine.

A dedicated endpoint that fails never falls back to playback. `ACE_CHECK_ENGINE_URL`
seeds the external choice until Settings saves an explicit choice; disabling it in
Settings overrides that environment default. The bundled checker remains managed
by `ENABLE_ACESTREAM_CHECK_ENGINE` and its supervisor; its route is read-only in
Settings. Overview offers configuration links for unmanaged engines and shows an
unconfigured engine as disabled, not unhealthy.

New scraper-only installs default to no playback endpoint. Bundled enabled engines
retain their internal endpoint. Existing saved URLs are preserved; clear an old
localhost URL in Playback if the installation no longer has an engine.
