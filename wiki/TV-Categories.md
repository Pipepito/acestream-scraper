# Channel categories and On now

Live TV opens with a category grid. Select a category to see its channels, or use
**All channels**. Search, Favorites only and Online only apply to the complete
catalogue before counts and pages are calculated. Returning to the grid or
switching discovery modes does not stop the current player.

**Channel categories** describe a channel's usual content. They do not change when
a new programme starts. **On now** uses all the current programme's guide genres;
a channel can appear under more than one genre. Counts therefore need not add up
to the total. No current guide and an unclassified programme are separate groups.
The catalogue refreshes every 30 seconds.

## Assigning categories

In **TV Channels**, edit a channel to choose a standard category or type a custom
one. Clearing a category manually keeps that choice protected. Existing categories
are preserved during upgrades.

**Review channel categories** previews suggestions for the current inventory page.
Nothing is selected or saved automatically. Suggestions can come from a reviewed
broadcaster identity, recognized attached-stream groups or a representative guide
schedule. Conflicting or insufficient evidence produces no suggestion. Select the
rows you agree with and choose **Apply selected**. If any evidence changes, the
whole selection is rejected so you can review again.

Manual, imported and reviewed assignments are protected. **Allow suggestions**
explicitly clears a protected assignment; a subsequent suggestion still needs
review. This operation affects the channel category, not its stream metadata.
Unrecognized imported groups remain available on their streams. New channels
created from playlists use a stable imported category only when the explicit
groups agree on one recognized category.

## Logos and programme metadata

Channel cards try the saved channel logo first, then the icon from its exact guide
source/channel mapping. If both are missing or fail, they use a category
illustration, then a neutral fallback. Current programme images do not replace
channel logos. Category identity does not depend on having a dedicated image.

Guide schedules and XML exports retain every programme category, including its
order and language. Unknown labels remain visible. The original single-category
API field remains available for older clients. New recordings preserve these
categories in their immutable programme snapshots.
