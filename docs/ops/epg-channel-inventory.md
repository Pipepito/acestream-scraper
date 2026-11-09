# Shared EPG channel inventory

From v2.2.1, imports with the same exact XMLTV channel ID and a matching name
appear once in EPG → Channels. Name comparison ignores case and repeated
whitespace, while retaining accents, region names and quality suffixes. A matching
name with a different ID, or a matching ID with a different name, stays separate.

The Sources column lists every linked guide. Open the channel and choose a source
above its schedule to inspect that guide's programmes. Disabling a source keeps
its membership visible with a disabled label. Source filtering returns channels
from that source and still shows all their linked guides. Counts and pagination
operate on logical channels, including when duplicates cross page boundaries.

Migration `20261109_1200` introduces `epg_channel_identities` and backfills membership
links. Existing `epg_channels` rows now represent source memberships; their IDs,
programmes and string rules are preserved. TV channel assignments, recording
snapshots, overlays and XMLTV export continue using source-qualified IDs. These
are necessary because two guides may disagree about a programme or its times.

Refresh updates only the importing source's membership and programme coverage.
A changed name can move that membership to a different logical identity. Removing
a source removes only its memberships and programmes, leaving other guides intact.
No cross-source schedule precedence or automatic programme merging is introduced.
Existing source-qualified detail URLs remain valid while that source exists.

Validation: `backend/tests/test_epg_channel_inventory.py` covers grouping,
pagination, renames, separate schedules, source removal, and upgrade/downgrade
preservation. Frontend and browser tests cover the source list and source switch.
