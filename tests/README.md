# Legacy Root Tests (Reference Only)

This `tests/` directory is legacy and retained only as migration reference.

Do not use this suite for required CI checks.
Canonical regression ownership is:

- `backend/tests/`
- `frontend/src/__tests__/`
- `scripts/ci/run_v2_test_suite.sh`

When migrating useful assertions from this directory, add them to canonical test locations and document the replacement in `docs/testing/test-ownership-matrix.md`.
