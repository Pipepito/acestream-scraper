# Import management screenshots

Captured 2026-10-27 from application commit `fbb5c1a` in the locally built
ARM64 `scraper-acestream-acexy` image. These are real SPA/API captures against
the migrated SQLite database, using a controlled upstream catalogue and source
for repeatable partial-result and exclusion states. No browser API responses
were mocked. The example names and stream IDs are synthetic.

| File | Page | Theme | Viewport |
| --- | --- | --- | --- |
| [searches-light-1440.png](searches-light-1440.png) | Saved searches | Light | 1440 × 960 |
| [exclusions-dark-1440.png](exclusions-dark-1440.png) | Import exclusions | Dark | 1440 × 960 |
| [exclusions-light-390.png](exclusions-light-390.png) | Import exclusions | Light | 390 × 960 |
| [searches-dark-390.png](searches-dark-390.png) | Saved searches | Dark | 390 × 960 |

The saved search is deliberately partial: two existing streams, one excluded
candidate and one unresolved candidate. Existing metadata remains unchanged.
Automatic refresh was enabled for the test and paused during cleanup.

Reproduce only against an isolated test installation. From `e2e/`, with the
image running on port 18000 and its logs captured to the specified file:

```bash
E2E_TARGET=docker E2E_BASE_URL=http://127.0.0.1:18000 \
E2E_REQUIRE_ENGINE=0 E2E_STRICT=1 \
E2E_BACKEND_LOG=/tmp/import-pr-container-final.log \
E2E_IMPORT_SCREENSHOTS_DIR="$PWD/../docs/dev/screenshots/import-exclusions-saved-searches" \
env -u NO_COLOR npx playwright test tests/18-import-management.spec.ts
```

The journey controls upstream responses, exercises real queue deduplication,
manual/scheduled imports and preservation, and checks for horizontal overflow.
The container must reach the host fixture through `host.docker.internal`, and
private source fetching must be enabled for this isolated test. The engine
precheck is disabled because this test temporarily selects its controlled
catalogue; bundled engine and Acexy health are verified separately.
