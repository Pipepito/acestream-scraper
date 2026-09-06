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
immediately. All status callers share two probe slots and serialize the same source
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
