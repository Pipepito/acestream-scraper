# Pitfalls Research

**Domain:** Large brownfield migration to a consolidated v2 stack
**Researched:** 2026-02-27
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Breaking scraper behavior during refactor

**What goes wrong:** Source parsing regresses while cleaning architecture, causing silent channel loss.

**Why it happens:** Teams refactor parser internals and surrounding orchestration in the same phase.

**How to avoid:** Freeze parser behavior first; treat scraper outputs as parity contracts with regression tests.

**Warning signs:** Lower channel counts, changed metadata fields, intermittent source failures.

**Phase to address:** Phase 1-2 (parity baseline + core migration).

---

### Pitfall 2: Partial cutover leaves root and v2 both “authoritative”

**What goes wrong:** CI, Docker, and runtime paths disagree on which stack is production.

**Why it happens:** Legacy release scripts are left active while new stack evolves.

**How to avoid:** Define single cutover phase that switches build/release/runtime to v2-only and retires root paths.

**Warning signs:** Conflicting docs/workflows, duplicated fixes, deployment confusion.

**Phase to address:** Phase 2-3 (cutover + release pipeline consolidation).

---

### Pitfall 3: UI redesign without API contract stabilization

**What goes wrong:** Frontend polish work repeatedly breaks due to shifting backend payloads.

**Why it happens:** Design/UI work starts before contract freeze and typed DTO cleanup.

**How to avoid:** Stabilize v2 API contracts and typed service layers before heavy UI iteration.

**Warning signs:** Frequent type casts, page-level runtime shape checks, regression churn.

**Phase to address:** Phase 3-4 (contract stabilization then UI refresh).

---

### Pitfall 4: “Multi-arch done” means image built but not validated

**What goes wrong:** arm/v7 or arm64 images build, but runtime behavior fails on target devices.

**Why it happens:** Build success is mistaken for runtime compatibility.

**How to avoid:** Add runtime smoke tests/checklists on representative ARM environments.

**Warning signs:** Startup crashes, missing dependencies, degraded performance on ARM devices.

**Phase to address:** Phase 5 (cross-arch packaging + validation).

---

### Pitfall 5: Zero-bug goal without focused verification gates

**What goes wrong:** “Bugs to zero” stays aspirational and regressions continue.

**Why it happens:** No enforced test and acceptance gates per migration phase.

**How to avoid:** Define explicit acceptance criteria and regression suites per phase; block transitions on failures.

**Warning signs:** Phase complete claims without measurable pass criteria.

**Phase to address:** All phases (especially 1, 4, 6).

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Keep legacy and v2 both active | Lower short-term migration pressure | Constant drift and duplicate maintenance | Never for final architecture |
| Skip typed contract cleanup | Faster short-term coding | High runtime breakage risk | Only temporary in spike branches |
| Broad catch-all exceptions without observability | Prevent crashes | Hides defects and makes debugging slower | Acceptable only with structured error telemetry |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Acestream engine | Hardcoding environment assumptions | Centralize config and validate at startup |
| WARP CLI | Parsing command output optimistically | Defensive parsing + explicit failure paths |
| External scrape URLs | No SSRF/validation guardrails | URL validation and network safety controls |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Row-by-row DB writes in scrape flows | Slow refresh and DB lock pressure | Batch writes and transaction scoping | Medium/high channel volume |
| In-process heavy jobs on API worker | Slow API during scheduled tasks | Isolate heavy work and tune scheduling | Frequent refresh intervals |
| Large frontend tables without optimization | Laggy UI interactions | Virtualization and filtered/paginated queries | Large datasets on lower-power devices |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Unauthenticated operational endpoints | Unauthorized control operations | Add authentication/authorization in v2 API |
| Unsanitized scrape target handling | SSRF/internal network exposure | Restrict/validate URLs and network ranges |
| Elevated container caps by default | Increased blast radius | Separate privileged modes and minimize defaults |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Function-first but clarity-poor admin screens | High operational friction | Prioritize information hierarchy and quick actions |
| Desktop-only assumptions | Poor TV/mobile usability | Responsive layout + keyboard/remote-friendly navigation |
| Hidden system/task status | Reduced trust and slower issue response | Prominent health/task/status surfaces |

## "Looks Done But Isn't" Checklist

- [ ] **Scraper parity:** verify source-by-source channel output consistency versus baseline
- [ ] **Cutover:** verify no runtime/release path still depends on root legacy app
- [ ] **ARM support:** verify runtime smoke tests pass on arm/v7 and arm64 targets
- [ ] **UI refresh:** verify critical user workflows complete without regressions
- [ ] **Bug reduction:** verify defect backlog + regression suite trend confirms stability

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Scraper regression | HIGH | Roll back parser-affecting changes, run parity diff, reintroduce incrementally |
| Cutover drift | MEDIUM | Freeze legacy changes, reconcile pipelines, enforce v2-only CI gate |
| ARM runtime failures | MEDIUM | Add architecture-specific dependency fixes and smoke-test matrix |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Scraper behavior regression | Phase 1-2 | Parity test set and output diff checks |
| Dual-stack drift | Phase 2-3 | CI/build/release prove v2-only ownership |
| Contract/UI churn | Phase 3-4 | Typed API/UI integration tests pass |
| ARM false-positive readiness | Phase 5 | Runtime smoke tests on target architectures |
| Undefined quality bar | All phases | Transition gates tied to explicit acceptance criteria |

## Sources

- `.planning/codebase/CONCERNS.md`
- `.planning/codebase/TESTING.md`
- `docs/migration/MIGRATION_GAPS.md`
- Existing v2 and legacy split structure observations

---
*Pitfalls research for: v2 consolidation migration*
*Researched: 2026-02-27*
