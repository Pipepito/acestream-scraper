"""Shared M3U formatting helpers.

One place for the EXTINF quoting rules, so the curated playlists and the
tuner playlist escape attribute values the same way.
"""


def m3u_attr(value) -> str:
    """Sanitize a value for use inside a double-quoted EXTINF attribute."""
    return str(value).replace('"', "'").replace("\r", " ").replace("\n", " ")
