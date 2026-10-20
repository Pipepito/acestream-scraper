# HTTP streams and broadcasters' live channels

Besides AceStream ids, a playlist source can bring ordinary HTTP/HLS streams, and a few broadcasters' websites can be added as sources of their own live channels.

## HTTP/HLS entries in a playlist

When a scraped M3U has an `http://` or `https://` entry that is not an AceStream link, it is kept as a stream instead of being dropped.

- **Its id** is `url:` followed by a hash of the URL. Scraping again updates the same stream instead of adding a copy.
- **In generated playlists** it appears with its own URL, whatever link format you chose: link formats only apply to AceStream ids. In a relay format (`/tuner/channel/...`), a TV channel whose first source is an HTTP stream is also handed that URL; the TV relay only opens AceStream sources.
- **Headers.** If the playlist publishes `#EXTVLCOPT:http-referrer`, `http-user-agent` or `http-origin` for an entry, they are kept and written in the `url|Referer=...` form that Kodi sends with every request. Some CDNs answer 403 without them.
- **Status checks** read the playlist, its first variant and the first KB of the newest segment, with the stream's headers. They never open an engine session.
- **"Online only" playlists** include HTTP streams that have not been checked yet. Streams a check found dead are left out.

Other schemes (`rtmp://`, relative paths) are still dropped.

### Streams whose manifests are served by the scraper

Some HLS streams that need headers are read cut short by ffmpeg, and therefore by Kodi: the last line loses its `.ts` and the whole list is rejected. For those, the playlist points at `/live/<stream id>`, and the scraper fetches each manifest with the stream's headers and serves it whole. Only manifests pass through the scraper; the video segments still go straight from the CDN to the player.

## Broadcasters' live channels

Some Spanish free-to-air broadcasters publish no playlist, but their websites play from public APIs. Add the website as a scraper source to import its live channels:

| Source URL | Channels |
|---|---|
| `https://www.atresplayer.com` | Atresmedia (Antena 3, laSexta, Neox, Nova, Mega, Atreseries) |
| `https://www.mediasetinfinity.es` | Mediaset (Telecinco, Cuatro, FDF, Divinity, Energy, Be Mad, Boing) |
| `https://www.telemadrid.es` | Telemadrid, La Otra |
| `https://www.7riojaplay.tv` | 7 TV La Rioja |

None of them needs an account. Their links carry tokens that expire, so they are never stored: the playlist points at `/live/<stream id>`, which asks the broadcaster for a fresh link when the player opens the channel and redirects to it.

`/live/` needs no API token, because a player following a playlist link cannot send one. Like the tuner routes, it only answers clients allowed by `TUNER_ALLOWED_NETWORKS`.

These integrations depend on each broadcaster's website and can break when it changes.
