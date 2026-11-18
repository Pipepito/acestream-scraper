# Per-source playback history

The tuner relay records how each attempt at a source ended and ranks a TV
channel's sources with that history. Status checks say whether a source was
broadcasting when it was checked; the history says what happened when a client
actually watched it. A box that is only switched on for a match has old check
results, and the history is often the only recent evidence.

## What is recorded

`tuner_playback_service.record_outcome()` is called once per attempt. Startup
installs `stream_history.StreamHistoryRecorder`, which queues the outcome and
writes one `stream_attempts` row on a background thread, so a slow or failing
SQLite write never delays or breaks playback.

A viewing is written while it plays: once a source has played 30 s it is
written as `ok` with those seconds and rewritten every 30 s, and its end
rewrites the outcome of the same row. A machine switched off mid-viewing keeps
what was watched. `/tuner/stream/<id>.ts` records viewings the same way.

| Outcome | Meaning | Counts as |
|---|---|---|
| `ok` | Played until the client left | 1 |
| `ended` | Played, then the source ended | 0.5 |
| `stall` | Played, then went silent mid-stream | 0.3 |
| `jumpy` | Played, but its clock went back twice or more (the viewer saw the same play again); also recorded by `/tuner/stream/` | 0.1 |
| `early_death` | Video, then silent within the first minute | 0 |
| `no_data`, `empty_session`, `engine_refused`, `upstream_error` | Never played | 0 |
| `engine_unavailable` | The engine was down: says nothing about the source | ignored |
| `handover` | Kodi's first GET, which handed the opening to its second GET: the viewing is recorded once, by the second | ignored |

Each row keeps the seconds played, the source's list (`source_url`) and how
many active sources its channel had at that moment, for later analysis. Peers
and download speed are stored when the relay provides them. Rows older than
180 days are pruned by the writer.

## How the relay ranks

`TunerService.relay_stream_ids()` keeps its order: saved preferences, then
recently online, online from an old check, then unknown or old offline;
recent offline results stay excluded. Within each group, sources rank by
`stream_history.score_sources()` before bitrate:

- each attempt's weight halves every 7 days, and an attempt that played counts as more
  evidence the longer it played (one more attempt's worth per 30 minutes, up to three);
- the prior is the share of the source's list that the last check found
  online (0.5 when unknown), with the strength of two attempts;
- a source is **demoted** (tried after every group, never dropped) when no list
  has published it for 14 days (`last_seen`), when its own recent history is
  clearly bad (decayed evidence ≥ 2 and score < 0.25), or when it has no
  history and at least 10 sources of its list are known with fewer than 20%
  online.

Saved preferences still come first, so an operator can always override the
ranking for a channel.

## Hiding sources with no use

The tuner setting `hide_unusable` (off by default; `PUT /api/v1/tuner/settings`)
leaves out of the lineup and the M3U playlists every *discarded* source and
every source whose own recent history is clearly bad (the same evidence and
score bounds as demotion). A channel left with none drops out. A playlist URL
can override the setting with `hide_unusable=true|false`.

A source is the asset; a list is only where it was found. Which lists still
publish a source does not count for hiding: a list that goes away or drops a
source changes nothing. The rule lives in `app/services/source_health.py`. A source is discarded when both hold:

- `failed_checks` is 5 or more: five status checks in a row found no media.
  Only real checks count (an HTTP check, or an engine check whose lookup
  answered found or not found); a timeout or an engine outage says nothing
  about the source.
- It has not worked for 7 days: `last_worked_at` (a check with media, or a
  relay attempt that ended `ok` or `handover`), or `failing_since` when it
  never worked. A time in the future discards nothing.

Both, because a server that is on now and then can make 7 days a single check,
and 5 checks can fall in one afternoon. A discarded source stays in the
database and is still checked, after every other source and at most once a
week; the first check with media or the first viewing brings it back.

Migration `20261113_1400` adds the three columns. It fills `last_worked_at`
from sources online at their last check and from `ok`/`handover` attempts;
failures count from the upgrade on.

## Limits

- The ranking is deliberately rule based. The rows are kept so that a learned
  model can replace `score_sources()` later without changing what is recorded.
- History is per content ID across channels: a source assigned to two channels
  shares its history.
- The writer queue holds up to 10 000 outcomes; when full, new outcomes are
  dropped with a warning instead of blocking the relay.
