# Live TV usability audit and changes

Audit date: 2026-11-07. Baseline: develop `7ccf16d`, following PRs #311/#312.
Scope: read-only inspection of the installed Live TV and TV matching screens,
plus source review of viewing, import/linking, background checks and retention.
The installation was not changed. This is a scoped UX review, not a WCAG
conformance certification or proof that any third-party feed is playable.

The interface already has a consistent operational design, readable theme
tokens, named controls, a separate management inventory and an inline player.
There is no decorative redesign needed. The largest problems are the choices
offered to viewers and the effort required to organize usable streams.

## Findings and response

| Priority | Finding | Impact | Change |
| --- | --- | --- | --- |
| P1 | Live TV required only a linked stream, regardless of signal | A dead channel looked as watchable as a working one | Online only now defaults on for TV and raw streams; enabled streams only; clear empty-state escape |
| P1 | TV catalogue was cached for five minutes without polling | A recovered source could remain absent or stale | Refresh every 30 seconds; selected player/source retains its identity |
| P1 | Exact-name-only matching discarded close spellings | Operators had to search and link streams one by one | Optional similar-name review, reasons, searchable groups, exact selection, one target per stream |
| P2 | Manual Add and catalogue Search separated import from linking | Several pages/actions to make a stream useful in Live TV | Shared searchable TV picker; atomic manual linking and Search Add and Link |
| P2 | Existing cleanup covered hidden/unlinked stale imports only | No controlled way to retire repeatedly offline streams | Opt-in age/interval settings, preview, recent evidence and bounded source refresh |
| P2 | `hide_unusable` had no UI | Operators needed an API request to use the previous PR | Media servers toggle with a plain explanation |

## Scoped quality score

Scores describe the baseline surfaces inspected, on a 0–4 scale (4 strongest).
They are prioritization aids, not automated compliance results.

| Dimension | Score | Evidence |
| --- | --- | --- |
| Accessibility | 3 | Named controls and semantic headings; new flows need keyboard regression coverage |
| Performance | 3 | Batched guide query, stream pagination; catalogue refresh missing |
| Responsive layout | 3 | Phone layout retains actions; dense matching requires expanding each station |
| Theming | 3 | Established shared light/dark tokens; no measured contrast audit in this scope |
| Visual consistency | 4 | Purposeful operational styling; no unnecessary visual rewrite |
| Total | 16/20 | Main weaknesses concern behavior and workflow |

For a first-time viewer, offline and unchecked channels were indistinguishable
from useful choices. For an operator, close names disappeared from matching
instead of explaining why review was needed. On a phone, the extra import/link
navigation amplified that work. The implementation prioritizes those three paths.

## Behavioral boundaries

- Online is the last observed status, not a promise of uninterrupted delivery.
- Hiding does not disable a stream or remove it from configured check scope.
  Existing protection pauses background scans during app-owned viewing; this
  change does not increase engine contention to make the catalogue look fresher.
- Similar-name hints never change exact identity matching used by EPG/event
  automation. Different numeric feeds and explicit country conflicts are rejected.
- Cleanup is off by default, tracks new evidence only, and keeps linked streams
  unless explicitly included. Source membership alone is not a signal check.
- Imported streams can reappear after cleanup. They return unchecked, and manual
  assignments removed through the opt-in linked cleanup may need restoring.

Regression coverage includes backend linking rollback, status streak reset,
retention eligibility, migration upgrade, reviewed matching and frontend filter/
player continuity. Browser journeys exercise the built SPA across phone, tablet,
desktop and both themes. Validation evidence belongs in the PR and task logs,
not a timeless claim in this document.
