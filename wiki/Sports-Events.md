# Sports events

Development feature for v2.2.0; these notes do not establish stable availability.

Open **Watch → Events** for a day-by-day agenda with start times and broadcaster
names. Select **When** to see the next **14 days** (including today), **Today**,
**Choose a date**, **All saved events** or **Archived**. Events without a date appear
at the end of the upcoming schedule and in All saved events; unknown times show
“Time TBC”. Open an event title for its details and where to watch.

Search by title/participant, or open **Filter events** to select sports,
competitions, teams or Following. Sports, competitions and teams combine with
**OR**: Premier League, one team and Motorsport includes anything matching any
selection. The filter button shows the active count even when collapsed.
**More filters & timezone** contains source and text filters, the 7/14/30-day
window and display timezone. Text filters further narrow the view. Times initially
use your browser timezone; enter an IANA timezone such as `Europe/Madrid` to change
it for this page visit.

## Built-in providers

**Add events** opens **Built-in provider**. No JSON file or API key is needed:

- **Fútbol en la TV · Spain** reads the [multi-sport guide](https://www.futbolenlatv.es/deporte)
  and selected sport feeds, including [motorsport](https://www.futbolenlatv.es/deporte/automovilismo).
  Spain is the **broadcast market**, not a restriction on teams or competition countries.
  The all-sports page currently publishes a short-range schedule; individual sport
  pages can cover more days. The default includes all sports and the motorsport page.
- **OpenFootball** reads the selected league/season from
  [football.json](https://github.com/openfootball/football.json). Choose a published
  season and confirm the source timezone. Community fixture coverage varies, and
  this source does **not** include TV broadcasters. A date without kickoff time
  stays date-only; the app does not invent a midnight start.

Choose an import window (7, **14** or 30 days) and **Preview events**. In the preview,
select any sports, competitions and teams you want, then **Update preview with
interests**. Selections combine with OR; empty selections include everything in the
chosen feeds. Choose events individually or **Select all shown events**, then save.
The available-interest list comes from the published window; an exact name can also
be typed and accepted with Enter. At most 500 matching events appear per preview;
narrow the interests if the provider publishes more.

Each provider has one saved configuration (one per league/season for OpenFootball).
The source remembers its feeds, interests and window. **Sources & retention →
Review schedule** reopens them. An empty preview can still save the source for later
review. Scheduled refresh updates selected, previously reviewed events; new events
still need review. A shorter window or changed interest never deletes saved events
or manual links. Display interests on the Events page are independent of import
interests and apply for the current page visit.

Fútbol en la TV does not publish stable fixture IDs in these pages. The integration
therefore identifies exact published occurrences, including their date and time.
An edited kickoff appears as a **new occurrence requiring review**, not an automatic
reschedule. Check it and archive the older occurrence when appropriate. Doubleheaders,
practice sessions and races are not merged just because their titles match.
OpenFootball uses season, league, round and teams, so a kickoff edit retains identity.
Neither source creates playable streams or promises complete 14-day coverage.

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

An observation can include `participants`, `scheduled_date` (when the date is known but time is not), a known `ends_at`, `time_notes`, and up
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

For other providers, use the advanced JSON/URL modes. A free website or JSON API
must supply the version 1 format above or supported SportsEvent metadata below;
arbitrary provider APIs and iCalendar (`.ics`) feeds still need an adapter.
Invalid JSON and schema errors show the affected field paths before anything saves.

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

At most 20 sources are saved. A URL fetch is limited to 2 MiB and 15 seconds;
built-in providers use at most three simultaneous requests, 2 MiB per response,
12 MiB total and one shared 15-second deadline;
a pass has a 120-second fetch budget and prioritizes sources with older attempts.
Remaining sources are deferred. Turning refresh off during a fetch prevents its
results from applying. A source identity belongs to one URL; use distinct publisher
identities for different feeds. A structured guide derives its namespace from its
saved URL, while publisher event IDs remain stable through postponements.

## Watch and follow

Open an event's title for its time and **Where to watch**. **Manage event** reveals
schedule corrections, archive controls, channel links, language/quality, source
and the last verified signal when available. **Schedule notes** expands any timing
information supplied by the source. **Play** uses the normal
browser player with shared audio/subtitle choices and cleanup. Choose another
broadcast explicitly if one fails; seamless automatic switching is not provided.
The existing player replaces only your viewer's session.

AceStream and direct HTTP HLS (`.m3u8`) / MPEG-TS (`.ts`) sources are compatible.
Compatibility does not guarantee delivery, codecs or current access. Website links
remain unsupported until an appropriate resolver exists; the application does not
send HTML to FFmpeg. Expired URLs need a revised import. Event-only HTTP sources
stay private and are not added to TV Channels, permanent stream inventory or
playlist exports. No TV number, guide assignment or TV favorite is inferred.

Broadcaster names link to an existing **TV channel first**, otherwise an unambiguous
**EPG channel**. Matching requires the same normalized name and compatible explicit
country/edition; generic names such as DAZN and ambiguous matches remain plain text.
A link opens the existing channel detail page and does not assert playable signal.

For an unmatched broadcaster, use **Link [broadcaster]**; for an existing link,
open **Manage event** first. Choose a TV or EPG channel manually, including a
differently named channel in your country. **Individual stream** retains the direct
stream mapping option. The choice applies to this event's broadcast, survives
refresh and overrides automatic matching. **Use source broadcast** clears it.
Missing/disabled or replaced manual targets remain unavailable until reviewed;
no permanent channel, EPG assignment or name changes are made. Manual links are
per broadcast, not global broadcaster aliases.

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

## Events on the TV dashboard

**Up next** shows up to six saved events across the next seven calendar days in
your selected timezone. Eligible **Live · reported** events appear first, then
nearest timed starts, followed by date-only fixtures labelled **Time TBC**.
Finished, cancelled, archived and explicitly ended events are excluded. A live
report without an end expires from this summary 24 hours after its start; fully
undated events remain in the full agenda. These labels do not verify playback.

Choose **All upcoming**, **Following** or **My interests**. **Customize events**
saves sports, competitions, teams and timezone in this browser. Interest matches
use OR: any selected sport, competition or team qualifies. Choose at least one for
My interests. Following uses the installation-wide follow state from event details.
An empty view stays empty until you change it; it never silently switches filters.

The summary refreshes every minute and on window focus. Opening an event uses the
existing broadcasts/details view; closing it returns to the agenda. Dashboard reads
never import schedules, change provider interests or start playback. Add or review
provider events from **Events** as usual.

### Removing a schedule source and finding guide programmes

In **Sources & retention**, **Delete source** removes the saved provider/URL and
stops automatic refresh. Confirmation explains that imported events, corrections,
following and permanent channels are retained. Archive unwanted events separately.
A stale edit or pending preview cannot recreate a deleted source; reload and review
it again to add it back.

Event previews and details check imported, enabled EPG guides for both participant
names in programme titles/subtitles, ignoring case, accents and punctuation.
Known kickoffs allow programme starts within 30 minutes; unknown kickoffs use the
source's local calendar date. Repeats on one guide channel, widely separated start
times and known replay/highlights labels are left unmatched. This first matching
pass requires both full team names; aliases and abbreviations are not guessed.

**Matching guide programmes** links to the guide channel and, when exactly one
active TV channel has that source-qualified guide assignment, to that TV channel.
Matches are rechecked against current guide data, including after EPG replacement.
Source broadcasts, manual choices and kickoff times stay intact. A programme
association does not prove live signal or create a permanent channel.
