# Channel management

**Acestream Channels** is the inventory of discovered stream IDs. **TV Channels** groups those IDs into stations with numbers, favorites and EPG. **Live TV** is the viewing catalogue. See the [illustrated walkthrough](../Usage.md) for the complete import-to-playback workflow.

## Build the inventory

1. Add enabled source URLs in **Scraper** and run Scrape, or add engine search results in **Search**. An import does not establish online status.
2. In **Acestream Channels**, check signal and assign streams to TV channels. A TV channel can have several alternatives; a stream has at most one TV-channel assignment.
3. Add XMLTV sources in **EPG → Sources** and refresh. Review guide channels, create stations from unlinked entries and check matching/rules before accepting bulk changes.
4. Use **TV Channels → Auto-match streams → Find matches** for a preview across all TV channels. Nothing is selected initially. A country assumption fills missing country information for this analysis only; it neither rewrites metadata nor excludes explicitly foreign stations. Select stations or individual IDs and choose **Assign selected**.

## Numbers, favorites and filters

Edit **Number** in the table or phone card. Enter or blur saves; blank clears. Toggle the **Favorite** star independently of the channel's other actions.

Search, Category, Status and Favorites stay visible. **Advanced filters** holds the other filters and displays an active count. Filtering applies across the full catalogue before sorting and pagination. **Reset filters** clears the current selection.

**Reorder channels** shows every channel, regardless of current filters. Drag the handle, use its keyboard interaction, or use arrow buttons to preview consecutive numbers from 1. **Save order** saves the complete order in one operation. **Cancel** leaves numbers unchanged. A concurrent inventory change is rejected instead of silently overwriting it; reload and reorder again.

## Guide mapping and recovery

A TV channel carries one EPG identity. Its detail page shows the current/upcoming guide and attached streams. Wrong regional editions or mismatched IDs need a mapping correction, not repeated refreshes. Guide times use the browser's timezone.

If an older import left links missing, refresh the EPG source and review matching again. Preserve manually assigned links; do not clear all guide/channel records as a first troubleshooting step. See [EPG troubleshooting](../Troubleshooting.md#programme-guide-is-empty-or-wrong).

## Publish the catalogue

In **Playlist**, choose **TV channel relay (automatic failover)** for one stable station entry with backup sources. It uses `{tv_channel_id}`. The individual **Server relay** format uses `{channel_id}` and plays that one ID. Unassigned streams can be appended last; they retain individual URLs without channel failover.

The format editor is shared with **Settings → Stream links**. Changing a default affects other consumers of that default. Set **Integrations → Public address** before copying links to other devices. See [relay recovery](../Media-Servers.md#channels-with-several-streams) for default client reconnection and experimental transcoding behavior.
