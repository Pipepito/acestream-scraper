# Using Acestream Ids Scraper

This walkthrough starts with a running container and ends with a playlist you can open in VLC, Kodi, or an IPTV app. Screenshots were refreshed from a running Scraper test installation on 8 September 2026. Addresses and source URLs are hidden where needed; your catalogue and enabled services will differ.

## Before you begin

Open `http://localhost:8000` (replace `localhost` with the Docker host's address when using another device).

If you have not created the container yet, use the [Docker command builder](https://pipepito.github.io/acestream-scraper/). It asks about your CPU, engine, proxy, and optional services, then produces a ready-to-copy `docker run` command or `docker-compose.yml`. The [project README](https://github.com/Pipepito/acestream-scraper#readme) gives the short project overview; the [Installation Guide](Installation.md) and [Docker Guide](Docker.md) contain the full details.

## Find your way around

Navigation groups **Watch** (TV dashboard, Live TV, Catalogues, Events), **Manage** (sources, Search, stream and TV inventories, EPG, Playlist), **Integrations** (Public address, Web player, Remote players, Media servers, Telegram), and **System** (System status, WARP, Settings). The top-left button collapses the sidebar on desktop and opens the menu on a phone. The theme button switches between light and dark.

A **stream** is one AceStream content ID. A **TV channel** groups stream IDs for one station, with its channel number, favorite flag and programme guide. Scraping discovers streams; assigning them to TV channels creates the viewing catalogue.

Choose **Wiki** in the top bar for these guides and troubleshooting help. It stays available on phones and with the sidebar collapsed, and opens in a new tab so your current page and playback remain open.

## Step 1: Open the TV dashboard

The **TV dashboard** at `/` is the landing page. It shows browser playback and server
relays, immediate and followed events, saved channels and streams, guide coverage, and time until the next source, guide and stream-check updates. Running and queued
updates show their current state; results and history stay on System status. **Watch TV** opens the viewing catalogue; **Events** opens saved schedules.
**Up next** shows up to six saved events. Choose All upcoming, Following or My interests;
Customize events saves sports, competitions, teams and timezone for this browser.
Open an event to view broadcasts or follow it. See [Sports events](Sports-Events.md).
Players connected directly to an external engine are outside the playback summary.
Starting or failed sessions have their own labels and are not counted as playing.

Open **System status** under System (`/system`) for service health, software version,
storage, diagnostics and the complete scheduled-job history. Services distinguish
running, stopped, disabled, external and not-installed states. An unavailable status
read stays unknown; it is not reported as healthy.

The playback and checking engines have separate Start, Stop and Restart controls.
Stop pauses automatic engine recovery until Start/Restart or a container restart.
**Download diagnostics** collects recent scraper and service logs. Scheduled jobs
retain their last launch and result across restarts; unfinished runs are interrupted.

Engines are optional. A scraper-only installation can manage sources and playlists;
HTTP browser playback does not require AceStream. AceStream playback and engine
search need a reachable playback engine. Checks of AceStream streams need a playback
or dedicated checking engine.

## Step 2: Configure playback, checks and links

Open **Settings**. Its four tabs can be bookmarked independently:

| Tab | Use it for |
|---|---|
| **Playback** (`/settings?tab=playback`) | Save the optional engine URL reachable from the backend. A bundled engine normally uses `http://localhost:6878`. Optionally enable **Route playback through Acexy** and save its backend-facing URL. This does not start Acexy and applies to new sessions. |
| **Automation** (`/settings?tab=automation`) | Choose a dedicated checking engine and save source-scrape, EPG-refresh and stream-check intervals. Changes apply immediately. A bundled checker is read-only here; its controls are in System status. |
| **Stream links** (`/settings?tab=links`) | Add named player formats, choose the default, and set optional PID/AppID compatibility flags. The same editor is available in Playlist. |
| **API access** (`/settings?tab=access`) | Store the server's `API_TOKEN` in this browser, if one is configured. This does not set or change the server token. |

Integrations is a menu category: each setup has its own page. Public address (`/integrations/public-address`), Web player (`/integrations/web-player`), Remote players (`/integrations/remote-players`), Media servers (`/integrations/media-servers`) and Telegram (`/integrations/telegram`) can be bookmarked directly. Shared tuner settings remain on Media servers; old `/integrations` bookmarks open Public address.

Set the address other devices use in **Integrations → Public address**. A backend engine URL may use `localhost` when it shares the container; a link opened on another device must use the server's reachable address.

Without a dedicated checker, checks use the saved playback engine. With neither configured they are skipped without changing channel results. A dedicated checker outage never falls back to playback.

![Settings Playback tab with engine and Acexy routing controls](usage-08-settings.png)

![Settings Automation tab with dedicated checker and job schedules](usage-10-automation.png)

## Step 3: Add and scrape a source

Open **Scraper**, select **Add URL**, and enter a page or feed that contains AceStream links.

1. Choose **Auto-detect** unless you know the source type.
2. Use **Regular HTTP** for normal web pages, **ZeroNet** for ZeroNet content, or **IPFS** for `ipfs://`, `ipns://`, and gateway content that should be fetched through the configured IPFS gateway.
3. Keep the source **Enabled** so scheduled scrapes include it.
4. Turn on **Harvest bare content IDs** only when the source lists raw 40-character hashes without `acestream://` links.

With **Auto** or **IPFS**, `inbrowser.link` IPFS/IPNS links are fetched through
`IPFS_GATEWAY_URL` (default `http://127.0.0.1:8081` inside the container).
The browser gateway relies on a service worker and cannot serve scraper requests
like a normal HTTP gateway. Enable IPFS or configure a reachable HTTP gateway.
Native `ipns://<name>/path` links use the same route. An explicit **Regular HTTP**
selection preserves direct HTTP fetching.

Plain `.txt` lists with alternating channel-name and 40-character ID lines are
recognized automatically, preserving their names. Malformed hashes are skipped.
Unstructured bare hashes on other pages still require **Harvest bare content IDs**.
Select **Add**, then use the row's **Scrape** action. **Scrape all** processes every enabled source.

The table records the last result, last run, and number of channels found. If a source fails, its error remains visible there.

![Add URL dialog on the Scraper page](usage-02-add-source.png)

## Step 4: Review discovered streams

Open **Acestream Channels**. This is the stream inventory populated by scraping or engine search.

1. Filter by name, group, online state, or playlist visibility.
2. Use the circular-arrow action to check one stream, or **Run status check now** for the current inventory.
3. Open the row's **More actions** menu to assign a stream to a TV channel.
4. Open the row menu to edit, hide/show in playlists, mark its TV channel as a favorite, or delete it.
5. Use **Export CSV** when you need an inventory snapshot.

Hiding a stream keeps it in the database but excludes it from generated playlists.

![Acestream Channels inventory with filters and linked TV channels](usage-03-acestream-channels.png)

## Step 5: Organize streams into TV channels

Open **TV Channels**. A TV channel is the user-facing station in your playlist; it can group primary and backup AceStream IDs and carry one EPG identity.

1. Select **Add TV Channel** and enter its name and optional metadata.
2. Open the channel after creation.
3. Add one or more streams, or paste multiple IDs in bulk.
4. Set its EPG ID or link it from the EPG workflow.
5. Use the **Favorite** star in the table or phone card. Edit **Number** and press Enter or leave the field to save; blank clears it.
6. Search, Category, Status and Favorites stay visible. **Advanced filters** holds the remaining filters and shows an active count. Filters apply to the whole catalogue before pagination.
7. Choose **Reorder channels** to see the complete catalogue. Drag the handles or use arrow/keyboard controls to preview consecutive numbers from 1. **Save order** commits the full order; **Cancel** leaves stored numbers unchanged. If another edit makes the inventory stale, reload it before trying again.

To fill existing TV channels from scraped streams, select **Auto-match streams**
then **Find matches**. This checks all TV channels, including those outside the
current filters. Results are grouped by TV station with a count of matching stream IDs.
If the source sites mostly carry one country, choose it under **Assume country
for unlabelled channels** before finding matches. For example, **Spain** treats
unlabelled streams and TV channels as Spanish for this analysis. Explicit country
labels take precedence; stored metadata is unchanged. This fills missing countries,
it does not filter out explicitly labelled foreign channels. The default is
**No assumption**. Changing it clears the preview and selections.

Nothing is selected initially. Select a station or expand its streams and select
individual IDs, then select **Assign selected**. Only full station identities
are shown; uncertain names, editions and conflicting metadata are discarded.
Existing stream assignments are preserved. Ambiguous or
unmatched streams can still be assigned from the channel detail page.

The channel detail page also shows the linked guide's current and upcoming programmes.

![TV Channels inventory with filters, favorites, and stream counts](usage-04-tv-channels.png)

![Reorder preview with drag handles and arrow controls](usage-11-reorder.png)

## Step 6: Add programme-guide data

Open **EPG**. The five tabs form one workflow:

1. **Sources**: add an XMLTV URL and refresh it.
2. **Channels**: review guide channels and create TV channels from selected unlinked entries.
3. **Matching**: analyze scraped stream names, review the proposed streams and guide source, select rows, then **Apply reviewed matches**. Existing compatible TV channels are reused. Nothing is selected automatically.
4. **Rules**: manage include/exclude patterns used by matching.
5. **Export**: download XMLTV containing only your configured TV channels.

Large imports can continue in the background. Progress and future runs appear on **System status**.

**Playlist → Programme guide** shows how many catalogue streams have a linked guide
and links directly to reviewed matching. A guide imported under Sources is not
linked to streams until stations are assigned. Select a particular EPG source to
resolve competing providers; ambiguous matches are left for review.

Optional **Settings → Automation → Automatically match guide channels** applies
unambiguous exact matches after future successful scrapes and EPG refreshes. It is
off by default. It preserves assignments, favorites and channel numbers, and
leaves similar names or conflicting editions for review. The last run result is
shown below the switch. Disabling it preserves existing assignments.

M3U exports include the guide address and use the linked TV channel's guide ID.
When different sources reuse an ID, exports qualify it by source to keep their
programmes separate. Token-protected exports include the credential needed by
players to fetch XMLTV; handle downloaded playlists like the protected URL.

![EPG page showing the Sources, Channels, Matching, Rules, and Export tabs](usage-05-epg.png)

## Step 7: Build the playlist URL

Open **Playlist**.

1. Optionally filter by channel name.
2. Choose whether to include only online channels or only favorite TV channels.
3. Select a stream link format; **Default** uses the saved default (or `acestream://` if none exists). Expand **Manage link formats** to edit the shared formats without leaving this page.
4. For one stable entry per station with backup sources, add/select **TV channel relay (automatic failover)** using `http://SERVER:8000/tuner/channel/{tv_channel_id}.ts`. **Server relay** with `/tuner/stream/{channel_id}.ts` plays a specific stream and does not provide TV-channel failover.
5. Choose **Include unassigned streams at the end** if desired. In a TV relay playlist these use individual stream URLs, without channel failover.
6. Expand **Group filters** to include or exclude categories.
7. Copy the generated URL or select **Download M3U**.

The canonical player-facing endpoint is `/playlists/m3u`. The web page may generate the equivalent versioned API URL so it can include every selected option.

![Playlist page with filters and the generated M3U URL hidden](usage-06-playlist.png)

![Shared stream-link editor expanded inside Playlist; private addresses hidden](usage-12-link-formats.png)

## Step 8: Import it on another device

Select **Show QR code** to move the generated URL to a phone, TV, or IPTV app without typing it. The player must be able to reach both the web endpoint and the host used in the stream-link format.

The QR code contains the generated URL, including a token when required. Treat it like a credential if API access is protected.

In VLC, choose **Media → Open Network Stream**, paste the playlist URL, and play. Other clients usually call the same action **Add playlist by URL**, **M3U URL**, or **Open network stream**.

## Watch in the browser

Open **Live TV** for active TV channels with assigned streams, current/next programmes and favorite filtering. **Online streams without a channel** has its own search and pagination.

Choose **Watch**. The player and scrollable catalogue stay on the same page. Searching and filtering do not stop playback. **Playback options → Larger player** expands the desktop video area; **Standard player** restores the split. **Schedule** shows the current and upcoming programmes in your device timezone. Select another **Stream** or **Audio track** when available. **Stop watching** releases your viewer.

**Send to player** sends directly to a saved remote player; it does not start browser playback. Players opened on other pages use a dialog. See [Web Player](Web-Player.md) for codec requirements and error messages.

![Live TV catalogue with current and next programmes](usage-09-live-tv.png)

## Search and manual additions

Use **Search** to query the connected AceStream engine catalogue. Add one result or select several and add them together. Use **Add channel** on **Acestream Channels** when you already know a content ID.

Search returns infohashes, which are different from playback content IDs. **Add**
and **Play** resolve the selected result through the configured playback engine
before saving or opening it. A failed lookup leaves the inventory unchanged and
can be retried; **Play** does not add a channel. Saved channels and exported links
use the resolved content ID, including with Acexy routing. Catalogue search and
resolution still require the playback engine, even when a dedicated checker or
Acexy is configured.

If a result added by an older version passes **Check broadcast** but fails with
“failed to load content”, add it again from Search. The corrected content ID may
create a separate entry: move any TV assignment to it, then remove the old entry
when no longer needed. Existing entries are not rewritten automatically because
a 40-character hash alone cannot identify which kind it is.

Search shows the catalogue's availability and last update separately from the
current broadcast. **Catalogue: available** is an upstream report, not proof of
an emission now. **Check broadcast** opens a temporary engine session for that
infohash, checks increasing P2P downloads and a media sample for identified audio/video packets, then cleans up its session.
It does not add the result to your channels. **No broadcast detected** means the
check could not confirm usable media within its time limit; it is not proof
that a scheduled event or a temporarily unreachable stream will never work.

Saved-channel status checks use the same signal verification. ID lookup (found, not found, unknown) is separate from broadcast status. A timeout or engine outage is not proof that an ID is absent. Online describes the last successful check, not a playback guarantee. A live-type
flag, connected peers, cached download totals, or “got newer download” alone no
longer marks a channel online. Session creation retries once on timeout; data
observation uses the `acestream_check_timeout` setting (10 seconds by default,
capped at 120 seconds), followed by bounded session cleanup.

## API and health endpoints

- Interactive OpenAPI documentation: `http://localhost:8000/docs`
- Public health check: `http://localhost:8000/api/v1/health`
- Player-friendly M3U: `http://localhost:8000/playlists/m3u`
- Versioned playlist API: `http://localhost:8000/api/v1/playlists/m3u`

All current application APIs are under `/api/v1`. A small set of v1 playlist aliases remains so existing players continue to work.

## WARP

Open **WARP** under System, or choose **Manage WARP** in System status. When installed and enabled, The page shows connection state, mode, account, and exit location, and provides connect/disconnect controls. Enabling WARP in Docker requires `ENABLE_WARP=true`, the `NET_ADMIN` and `SYS_ADMIN` capabilities, and the `/dev/net/tun` device. Set `WARP_ENABLE_NAT=true` to connect automatically, or use the page's connect control. WARP is available on `linux/amd64` and `linux/arm64`; it is unavailable on `linux/arm/v7` because Cloudflare does not publish a 32-bit ARM package.

## Next steps

- [Configuration Reference](Configuration.md)
- [Docker and platform guide](Docker.md)
- [Troubleshooting and startup recovery](Troubleshooting.md)
- [Frequently asked questions](FAQ.md)
- [Bug reporting](Bug-Reporting.md)

## Import exclusions and saved searches

Open **Scraper → Import exclusions** to skip future imports by Name contains,
Name equals or Stream ID equals. Matching is literal and ignores name case and
repeated spaces; accents and regional markers still matter. **Preview matches**
checks current inventory without changing it. A limited preview shows “at least”.
Existing channels, favorites, TV assignments and playback stay available. Removing
or disabling a rule permits future discoveries; it does not replay Telegram history.
Manual Add can use **Add anyway** after a separate confirmation for that one stream.

On Search, **Save search** captures the last submitted query/category, even if you
have since edited the search form. Saving does not fetch or import. Manage it under
**Scraper → Saved searches**. **Run now** imports discoveries once; **Preview**
reads results without saving them, and **Import this preview** imports only that
private snapshot. Previews expire after five minutes. Automatic refresh is off by
default. Enable it to import matching results on the source refresh schedule in
Settings → Automation. Changing query/category pauses automatic refresh again.

Waiting means another maintenance job has the shared queue. A second Run now does
not create another copy. Existing channels are preserved, including operator names
and signal results. Missing results never remove channels. Deleting a saved search
keeps imported channels. Complete, partial, skipped and failed outcomes distinguish
excluded candidates from unresolved IDs and deferred work. Configure the catalogue
engine in Settings → Playback; no engine is selected silently.

Leave **Search Query** empty and click **Search** to browse all channels published
in the AceStream catalogue. Category filters and pagination still apply; each
page is fetched separately. Whitespace-only input is treated as empty. Browsing
starts only after clicking Search (or pressing Enter), not when opening the page.
