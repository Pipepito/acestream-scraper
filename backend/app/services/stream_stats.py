"""Normalize a single engine sample without inventing values for absent fields."""
import math
from datetime import datetime, timezone
from app.schemas.stream_stats import StreamStats


def stream_stats_sample(state: dict) -> dict | None:
    def number(key, maximum, integer=False):
        value = state.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if not 0 <= value <= maximum or not math.isfinite(value):
            return None
        if integer and value != int(value):
            return None
        return int(value) if integer else float(value)

    peers = number("peers", 2147483647, integer=True)
    download = number("speed_down", 1e12)
    upload = number("speed_up", 1e12)
    if peers is None and download is None and upload is None:
        return None
    return StreamStats(
        observed_at=datetime.now(timezone.utc), peers=peers,
        download_speed_kbytes_sec=download, upload_speed_kbytes_sec=upload,
    ).model_dump(mode="json")
