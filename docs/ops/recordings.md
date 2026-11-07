# Built-in recording implementation and operations

Operator behavior: [Recordings](../../wiki/Recordings.md).

The schema revision `20261028_1200` adds `recordings`, `recording_attempts`, `recording_artifacts` and a stable unique `epg_sources.recording_uuid`. The SQLite server default also covers legacy raw-SQL EPG imports. Occurrence keys hash source UUID, XMLTV channel ID and original UTC start; repeated imports cannot retarget a saved schedule. Metadata snapshots have no FK to replaceable programme rows. Channel deletion nulls the TV reference while preserving history.

`RecordingService` serializes admission/operator mutations using the existing database write claim. Requests have idempotency keys and edits have expected revisions. `/api/v1/recordings` owns history, schedule, file and playback contracts; `/api/v1/config/recordings` owns settings. Paths/process identities never enter DTOs. OpenAPI and generated frontend types are committed together.

`RecordingCoordinator` runs a dedicated event loop in its own thread, with a 200 ms due-time scan, cached reservations/source preparation and an independent worker pool. It does not enter the maintenance FIFO. Database writes are journal-backed and asynchronous to dispatch. Storage checks, engine startup and media validation still impose real latency; this is not a hard real-time guarantee. Catalogue probes pause for imminent/active recordings; direct probe final-stop shares source ownership serialization. Dedicated checker probes never borrow the recording engine. Conversion yields when capture is within 60 seconds and restarts from the preserved original.

`recording_process` owns each FFmpeg process group, uses a control-pipe lifetime and Linux parent-death signal, and reaps before releasing the execution lock. No recovery code kills a PID inferred from a journal. Recovery validates storage identity and replays journals; original parts are never overwritten. File operations are descriptor-relative, no-follow and owned-regular-file only. Range delivery is bounded and closes reader leases on disconnect.

Browser VOD uses prepared fragmented MP4 rather than another engine-backed HLS pipeline. This deliberate implementation choice supports seeking without requiring an unbundled encoder; unsupported video remains downloadable. No full-video transcode is implied by AAC preparation. The wrapper writes derivatives through an inherited output descriptor: fragmented MP4 avoids unsafe/nonportable fast-start path reopening.

## Validation

Run the application gate, focused `test_recordings.py` and `test_recording_runtime.py`, frontend recording/timezone tests and command-builder contract. The runtime tests use fake owned children and the committed H.264/AC-3 media fixture, never live streams. The fixture conversion test skips only when FFmpeg is absent. Packaging qualification is separate: `backend/tests/docker/test_ffmpeg_build.py` covers amd64, arm64 and arm/v7; production qualification also needs bounded capture/failover, process-death and disk-pressure exercises on actual target hardware.

## Disable and rollback

1. Disable recordings in Automation; wait until active processes finish and retain partial media.
2. Back up the database and the entire persistent recording directory together. Preserve `.dvr-root` and journals.
3. Revert application code only after stopping the application. Do not point an older app at an unreviewed newer schema. Prefer restoring the matching pre-upgrade database backup when rolling back the deployment.
4. The Alembic downgrade removes DVR tables/source UUIDs but deliberately never deletes media. Export history first if using that destructive downgrade. Rolling forward again creates new source UUIDs; old occurrence identities are not reconstructed.

No infrastructure/release policy changes are required. Recording storage is an explicit deployment mount; neither startup nor the UI installs FFmpeg or creates missing mount roots.

## Local validation snapshot — 2026-10-28

Implementation working tree based on `ab890e4056f9f75536dede22e8005c82683e4ad2`, containing fetched develop `40f6d1e5bf56d6e325e0b33f7b7595e5ea19f702`:

- Full application backend: 2,239 passed (`pytest backend/tests --ignore=backend/tests/docker`). Runtime FFmpeg was compiled temporarily from the repository's pinned 8.1.2 source; a separately downloaded, pinned `imageio-ffmpeg==0.6.0` wheel supplied only the existing tests' libx264/lavfi fixture generator. Neither changed application dependencies.
- Frontend: 97 suites / 578 tests passed; TypeScript, ESLint with zero warnings and production build passed. The build still reports the same pre-existing 574.91 kB player and 676.30 kB data-grid vendor chunk advisories, reproduced from the base commit; no warning threshold was changed.
- Mocked browser journeys: 16 passed across phone Chromium, small-phone WebKit, tablet Firefox and desktop Chromium, in both themes. No live media or backend recording workload was used.
- Focused DVR lifecycle/security/timing checks and shared-source ownership checks passed after the final recovery changes. Due dispatch stayed below one second while a fake database writer was blocked.
- OpenAPI/generated TypeScript reproduced byte-for-byte; command-builder, Docker metadata, docs contract, strict legacy-path and Pages payload checks passed. The full gate's Git-diff check against committed types is not used as evidence for an uncommitted API change; regeneration stability was checked separately.

These are local results, not CI or release status. Docker multi-architecture DVR qualification and actual Linux/ARM hardware interruption/storage-pressure runs remain outstanding; recordings stay disabled by default. No deployment, publication or private infrastructure mutation was performed.
