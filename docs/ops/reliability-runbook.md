# Reliability Runbook

## Scope

This runbook covers reliability diagnostics and recovery for:

- APScheduler lifecycle and job health
- `/api/v1/background-tasks/status` endpoint
- periodic scrape/EPG/channel-status tasks
- WARP integration endpoint failures

## Quick Diagnostic Checklist

1. Verify API health: `curl -s http://localhost:8000/api/v1/health/ | jq`
2. Check background-task status: `curl -s http://localhost:8000/api/v1/background-tasks/status | jq`
3. Look for scheduler/task failures in backend logs:
   - `Scheduled task failed`
   - `WARP_*_UNAVAILABLE`
   - `BACKGROUND_TASK_STATUS_FAILED`
4. Confirm recent database activity (new `last_run` values, channel/EPG updates).

## Background Task Status Semantics

- `status=idle`: task is healthy and not currently executing.
- `status=running`: task execution is in progress.
- `status=error`: last execution failed; inspect `last_error`.
- `status=removed`: task was unscheduled.

If a task has `status=error`, recovery is:

1. Inspect logs for root cause and correlation id.
2. Fix dependency issue (network, source URL, DB lock, WARP daemon, etc.).
3. Restart backend process to trigger clean scheduler startup and task re-registration.
4. Re-check `/api/v1/background-tasks/status` for `idle` + updated `last_run`.

## Scheduler Recovery

Symptoms:

- No periodic task activity
- stale `next_run` values
- no jobs returned in status endpoint

Actions:

1. Restart the backend process/container.
2. Confirm startup logs include scheduler start.
3. Confirm all expected job ids are visible in background-task status output.

## WARP Error Contract and Recovery

WARP failures now return stable API error codes:

- `WARP_STATUS_UNAVAILABLE`
- `WARP_CONNECT_FAILED` / `WARP_CONNECT_UNAVAILABLE`
- `WARP_DISCONNECT_FAILED` / `WARP_DISCONNECT_UNAVAILABLE`
- `WARP_MODE_CHANGE_FAILED` / `WARP_MODE_CHANGE_UNAVAILABLE`
- `WARP_LICENSE_REQUIRED` / `WARP_LICENSE_REGISTER_FAILED`

Recovery:

1. For `*_UNAVAILABLE`: verify `warp-cli` is installed and daemon is reachable.
2. For `*_FAILED`: inspect `error.context.error` for command-level failure reason.
3. Retry the operation after daemon/network remediation.

## Reliability Regression Commands

Run these when diagnosing release risk:

```bash
PYTHONPATH=backend backend/venv/bin/pytest -q \
  backend/tests/test_background_tasks.py \
  backend/tests/test_task_service.py \
  backend/tests/test_warp.py \
  backend/tests/test_error_contracts.py
```
