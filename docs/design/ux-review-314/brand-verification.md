# SPORTZZ brand continuation — validation record

Worktree: `/srv/opencode-workspace/sportzz-brand-system`, branch
`pepe/sportzz-brand-system`, based on `de69e644`.
Date: 9 November 2026. The owner authorized a review preview and static Pages
publication after testing. Publication uses an immutable local design commit and
the administrator's narrow static route; no application/source push is authorized.
No artwork was generated. The publication manifest identifies the exported commit.

## Scope and evidence

The existing static design site was found on `design/ux-review-314`. Read-only
GitHub Pages inspection confirmed `gh-pages:/`. The site's immutable-commit
packager now includes the brand reference, shared CSS/JS and selected assets;
existing installation tools and deployment ownership are preserved.

The supplied logo variants, twelve icons, seventeen category covers, representative
optimized sports images and matching masters were inspected as actual graphics.
Nine category videos were inspected at three frames each; still photography is
the selected treatment. The asset map records unchanged supplied files and hashes.

Current browser evidence is stored under
`artifacts/visual-review/sportzz-brand-system/` (locally ignored), with detailed
JSON results and desktop/mobile/tablet screenshots. Reproduction commands:

```sh
workspace-prepare
workspace-test python docs/design/ux-review-314/compose_review06.py --pages-only
workspace-test python docs/design/ux-review-314/check_brand.py \
  --base-url http://127.0.0.1:18791/acestream-scraper/design/ux-review-314/ \
  --output artifacts/visual-review/sportzz-brand-system \
  --axe frontend/node_modules/axe-core/axe.min.js
workspace-test python docs/design/ux-review-314/check_workflows.py \
  --output /tmp/opencode/sportzz-all-workflows --smoke --exports \
  --axe frontend/node_modules/axe-core/axe.min.js
workspace-test python docs/design/ux-review-314/check_journeys06.py \
  --output /tmp/opencode/sportzz-journeys
workspace-test python docs/design/ux-review-314/check_image_contrast06.py \
  --output /tmp/opencode/sportzz-contrast
workspace-test python docs/design/ux-review-314/check_artifacts.py \
  --output /tmp/opencode/sportzz-artifacts
```

The local HTTP preview mounts `docs/` at `/acestream-scraper/`; it does not run
the application. `check_brand.py` confines browser requests to the design subtree,
checks navigation/assets/links, logo hashes, theme token equality, 320/390/820/1440
reflow, contrast pairs, reduced motion and keyboard/dialog/filter/field controls.
Existing workflow checks retain EN/ES, all three presets, synthetic playback
ownership, state transitions and saved drafts. `check_image_contrast06.py` samples
rendered backgrounds under hero text rather than relying only on axe.

## Current results

Brand reference: 1,035 checks passed across 320/390/820/1440 widths and both themes;
zero axe violations, script/console errors or unexpected requests. Initial focused
workflow pass: 96 layouts and 48 axe scans passed; the expanded responsive pass
covered 594 cases. All 48 connected journey assertions passed. Hero contrast:
24 contexts, 232 text rectangles, zero failures; lowest measured ratio 5.377:1.
Targeted Firefox and WebKit phone checks passed focus wrapping/return, filters,
theme changes and reflow, with no script errors.

The full static workflow pass covered 146 screens, 1,752 layouts and 877 axe scans,
with zero layout/accessibility failures. Three pending-state assertions initially
raced the 180ms synthetic save timer: installing the test clock did not pause it.
The assertion now pauses time before submitting and explicitly advances it after
switching presets. The affected final pass covered 584 lime layouts, 293 axe scans,
all 105 functional assertions and 14 reflow/text-enlargement cases, all passing.
All 876 current gallery images were refreshed, including 292 final lime exports.

Final artifact checks passed 4,001 local links, 657 fragments, ten generated files
without drift, 146 workflow contexts and the expected current/historical export
inventory. The local Pages rehearsal preserves all 102 non-preview files from
`c20548ab0dedaecdfec5a322595183c498091eaa` byte-for-byte. Eight packaged landing/gallery
accessibility/layout cases and six long-content cases passed. Six additional real
HTTP page/viewport cases verified runtime assets and navigation beneath
`/acestream-scraper/`, with no missing requests, script errors or overflow. Its
temporary server stopped. The final exporter now includes local reference documents
from the immutable design commit, avoiding links to an unpublished source SHA.

The documentation export rehearsal rendered all 35 top-level reference documents
and eleven escaped, non-executable source snapshots. It included nine additional
linked reference assets. All 4,507 packaged local links and 703 fragments resolved;
all 102 files outside the preview subtree remained byte-identical. Source artifact
checks were repeated after the exporter changes: 4,001 links, 657 fragments and ten
generated files passed without drift. The pinned renderer dependency is local
`Markdown==3.11.3`, not an application runtime dependency. See [publication procedure](pages-preview.md).

Documentation browser rehearsal passed 92 desktop/phone layouts, twelve axe scans
and three preset-to-specification anchor journeys, with zero console, script,
request or layout errors. The first run exposed unfocusable scrolling code blocks
and Markdown table alignment styles blocked by CSP; keyboard-focusable code blocks
and CSS alignment classes fixed those issues. The temporary server stopped and
port 18792 was freed. Read-only GitHub commit checks plus immutable tree inspection
confirmed all 1,492 distinct external source-file links reference publicly available
files. The final immutable export repeats the packaged browser checks.

