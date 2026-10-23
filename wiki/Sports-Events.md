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
catalogue or Telegram messages. Their collectors use this shared contract. A minimal file:

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

## Schedule URLs and structured guides

Choose **Add events → Load schedule URL**. Select either the version 1 JSON format
above or **Structured sports guide (JSON or HTML JSON-LD)**. For structured guides,
check the source timezone: it is used for local timestamps without an offset.
Preview, explicitly select events and save. Fetching a preview writes nothing.

The structured adapter accepts [schema.org SportsEvent](https://schema.org/SportsEvent)
records in JSON or `application/ld+json` HTML scripts, including `@graph`. Each event
needs a stable `@id` or `identifier` and a name. It reads explicit start/end dates,
sport, competition (`superEvent`), home/away teams and competitors. It preserves
postponement/cancellation status. Date-only values, “today” and ambiguous local
DST times are rejected; no URL dates or duration are guessed. It does not execute
JavaScript, load remote contexts, interpret arbitrary page text or scrape all
sports websites. The original ZeroNet wrapper is not a runtime dependency.

Related `BroadcastEvent` records contribute broadcaster names as unresolved
options. Event `VideoObject` records under `subjectOf` or `video` can provide
`contentUrl` (direct media) or `embedUrl` (usually an unsupported player website),
language and quality. Ticket links and event/homepage URLs are never media.
`isLiveBroadcast` does not prove that the event is currently live or online.

Enable **Refresh selected events automatically with scheduled scraping** during
review, or toggle the source under **Sources & retention**. Refresh uses the
existing scraping interval, startup catch-up and FIFO queue. **Run scraping & event refresh** queues a pass now (including the regular channel
scrapes); repeated requests do not duplicate running/waiting work. It updates only previously reviewed events; **Review schedule**
lets you accept newly discovered events. Failed, empty, invalid or partial feeds
preserve saved events and variants. The last success, errors and new-event count
are visible per source. Signed schedule URLs are not exposed in the source list.

At most 20 schedule URLs are saved. Each fetch is limited to 2 MiB and 15 seconds;
a pass has a 120-second fetch budget and prioritizes sources with older attempts.
Remaining sources are deferred. Turning refresh off during a fetch prevents its
results from applying. A source identity belongs to one URL; use distinct publisher
identities for different feeds. A structured guide derives its namespace from its
saved URL, while publisher event IDs remain stable through postponements.

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

Use **Map [broadcaster] to a stream** to search active streams and select the exact
country/edition. The selection is explicit, saved for that event's broadcast and
preserved by refresh. **Use source broadcast** removes the override. Missing or
disabled mapped streams remain unavailable; a generic “DAZN” never selects one
automatically. No permanent channel is created or changed by mapping.

If a source supplies `artwork_url` (or structured `image`), **Load event artwork**
fetches it on request through the server. Only small PNG/JPEG/static WebP images
are supported (512 KiB, at most 4 million pixels and 4096 pixels per dimension).
The original URL stays private; artwork failures do not affect playback.

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
views; **Archived → Restore event** brings it back. **Sources & retention** configures
separate ended/archive retention. Both default to **0 (keep indefinitely)**; positive
values are days. Deletion runs with existing daily cleanup, never earlier at startup.
Ended retention requires a reported finished/cancelled state and a known end; an
old scheduled start alone does not qualify. Archived retention starts at the archive
date, independently of scheduled dates. Followed events are protected.

Cleanup removes only event records and their private media lookups; permanent
streams/TV channels and active viewers stay intact. Deleted events lose their
refresh approval and cannot return automatically; they may appear for explicit
review again. Archive/restore remains reversible until configured cleanup deletes
an eligible event. Keep normal database backups; private URLs and headers are
stored there.

Limits: 2 MiB per JSON upload, 500 observations per import, 2,000 stored events,
4,000 observations, 10,000 broadcasts and 16 MiB observation data. A reached limit
preserves the existing inventory. Reviewed W3U imports share this event model;
automatic W3U schedule extraction and Telegram transport remain in #257/#258. Arbitrary website
resolvers, automatic playback fallback and guide overlays are not offered here.


## From a Wiseplay catalogue

In **Catalogues**, save a list, open a compatible source and choose **Add as event**.
Review its schedule and timezone, preview, then select the event to save. The
shared event model retains private broadcast inputs without creating permanent
channels. Catalogue refresh does not automatically change event schedules; review
the saved source again to update it. See [W3U catalogues](W3U-Catalogues.md#add-a-catalogue-broadcast-to-events).
