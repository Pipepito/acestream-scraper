# Wiseplay / W3U catalogues

Development feature for v2.2.0; these notes do not establish stable release availability.

Open **Watch → Catalogues**, or **Scraper → W3U catalogues**. Add an HTTP(S)
catalogue URL or choose a local `.w3u`/JSON file (maximum 4 MiB). **Preview URL**
reads the hierarchy without creating channels. A local file can contain absolute
linked catalogue URLs; relative links require a remote document as their base.

Review the compatible, duplicate, invalid, unsupported and failed-fetch counts.
Open folders and use breadcrumbs or Back to parent folder. Search and content-type
filters search the entire catalogue. Item details show the publisher description,
source host, guide ID, supported header names and compatibility reason. Publisher
artwork is off initially: enabling it loads unsigned image URLs directly in your
browser without a referrer. Images are never treated as media or child documents.

**All folders** selects the complete tree. Clear it to select individual folders;
a selected folder includes all its descendants. Choose **Compatible live streams**
or **AceStream only**. Check **Import selected compatible entries as permanent live
channels** only after reviewing their content, then **Save catalogue and import**.
Leave it unchecked to **Save catalogue** without new channel imports. Explicit
event and VOD records cannot become permanent channels. Unsupported entries stay
in the saved tree but cannot play. Preview tokens expire after 15 minutes or when
superseded by four newer previews. Restarting the server also expires them; preview
again if necessary. A changed/deleted catalogue rejects an old preview.

Imported streams use the existing web player, audio/subtitle choices and playback
route. Open a stream's details and choose **Play source**. AceStream streams also
have the existing remote-player actions in the player. HTTP catalogue streams support browser playback only: they are excluded from
playlist exports and do not offer remote-player actions, to keep source URLs and
header values private. AceStream catalogue streams remain exportable. A working import is not proof of signal, origin availability or
browser codec compatibility. Different IDs with identical names stay separate;
item details let you select other same-title entries in the same folder. No TV
channel or EPG assignment is inferred. Use the normal channel management and guide
matching workflows when you want an imported stream assigned to Live TV.

Favorites (up to 500) and recent accessed items (last 100) are stored in this browser,
scoped to the saved catalogue and entry. They are not shared with other browsers
or TV-channel favorites. Clearing browser storage removes them. If browser storage
is blocked, they last only for the current page session.

## Refresh and removal

**Preview refresh** re-reads remote catalogues before any import changes. Local
uploads use **Review selection** against their saved snapshot; upload another file
to import a revised local catalogue. Enable **Refresh with scheduled scraping** in
the preview to use the existing scheduled scraping interval, clock anchors and FIFO
maintenance queue. It is off by default. Catalogue refresh runs after ordinary
sources in that scheduled job. Scraper's manual “scrape all” is still for ordinary
scraper URLs; use Preview refresh for a catalogue.

Each refresh keeps the selected branch identities, reviewed live entries and stream-type filter. New entries require review before channel insertion. Folder
identity uses its parent and link (or name for inline folders); a moved/renamed
folder may need a new selection. A refresh that removes a selected folder fails
rather than silently broadening the import.

A failed root fetch writes nothing. A partial traversal retains previous missing
entries, marked **Retained**; if the merged result would exceed the record limit,
the previous inventory is kept. Full successful refreshes replace the browsable
snapshot, but **never delete imported channels**. Deselection, removal from the
publisher's list, and **Remove catalogue** also leave imported channels and manual
assignments intact. Remove unwanted channels explicitly in Acestream Channels.
Existing channel metadata, active choices and assignments are preserved; a new
stream URL or different headers creates a different HTTP identity. Duplicate IDs
share the stored channel while retaining each catalogue occurrence's metadata.

The catalogue stores private source URLs, supported header values and bounded
conditional-fetch data in the installation database. Public catalogue responses
show hosts and header names, not URL queries or header values. Protect database
backups as you do other source configuration. W3U-owned HTTP channels are excluded from playlist exports; this does not change
existing streams already imported by another source.