During iteration, the new reference dialog needed explicit Tab wrapping, and the
grid illustration needed a valid image role for its accessible name. Both were
fixed; initial failures are retained in task logs. Python Playwright was aligned
to 1.62.0 to use the installed browser revision after an initial 1.64.1 browser
lookup failure. This was a tooling mismatch, not an application failure.

## Outstanding acceptance

The owner explicitly rejected narrowing validation for this task. Historical
design-only waivers and older passing counts are not new receipts. Full application,
Docker/flavour/architecture and browser suites are being run against this working
tree. Supported ARM images are built with the installed emulator; native ARM engine
acceptance remains distinct and requires appropriate hardware. The private policy
was inspected at `f9d7f16e05542b593b1b80470db8bc0b628dfbab`.

The clean-commit workspace wrapper cannot certify uncommitted inputs. Direct
Buildx/test commands use task-specific tags, input hashes and isolated data instead;
they do not create an immutable-commit validation receipt. The later publication
authorization permits the local design snapshot and one static `gh-pages` commit.
The Docker driver uses the shared validation lock, the bounded `workspace` builder,
all manifest-supported flavour/platform combinations, HTTP smokes, private image
acceptance probes and `backend/tests/docker`. Full native application journeys use
the controlled local fixture scenario with strict error monitoring. Separate mobile
and monitor suites cover Chromium, Firefox and WebKit.

The monitor suite exposed a browser compatibility defect: current WebKit reports
explicit cancellation as `Load request cancelled`. A real abort probe confirmed the
exact message for GET/HEAD/POST. The monitor now classifies that exact message only
for reads; cancelled writes and actual HTTP/socket failures remain errors. The
existing three-browser regression suite passed all 30 tests after this change.

Visual review of the regenerated gallery also caught a CSS specificity defect:
dark lime inherited cyan from the shared theme selector. The explicit dark-lime
accent now retains the supplied #B6FF00. Six assertions verify the rendered primary
action in all three presets and both themes. Final brand checks, the 24-context
hero contrast pass and the refreshed lime exports cover this correction.

The full application gate passed with the prepared dependencies and isolated
temporary test data:

```sh
TMPDIR=/dev/shm/sportzz-brand-suite CI_USE_PREINSTALLED_DEPS=1 \
  flock /srv/opencode-workspace/checks/validation.lock \
  workspace-test bash scripts/ci/run_v2_test_suite.sh --profile full
```

Results: four Docker documentation-contract tests, 2,562 backend tests and 659
frontend tests across 106 suites passed. No warnings or skips were reported.
Frontend lint (zero-warning limit), TypeScript, OpenAPI/client drift, production
build and Pages-helper drift checks passed. Full log:
`/tmp/opencode/sportzz-application-final.log`. Application runtime sources remained
unchanged by this work; E2E changes are the fixture/monitor fixes above and the
phone-layout assertion correction below.

Docker and full browser-journey acceptance remain outstanding. The initial mobile run passed 219 of
236 cases; eight startup cases lacked the auth-status fixture and nine Firefox
cases failed during the concurrent workload. After correcting that fixture and
serializing browser workers, all 64 cases across the seven affected specs passed
on all four projects. Together with the unchanged passing cases, this covers all
236 mobile cases. The temporary preview stopped and port 18841 is free.
Native journeys also encountered timeouts and a real
multicast `PermissionError` in Zeroconf; strict monitoring retained that evidence.
The initial amd64 scraper image passed build, HTTP startup and private runtime
acceptance. The next image build was interrupted deliberately to serialize
disk-heavy validation after observing blocked I/O and request timeouts. Completed
image evidence is retained; the interrupted build is not counted as a pass.

The initial native Firefox run ended with 34 passes, 14 failures and ten blocked
follow-on cases. Its fixture/backend processes exited and ports 18839/18840 are
free. The first full unit-suite attempt was interrupted after 508 passes and one
startup-fixture timeout; it is not a full-suite pass. SQLite commits took multiple
seconds under the concurrent disk workload. The full gate is rerunning with
isolated memory-backed temporary data and the shared validation lock, retaining
the original assertions, warning policy and timeouts. That rerun passed as recorded
above; the native browser rerun is serialized after it with fresh temporary data.

That fresh native Firefox rerun finished with 55 passes and three failures. Its
fixture/backend processes stopped and ports 18839/18840 were freed. Two failures
were test setup/expectation defects: the isolated recording directory was missing,
and the Live TV test assumed simultaneous player/search visibility on a phone,
although the existing mobile suite and application stack those sections. The
runner now creates the directory; the Live TV assertion scrolls between sections
while checking advancing playback and unchanged session ownership. Their focused
rerun is queued behind the Docker matrix. The third failure remains environmental:
Zeroconf sends during Cast navigation receive `PermissionError: [Errno 1] Operation
not permitted` on the VM interfaces. Strict error monitoring retains it; no warning
suppression or infrastructure policy change was made. These are outstanding native
results, not a claim of complete application/browser acceptance.

Physical-device logo optical checks, print proofs and native assistive-technology
review remain unverified. Static examples do not certify production media behavior.
