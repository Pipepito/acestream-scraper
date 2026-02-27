# Phase 5 Architecture Smoke Checklist

Use this checklist to validate runtime behavior for supported architecture targets.

## Scope

Required targets:

- `linux/arm/v7`
- `linux/arm64`

Optional baseline:

- `linux/amd64`

## Quick CI Profile

Run in CI-friendly mode:

```bash
python3 scripts/phase_gates/phase5_gate_runner.py --profile quick --json-output > phase5-gate-report-quick.json
```

Expected:

- Multi-arch build command validates target matrix.
- Required architecture matrix entries are asserted.
- Runtime smoke plan shape validates in dry-run mode.

## Full Validation Profile

Run full architecture validation:

```bash
python3 scripts/phase_gates/phase5_gate_runner.py --profile full --json-output > phase5-gate-report-full.json
```

Expected:

- Buildx executes multi-arch build matrix.
- Required arch entries are validated.
- Runtime smoke script executes endpoint checks for required targets.

## Manual Runtime Probe (Per Target)

If additional manual confidence is needed:

1. Build platform image:
   ```bash
   docker buildx build --platform linux/arm64 -t acestream-scraper-smoke:arm64 --load .
   ```
2. Run container:
   ```bash
   docker run --rm -d -p 18080:8000 --name phase5-smoke-arm64 acestream-scraper-smoke:arm64
   ```
3. Validate health and frontend root:
   ```bash
   curl -fsS http://127.0.0.1:18080/api/v1/health
   curl -fsS http://127.0.0.1:18080/
   ```
4. Stop container:
   ```bash
   docker rm -f phase5-smoke-arm64
   ```

Repeat for `linux/arm/v7`.

## Android TV Notes

- Prefer ARM64 images where supported.
- For ARMv7 devices, monitor memory pressure and startup time.
- Run this checklist before first rollout to each Android TV hardware class.

