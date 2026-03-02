# Test Ownership Matrix

## Canonical Test Locations

Required regression checks are owned exclusively by:

- `backend/tests/`
- `frontend/src/__tests__/`
- `scripts/ci/run_v2_test_suite.sh`

CI-required flows must call `scripts/ci/run_v2_test_suite.sh` (directly or indirectly).

## Legacy Root Suite Status

`tests/` is now a legacy reference area and is not authoritative for required checks.

- Purpose: historical migration reference while equivalent coverage lands in canonical suites.
- Policy: new regression tests must be added to canonical locations, not to root `tests/`.
- Removal condition: once all useful legacy assertions are migrated, root `tests/` can be deleted.

## Migration Mapping (Initial)

| Legacy scope (`tests/`) | Canonical replacement | Status |
|---|---|---|
| URL refresh and shape checks (`tests/integration/test_api*.py`) | `backend/tests/contracts/test_urls_contracts.py` | Migrated |
| URL type + `ScrapedURL.update_status` behavior (`tests/unit/test_url_types.py`, `tests/unit/test_scraped_url.py`) | `backend/tests/regression/test_legacy_behavior_parity.py` | Migrated |
| Acestream channels operational page flow | `frontend/src/__tests__/AcestreamChannelsPage.test.tsx` | Added |

## Execution Contract

Quick profile:

```bash
bash scripts/ci/run_v2_test_suite.sh --profile quick
```

Full profile:

```bash
bash scripts/ci/run_v2_test_suite.sh --profile full
```
