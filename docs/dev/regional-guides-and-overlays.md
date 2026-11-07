# Regional guides and reviewed event overlays (#233)

Based on develop `d224476`, October 30, 2026. Issue #233 and all comments were
read using `gh issue view 233 --repo Pipepito/acestream-scraper --comments`.
The linked `scarcraft1:aporte/guias-html` branch was compared through commit
`43bb3014d588e2373a6775fb4fe5ce6958fede4c`. The regional converters are adapted
from that contribution; its football-to-XMLTV converter is deliberately replaced
by the existing event-provider ingestion and explicit overlays described here.
This is implementation scope, not a release or CI-status claim.

## Regional HTML sources

Adding a supported URL under EPG → Sources opts into conversion; there are no
seeded sources or background discovery. Exact supported hosts and paths:

- `https://proyectos.larioja.com/tvr/dimeprogramacion/dimeprogramacion.php?dia=0`
  fetches seven weekday pages, merges one XMLTV document, then invokes the normal
  incremental EPG reconciliation once. Weekdays 1–7 mean Monday–Sunday of the
  **current Madrid calendar week**, not next week's predicted programmes. `dia=0`
  means today. The page supplies no calendar date or end time: successive starts
  delimit programmes and midnight bounds the last programme. These are explicit
  adapter interpretations, not publisher-confirmed dates/ends.
- `https://sincroguia-tv.expansion.com/programacion/<channel>` reads only the
  channel's schedule HTML, never the unrelated JSON-LD highlight blocks. The
  configured URL owns the stable channel identity; an HTML canonical tag cannot
  change it. Yearless dates use the nearest year, at most 45 days away. A decreasing
  start clock crosses midnight; end clocks may cross midnight independently.

Both convert Europe/Madrid civil times to UTC and reject ambiguous/nonexistent
DST times. Invalid, missing, overlapping or duplicate times fail rather than
inventing programmes. TV Rioja weekly interpretation differs from the proposed
fork's "next occurrence of weekday" assumption. All seven pages must succeed
before ingestion. Existing data survives markup/HTTP/size/time failures.

Transport uses `outbound_http.source_session`, pinned DNS and existing SSRF
policy, no environment proxy, no redirect following, 2 MiB/page, 30s/page and
90s/source. HTML parsing runs off the event loop. No scripts or page assets run.
Public failure text does not contain upstream URLs or responses. Synthetic
`test_regional_guides.py` examples preserve the contributor's interpretation cases
for future #216 work, adding DST ambiguity, malformed rows and year boundaries.
General guide recipes and model interpretation remain #216's separate scope.

## Event sourcing before download

WOSTI Football exposes a curated set of competition paths in `/events/providers`.
`football_competitions` replaces the broad football fetch with those exact paths;
other selected sport feeds remain included. Empty competition selection requests
`/deporte/futbol`. All sports must be deselected to narrow football; the API rejects
contradictory combinations and unknown path keys. No arbitrary upstream URL is
constructed from user text. The setup explains this before the first preview.

`timeout_seconds` is saved in the source adapter (default 15, range 5–300). Preview
and automatic refresh share it; edits retain the existing source revision guard.
The browser allows an additional 30 seconds for server processing. The existing
120-second refresh-pass budget controls admission **between sources**; an admitted
source receives its full configured timeout, so a pass can take up to just under
420 seconds of fetch time. Remaining sources defer and oldest attempts run first.
The byte limits, three-request concurrency, review requirements and preservation
of events outside the selection remain unchanged. Interests still use their
existing OR semantics within fetched rows; they do not broaden competition URLs.

## Reviewed XMLTV overlays

Events → event details → Manage event → XMLTV guide overlay offers a preview,
explicit apply and removal. Select a broadcast linked to a TV/EPG channel with an
enabled, source-qualified guide. Confirm an explicit-offset end after the known
start, within twelve hours. This is an operator-owned overlay window, not a new
assertion about the event's real end. Generic/ambiguous broadcasters need a manual
channel mapping first; no global DAZN or HDR alias is introduced.

Preview exposes affected programmes without writes. Apply obtains the event's
revision write claim, recomputes the target/schedule/affected-programme fingerprint
and rejects stale previews or overlapping accepted overlays. Migration
`20261030_1300` adds nullable `sporting_events.guide_overlays` after the source-name
migration `20261030_1200`; upgrade/downgrade tests preserve existing events and
named sources. A source URL digest,
guide identity and broadcast target are retained privately to detect replacement.

`programs_in_window` projects overlays for both ordinary XMLTV and tuner exports:
regular programmes are split at the window edges and preserved outside it. No
EPGProgram, channel assignment, playlist identity, API token or recording row is
written. The original guide view and built-in recording selector therefore retain
their original programme IDs and listings. This distinction is stated in the UI.
Clients consuming exported XMLTV see the event in that window.

Changed title, schedule, sport/competition, broadcast target or guide identity
suspends the snapshot until reviewed again. Archive, postponement, cancellation,
missing/disabled guides also suppress it. Unchanged source refreshes preserve it.
Removal restores the regular export immediately; source and event retention
cannot leave independent orphan overlays. Persisted conflicts fail closed during
projection, never resolve by row order. Overlay end times are never guessed from
sport, and broadcaster labels never imply verified signal.
