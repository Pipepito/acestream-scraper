# Developer Utility Scripts

Scratch utilities used during development and debugging. Not part of the
production runtime, not invoked by CI, and not covered by tests.

## `epg/`

Originally lived at the repo root during the v1 era; relocated here in the v2
gap-closure pass to keep the project root clean.

- `check_epg_data.py` — prints a summary of EPG sources, channels, and
  programs from the configured database.
- `force_epg_refresh.py` — manually triggers an EPG refresh against the
  configured sources. (May reference v1 service signatures and require a
  small port to current `EPGService` if you intend to run it.)
- `test_epg_xml.py` — generates `generated_epg.xml` from current data for
  visual inspection.
- `test_epg_time.py` — sanity-checks XMLTV timestamp parsing.

These scripts are convenience tools, not part of the supported test surface.
For automated EPG coverage, see `backend/tests/test_epg.py` and
`backend/tests/parity/test_output_parity.py`.
