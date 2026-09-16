# Stream statistics

Acestream Channels shows the latest peer count and transfer speeds collected by
a stream status check. Use these observations to compare alternative sources for
the same channel. They are brief samples from your checking engine, so conditions
may differ when you start watching later.

## Collect and read a sample

1. Configure an engine in **Settings → Automation**. A dedicated checking engine
   keeps checks separate from the playback engine. Without an engine, checks are
   skipped and no new statistics are collected.
2. Open **Acestream Channels**, find a stream and choose **Check status** from its
   row actions. For regular collection, enable scheduled stream checks in
   **Settings → Automation**. Manual, bulk and scheduled checks use the same sampler.
3. Read **Stream statistics** in the table, or below the signal status on phone
   cards. Hover or keyboard-focus the statistics to see exact measurement times
   and the explanation. Search for a channel name to compare its sources.

| Value | Meaning |
|---|---|
| Peers | Connected peers reported by the engine in the latest valid sample. |
| Down / Up | P2P download/upload rate, in the engine's Kbytes/sec (shown as KB/s). |
| Media | Encoded media bitrate in Mbps, measured separately by the media probe. |
| Sample | Age of the engine sample, independent of the latest status-check time. |
| Unknown / Not sampled | The engine did not provide a valid value, or no sample has been collected. |

A value of **0** is a measured zero. Missing fields remain unknown; they are not
filled from an earlier poll. Media bitrate has its own measurement time in the
tooltip and may be older than the transfer-speed sample. It is not calculated from
P2P download speed. The engine's rate units are documented in the
[official playback API](https://docs.acestream.media/developers/start-playback/).

## Limits and interpretation

- A check records the latest valid sample from its existing bounded polling loop.
  It does not average a long-running transfer, test your internet connection, or
  continuously monitor playback. Startup buffering and cached data affect rates.
- Peers or a nonzero speed do not prove playable content. **Signal verified** still
  requires identified audio/video packets. Peers with no new data are allowed to
  wait through the normal check timeout; they do not immediately count as success.
- Only the latest sample is stored. There are no history charts, automatic playlist
  thresholds, or looping/stale-content detection in this version. Existing source
  ranking and playlist behavior are unchanged.
- Active playback can cause a check to be skipped. A missing or unavailable engine
  also skips checks. A configured dedicated checker never falls back to playback.
  Previous observations retain their original timestamps in these cases.
- If a completed check supplies no valid statistics, the previous sample remains
  visible with its original age. A sample is not evidence that the current check
  succeeded: read the separate signal status and **Last checked** value too.
- Scheduled checks cover active streams and share the existing sequential probe
  queue. Large catalogues take time to scan; statistics need not have the same age.

## API

Channel responses (including sources nested in TV channels) and individual status
check responses expose nullable `stream_stats`:

```json
{
  "observed_at": "2026-09-15T10:00:00Z",
  "peers": 12,
  "download_speed_kbytes_sec": 850.5,
  "upload_speed_kbytes_sec": 25.0
}
```

These are read-only observations. Existing installations start with `null`; the
normal database upgrade adds storage without replacing channel or source data.
