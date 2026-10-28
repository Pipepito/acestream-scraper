# Recordings

Record now captures a TV Channel independently of browser playback. Choose **Record now** in Live TV or the channel player, or **Schedule recording** beside a future programme in its guide. Raw catalogue streams must first belong to a TV Channel. When multiple TV Channels share a guide, select the intended channel.

## Setup

Recordings are off by default. Create a persistent directory owned by the application user, mount it into the container, and set `RECORDINGS_DIR` to its absolute container path (for example `/recordings`). Native installations also need FFmpeg and its sibling ffprobe executable; `FFMPEG_BINARY_PATH` selects the binary. The recording folder must be separate from the temporary player HLS folder. Symlinked directories and files are rejected.

Enable recordings in **Settings → Automation**. Defaults are one simultaneous capture, 2 GiB free-space reserve, 100 GiB per recording, and no automatic deletion. Up to four simultaneous captures are supported. Recording admission estimates space at 20 Mbit/s plus 20% headroom; this is an estimate, not an observed bitrate. Actual size depends on the source. A recording cannot exceed 12 hours; up to 1,000 pending requests within 90 days are allowed. Overlapping reservations beyond the configured capacity are rejected, including two seconds for cleanup between reservations.

The first enable creates an owned `.dvr-root` marker. The application saves its identity in the database and refuses a missing or different mount instead of silently writing into the container. Restore the original directory and marker if storage becomes unavailable. Back up the database and recording folder together. Do not edit or remove marker/journal/lock files while the application runs.

## Times and controls

Review the start, end and IANA timezone before saving. Repeated daylight-saving hours require an explicit UTC choice; nonexistent local times are rejected. Requests are stored as UTC instants with the selected zone for editing. The history displays dates in the browser's local timezone and separately identifies the scheduled zone.

Record now uses the current programme's end where an unambiguous assigned guide is available, otherwise one hour. Change the end before saving or while recording. A scheduled start can be edited until capture starts. Guide refreshes and rematching never silently move saved times or replace saved titles/descriptions. Source-qualified guide identity and programme metadata survive removal of EPG rows.

**Cancel recording** removes a pending reservation. **Stop recording** closes the active capture and keeps usable media. Closing playback or leaving the page does not stop recording. Disabling the feature cancels pending requests and stops active captures. Re-enabling does not resume cancelled work.

## History, playback and files

**Watch → Recordings** lists schedules, completed and partial recordings, failures and deleted history. It shows missing intervals, actual media start/end and separate files after failover. Files are never blindly concatenated across source changes. Protect a recording to exclude it from deletion and retention.

Originals are stream-copy MPEG-TS. **Download** preserves the captured codecs and audio tracks. **Prepare MP4** remuxes the first video/audio tracks; **Prepare browser audio** converts the first audio track to AAC while preserving video. Derivatives use fragmented MP4, remain separate from originals and become available only after successful validation. Preparation pauses/restarts when capture is imminent or active.

**Play** creates a bounded viewing subscription and prepares browser audio when necessary. The browser can seek in the prepared local file. It may not support the source video codec; download the original for another player. There is no automatic video re-encoding, live rewind, series recording, or playback of a growing file. Closing one viewer does not stop another viewer or cancel shared preparation.

File downloads and playback use the same optional `API_TOKEN` policy as other APIs. When a token is configured, GET, HEAD and range requests require it; native media links carry it in their query. Reverse proxies should redact query strings from access logs. With no API token, installations retain the existing trusted-network open-access behavior. There is no per-user recording library.

## Failures and retention

Capture starts on a dedicated timer, independently of the maintenance FIFO. Timer dispatch does not guarantee first media at that exact instant: network, engine startup and buffering still take time. Add an earlier start for important programmes. Direct engine leases prevent recording cleanup from stopping a viewer; Acexy retains ownership of its own sessions. Imported HTTP broadcasts use the existing guarded media proxy, including nested playlists and redirects.

The coordinator tries eligible TV-channel sources in playback order, with bounded startup/failover budgets. Source stalls, quota exhaustion, low space and shutdown close owned child process groups. Identified A/V packets and timestamp progress are required before a part is usable. Keep partial recordings when any part is usable. Downtime and source changes are shown as gaps.

On restart, journals reconcile pending database state and closed files. An interrupted recording with time remaining may resume as a new part; explicit stops do not resume. A first start more than two minutes late is missed. An execution lock prevents a second process from writing the same recording. An unavailable mount or unverifiable process ownership fails closed.

Optional retention removes unprotected terminal recordings older than the configured number of days. It does not delete active captures or a conversion in progress. Up to 16 file readers are admitted at once. Active downloads hold file leases, so deletion waits for readers. Low space stops capture rather than deleting protected or recent recordings unexpectedly. History remains after media deletion.

## Architecture qualification

All bundled flavours share the pinned minimal FFmpeg build for amd64, arm64 and arm/v7. Capture needs MPEG-TS muxing, packet parsing and pipe/HTTP protocols; MP4 preparation needs the MP4 muxer, and browser audio needs the AAC encoder. No libx264, Matroska muxer or concat demuxer is required. Capability checks inspect the selected runtime binary before enabling capture or conversion.

Native fixture validation does not establish Linux multi-architecture runtime qualification. Run the Docker FFmpeg tests and bounded source-failure/restart/storage-pressure scenarios on each supported architecture before enabling production DVR. ARMv7 engine support remains experimental; keep its concurrency at one until measured on real hardware.