## Compatibility

| Input | Current handling |
| --- | --- |
| `acestream://` plus exactly 40 hexadecimal characters | Normalized ID, existing direct/Acexy route |
| Loopback `http(s)://localhost:6878/ace/getstream?id=…` (also 127.0.0.1/::1) | Normalize the complete ID; do not connect to publisher loopback |
| Direct HTTP(S) `.m3u8` | Existing guarded HLS input proxy; unencrypted/AES-128 and fragmented MP4 use the current player |
| Direct HTTP(S) `.ts` | Existing guarded MPEG-TS input proxy |
| Existing broadcaster resolver schemes | Resolve at playback through the existing broadcaster adapters |
| `userAgent`, `referer`/`referrer`, `origin` | Inherit through folders; map to User-Agent, Referer, Origin for HTTP media only |
| Arbitrary headers, cookies, authorization fields | Unsupported; no silent credential forwarding |
| Signed direct media URLs | Private saved source until refreshed; expiry/region restrictions can prevent playback |
| Website, PHP, `isHost`, `embed`, extensionless unknown media | Unsupported pending an explicit, tested resolver; never execute publisher scripts |
| DASH `.mpd`, DRM fields, other schemes | Unsupported; no DRM bypass |
| Movie files and explicit movie/series/VOD entries | Retained as unavailable VOD; playback/progress/episodes belong to #99 |
| Sports events | Save the catalogue, then use **Add as event** in a compatible entry’s details |
| Publisher subtitles / player-specific options | Not applied; use the existing player's discovered audio/subtitle choices |

Source video normally passes through without transcoding. Browser codec limits,
media delivery, external-player compatibility and CDN expiry remain visible
playback constraints. These classifications are not a claim of Wiseplay parity.

## Limits and troubleshooting

One traversal allows 64 HTTP requests including redirects, 16 MiB aggregate
input (cached documents count too; failed reads reserve their permitted byte budget), 4 MiB per document, 10,000 entries, 12 nested
levels, and 45 seconds. Each request has at most 10 seconds and shares the total
deadline. Repeated documents are reused within a traversal; conditional requests
reuse ETag/Last-Modified data on refresh. Cycles and root self/update URLs do not
become playable items. Both `groups` and `stations` are parsed; linked groups
remain navigable even when the publisher sets `import: false`.

Only two previews may run concurrently. Upload admission, body size and a
30-second upload deadline apply before JSON parsing. If a limit is reached,
preview a smaller child catalogue directly. Fetches use the existing guarded
source client, including DNS pinning, redirect validation, private-source settings
and unconditional metadata-address denial. Preview errors do not reveal upstream
bodies or signed URLs. Scheduled job history includes catalogue failures and
partial refresh counts alongside ordinary source results.

See [HTTP streams](HTTP-Streams.md), [Web player](Web-Player.md), and
[Extraction recipes](Extraction-Recipes.md) for the shared import/playback paths.


## Add a catalogue broadcast to Events

Save the catalogue first; live-channel import is optional. Open a compatible
entry's details and choose **Add as event**. Review the title, sport, competition,
source timezone and start time. Leave the time blank when unknown. Preview, select
the event explicitly, then save it. **Open Events** takes you to its broadcasts.
Private media URLs and headers stay on the server, and no TV channel is created.
Movie/VOD and unsupported entries cannot use this action. Existing broadcaster
resolver entries need an explicit mapping to an existing stream in Events.

Refresh the catalogue and review the entry again to update an event. W3U event
updates are manual; the catalogue's scheduled-refresh switch does not change event
schedules. Stable unique publisher IDs preserve event identity across signed URL
changes. Without one, changing the folder or media creates a different identity:
review it carefully. Catalogue removal keeps existing events and channels.
