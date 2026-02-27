# Codebase Concerns

**Analysis Date:** 2026-02-27

## Tech Debt

**Dual-stack drift (legacy root vs v2 active code):**
- Issue: Active implementation is in `v2/`, but legacy root runtime/build/test assets still drive parts of CI/release.
- Why: Incremental migration from Flask/root architecture to FastAPI `v2`.
- Impact: Changes can pass/fail in one stack while breaking the other; deployment and test signals are ambiguous.
- Fix approach: Choose a canonical runtime (likely `v2`) and align CI/release, Docker, and docs to that path.

**Empty root `app/` package with stale references:**
- Issue: Root `app/` directory is empty, while root tests and root Docker/release paths still reference `app.*` and `COPY app/ ./app/`.
- Why: Code moved without complete cleanup of root workflows/tests.
- Impact: Legacy test/runtime paths can fail unexpectedly; onboarding confusion increases.
- Fix approach: Remove stale root references or restore a valid root package shim with clear deprecation notice.

**Large service/page modules:**
- Issue: Several modules are very large (`v2/backend/app/services/epg_service.py`, major frontend page files).
- Why: Feature accumulation in single files.
- Impact: High change risk, harder review/testing, greater regression probability.
- Fix approach: Split by subdomain use cases, extract helpers, and add focused tests per extracted unit.

## Known Bugs

**Frontend/backend type contract mismatch for paginated channels:**
- Symptoms: Frontend service type claims array return while pages cast to `{items,total}` manually.
- Trigger: Using `acestreamChannelService.getAcestreamChannels` types directly without casting.
- Workaround: Current page code uses custom type guard/casting in `v2/frontend/src/pages/AcestreamChannels.tsx`.
- Root cause: Service signature in `v2/frontend/src/services/channelService.ts` does not match backend response model.
- Fix approach: Update DTO/signature to paginated response type and propagate through hooks.

**Legacy tests likely broken against current repo layout:**
- Symptoms: Root tests import `app.*` modules that are not present in repository root.
- Trigger: Running root suite (`pytest tests/`) in current tree.
- Workaround: Prefer v2 backend test suite for active development.
- Root cause: Migration cleanup incomplete between root and v2.
- Fix approach: Either restore compatible module paths or retire root test suite and replace with v2 coverage.

## Security Considerations

**Unauthenticated operational endpoints:**
- Risk: Critical operations (scrape, status checks, config changes, WARP actions) appear exposed without auth middleware.
- Current mitigation: Network boundary/container isolation only.
- Recommendations: Add API auth/authorization layer for mutating and operational endpoints.

**Potential SSRF surface in scraping URLs:**
- Risk: User-provided URLs are fetched by scraper services (`ScraperService.scrape_url`) and could target internal resources.
- Current mitigation: URL type classification and parser constraints only.
- Recommendations: Add allow/deny-list policies, private network blocking, and strict URL validation.

**Sensitive process capabilities in runtime:**
- Risk: WARP-enabled deployments require elevated caps (`NET_ADMIN`, `SYS_ADMIN`) in `docker-compose.yml`.
- Current mitigation: Optional feature flag.
- Recommendations: Isolate privileged runtime mode from default profile and harden container policies.

## Performance Bottlenecks

**EPG and scraper heavy processing paths:**
- Problem: EPG refresh and scraping can run large loops/parsing in-process.
- Measurement: No repository-level p95/throughput telemetry detected.
- Cause: CPU/network intensive tasks scheduled in app process.
- Improvement path: Add metrics, move heavy work to dedicated worker queue, and batch DB writes.

**N+1-style persistence/update loops:**
- Problem: Some repository/service flows perform per-record operations with commits/refreshes.
- Measurement: Not instrumented in codebase.
- Cause: Iterative record processing in service/repository methods.
- Improvement path: Use bulk operations and transaction-scoped batching where safe.

## Fragile Areas

**Scheduler startup/shutdown lifecycle:**
- Why fragile: APScheduler runs in-process with app lifecycle and broad exception handling.
- Common failures: Silent task failures or duplicate scheduling after process/reload behavior changes.
- Safe modification: Keep explicit startup/shutdown hooks and add task-health assertions.
- Test coverage: Task endpoints exist, but scheduler lifecycle behavior is lightly covered.

**Multi-environment config path handling:**
- Why fragile: Multiple env vars and path assumptions across root scripts, v2 settings, and Docker files.
- Common failures: Wrong DB/config path or integration host mismatch at runtime.
- Safe modification: Centralize env key definitions and add startup validation.
- Test coverage: Partial config endpoint tests; end-to-end env matrix coverage is missing.

## Scaling Limits

**Single-process SQLite-backed API:**
- Current capacity: Adequate for small-medium workloads; exact threshold not benchmarked.
- Limit: Write contention and file-locking behavior under concurrent heavy tasks.
- Symptoms at limit: Slower writes, lock contention, stalled scraping/EPG updates.
- Scaling path: Move to managed PostgreSQL/MySQL and separate worker processes.

**In-process scheduled workload:**
- Current capacity: Bounded by one API process resources.
- Limit: Long-running scraping/EPG jobs can compete with request handling.
- Symptoms at limit: Elevated API latency during task windows.
- Scaling path: External queue/worker architecture (Celery/RQ/Arq) and horizontal API scaling.

## Dependencies at Risk

**Legacy Flask root toolchain still wired into release:**
- Risk: Release workflow and Dockerfile continue to depend on root legacy files.
- Impact: Deployment drift from actively developed v2 stack.
- Migration plan: Update release workflow triggers/steps to v2 backend/frontend artifacts.

**Cloudflare WARP CLI dependency:**
- Risk: `warp-cli` behavior/version changes can break runtime actions.
- Impact: WARP endpoints may fail even if core scraping/API works.
- Migration plan: Add CLI version pinning/verification and defensive parsing tests.

## Missing Critical Features

**Unified migration completion guardrails:**
- Problem: No enforced rule prevents mixing root and v2 feature implementation.
- Current workaround: Developer tribal knowledge.
- Blocks: Reliable release confidence and contributor onboarding.
- Implementation complexity: Medium.

**API authentication/authorization framework:**
- Problem: Operational endpoints are available without built-in identity controls.
- Current workaround: Deploy behind trusted/private network boundaries.
- Blocks: Safe multi-user/public deployment.
- Implementation complexity: Medium to high.

## Test Coverage Gaps

**End-to-end deployment path validation:**
- What's not tested: Build/deploy/runtime path consistency between CI release workflow and active v2 runtime.
- Risk: Production deploy breaks despite local v2 tests passing.
- Priority: High.
- Difficulty to test: Medium (requires CI environment matrix and smoke tests).

**Scheduler and long-running task reliability:**
- What's not tested: Restart behavior, overlapping jobs, task failure recovery.
- Risk: Silent data freshness regressions.
- Priority: High.
- Difficulty to test: Medium/high due to timing-dependent behavior.

---

*Concerns audit: 2026-02-27*
*Update as issues are fixed or new ones discovered*
