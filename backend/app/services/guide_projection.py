"""One effective Now/Next selection for both displayed guide and live genre filters."""
from datetime import timedelta
from app.repositories.category_repository import CategoryRepository
from app.services.event_overlay_service import EventOverlayService


def projected_guide(db, channels, reference):
    repo = CategoryRepository(db)
    lookup = repo.guide_lookup(channels, enabled_only=True)
    guide_ids = sorted({row.id for row in lookup.values() if row is not None})
    grouped = {key: [] for key in guide_ids}
    for row in repo.programmes(guide_ids, reference, reference + timedelta(hours=6)):
        grouped[row.epg_channel_id].append(row)
    # Reviewed overlays last at most twelve hours. Include ones that overlap now
    # or the six-hour next window, without changing imported programme rows.
    grouped = EventOverlayService(db).project(grouped, reference - timedelta(hours=12), reference + timedelta(hours=18))
    result = {}
    for channel in channels:
        guide = lookup.get((channel.epg_source_id, channel.epg_id))
        if guide is None:
            result[channel.id] = (None, None, None)
            continue
        rows = sorted(grouped.get(guide.id, []), key=lambda p: (p.start_time, getattr(p, 'id', 0), p.title))
        current = next((p for p in rows if p.start_time <= reference < p.end_time), None)
        following = next((p for p in rows if reference < p.start_time < reference + timedelta(hours=6)), None)
        result[channel.id] = (guide.id, current, following)
    return result
