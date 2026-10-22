# Sports events

Development feature for v2.2.0; these notes do not establish stable availability.

Open **Watch → Events**. Upcoming shows today's and future events, plus events with
unknown start times. **Today** selects your current local date; **By date**, **All
events** and **Archived** offer other views. Search by title/participant and filter
by sport, competition, source or Following. The initial display timezone is your
browser's timezone; open **Filters & timezone** and enter another IANA timezone,
such as `Europe/Madrid`, to change
it for this page visit.

## Add and review

**Add events → Create an event** accepts a title, optional sport/competition, start
time, broadcaster and stream link. Leave an unknown start blank. A broadcaster
without a stream remains useful as an unresolved broadcast. Preview first, select
the event, then **Save selected**. Cancel writes nothing.

For multiple events/streams, choose **Import event schedule JSON**. This accepts
version 1 normalized event observations, not arbitrary website HTML, a raw W3U
catalogue or Telegram messages. Those adapters are separate work. A minimal file:

```json
{
  "version": 1,
  "observations": [{
    "source_id": "my-guide",
    "source_name": "My sports guide",
    "source_kind": "guide",
    "external_id": "fixture-123",
    "title": "North United vs South City",
    "sport": "Football",
    "competition": "Example Cup",
    "timezone": "Europe/Madrid",
    "starts_at": "2026-10-24T23:30:00+02:00",
    "state": "scheduled",
    "broadcasts": [{ "id": "broadcaster-1", "label": "To be confirmed" }]
  }]
}
```

An observation can include `participants`, a known `ends_at`, `time_notes`, and up
to 50 broadcasts. A broadcast may include `language`, `quality`, `country`, either
`url` or an existing `channel_id`, and supported `headers` (`User-Agent`, `Referer`,
`Origin`). Keep source/event and broadcast IDs stable across refreshes. Re-importing
updates those identities rather than making another event. Different source IDs
are not combined automatically. An explicitly reviewed `event_id` can associate a
new observation; the original source remains authoritative for the schedule.

The preview exposes no signed URLs/header values. Review every selected event and
source compatibility. Tokens expire after 15 minutes, four newer previews, or a
server restart. Changed events reject stale previews; preview again. Invalid files
write nothing. Missing events and broadcasts remain saved on partial refresh.

## Watch and follow

Open an event's title or **View broadcasts** to inspect language/quality, source,
compatibility and the last verified signal when available. **Play** uses the normal
browser player with shared audio/subtitle choices and cleanup. Choose another
broadcast explicitly if one fails; seamless automatic switching is not provided.
The existing player replaces only your viewer's session.

AceStream and direct HTTP HLS (`.m3u8`) / MPEG-TS (`.ts`) sources are compatible.
Compatibility does not guarantee delivery, codecs or current access. Website links
remain unsupported until an appropriate resolver exists; the application does not
send HTML to FFmpeg. Expired URLs need a revised import. Event-only HTTP sources
stay private and are not added to TV Channels, permanent stream inventory or
playlist exports. No TV number, guide assignment or TV favorite is inferred.

**Follow event** persists on this installation and is shared across its browsers.
It filters the schedule; it does not send notifications. **Correct schedule** saves
a complete manual schedule override which future source imports preserve. **Use
source schedule** removes the override and reveals the latest imported schedule.

## Times, status and retention

Local times use the source's declared timezone. For the repeated autumn DST hour,
include the explicit UTC offset in JSON; invalid spring-forward times are rejected.
Unknown times remain unknown. No end time is estimated. “Scheduled” stays scheduled
after its start passes; “Live · reported” is a publisher/operator claim,
not a signal check. Source announcements never set stream online status.

Postponed, cancelled and finished events remain available. A finished event's
stream may now show another programme. **Archive event** hides it from ordinary
views; **Archived → Restore event** brings it back. Retention is currently indefinite,
with no automatic deletion or separate refresh scheduler. Archiving never deletes
shared channels or stops viewers. Keep normal database backups; private media URLs
and headers are stored in that database.

Limits: 2 MiB per JSON upload, 500 observations per import, 2,000 stored events,
4,000 observations, 10,000 broadcasts and 16 MiB observation data. A reached limit
preserves the existing inventory. Automatic retention and integrated W3U/Telegram/
website collectors remain follow-up work before issue #55 is complete.
