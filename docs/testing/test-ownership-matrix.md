# Test Ownership Matrix

## Canonical Test Locations

Required regression checks are owned exclusively by:

- `backend/tests/`
- `frontend/src/__tests__/`
- `scripts/ci/run_v2_test_suite.sh`

CI-required flows must call `scripts/ci/run_v2_test_suite.sh` (directly or indirectly).

## Legacy Root Suite Status

`tests/` is a legacy reference area and is not authoritative for required checks.

- Purpose: historical migration reference; equivalent required coverage now lives in canonical suites.
- Policy: new regression tests must be added to canonical locations, not to root `tests/`.
- Removal condition: once all useful legacy assertions are migrated, root `tests/` can be deleted.

## Migration Mapping

| Legacy scope (`tests/`) | Canonical replacement | Status |
|---|---|---|
| URL refresh and shape checks (`tests/integration/test_api*.py`) | `backend/tests/contracts/test_urls_contracts.py` | Migrated |
| URL type + `ScrapedURL.update_status` behavior (`tests/unit/test_url_types.py`, `tests/unit/test_scraped_url.py`) | `backend/tests/regression/test_legacy_behavior_parity.py` | Migrated |
| Acestream channels operational page flow | `frontend/src/__tests__/AcestreamChannelsPage.test.tsx` | Migrated |

## Execution Contract

Quick profile:

```bash
bash scripts/ci/run_v2_test_suite.sh --profile quick
```

Full profile:

```bash
bash scripts/ci/run_v2_test_suite.sh --profile full
```

### Tests inside a built application image

Use a disposable container with the same committed source snapshot and the
image's installed Python dependencies. The backend suite also tests repository
tooling, so prepare Git, Node and the frontend build helper's `fs-extra` dependency
in that disposable test environment and run as
an unprivileged user (the sudo-denial bootstrap test requires that context).
Do not install these test tools into a published application image.

For real-media remux tests, keep `FFMPEG_BINARY_PATH` pointed at the shipped
`/opt/ffmpeg/bin/ffmpeg`. Its deliberately small build has no lavfi input,
libx264 encoder or framemd5 output. Set `FFMPEG_TEST_TOOL_PATH` to a separate full
FFmpeg used only to generate and inspect test media, for example
`/usr/bin/ffmpeg` installed in the disposable container. The application's
remux subprocess still runs the production binary. Without that override,
tests use the same full local FFmpeg for both roles.
