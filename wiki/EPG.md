# Regional HTML guide sources

EPG → Sources accepts these optional HTML sources alongside XMLTV:

- TV Rioja: `https://proyectos.larioja.com/tvr/dimeprogramacion/dimeprogramacion.php?dia=0`.
  Seven weekday pages form the current Madrid calendar week's guide. The page
  supplies weekdays, not dates: the adapter does not project the past weekdays into
  next week. Ends use the next programme start, with midnight for the final row.
- Sincroguía: a channel page under
  `https://sincroguia-tv.expansion.com/programacion/`, such as `la-7-rioja`.
  Its dated schedule, local start/end times and midnight crossings are converted
  to UTC. Unrelated highlights on the page are ignored.

No sources are added automatically. Invalid markup, ambiguous daylight-saving
hours or incomplete page fetches fail the refresh and keep the previous guide.
The complete refresh is limited to 90 seconds and each page to 2 MiB.

Import football schedules under Events. For reviewed event windows over regular
XMLTV listings, see [Sports events](Sports-Events.md#place-an-event-in-exported-guides).
