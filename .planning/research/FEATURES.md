# Feature Research

**Domain:** IPTV/acestream scraping and channel management platform modernization
**Researched:** 2026-02-27
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Reliable source scraping (HTTP/M3U/ZeroNet) | Core reason users run the app | HIGH | Must preserve current scraper behavior parity |
| Channel CRUD + filtering/search | Daily operational workflow | MEDIUM | Must be fast on large channel lists |
| Playlist export (M3U) + EPG support | Essential downstream consumption path | HIGH | Includes EPG source refresh and mapping paths |
| System/config/status visibility | Users need operational trust | MEDIUM | Health, engine status, task visibility are expected |
| Stable Docker deployment | Common deployment mode for this app type | MEDIUM | Must be deterministic across target arches |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Clean, modern UX with responsive/admin-friendly flows | Reduces operational friction significantly | MEDIUM | Strong target for this migration |
| Android TV-class compatibility focus | Expands practical deployment options | MEDIUM | Start with image/runtime compatibility, then UX polishing |
| Robust task reliability with fewer silent failures | Improves trust versus brittle hobby tools | HIGH | Needs better observability and failure handling |
| Low-defect architecture and strict contracts | Easier long-term maintenance | HIGH | Requires structural cleanup and test discipline |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Preserve every legacy endpoint/route unchanged | Avoid client updates | Keeps legacy complexity and blocks cleanup | Publish clear v2 API and migration notes |
| Full architectural rewrites while changing scraper logic | “Do everything at once” temptation | High regression risk on core value | Freeze scraper behavior first, optimize later |
| UI over-animation/visual novelty over usability | Looks modern in demos | Slows real operations and TV-device usage | Prioritize clarity, speed, remote-friendly interactions |

## Feature Dependencies

```
v2 Runtime Cutover
    └──requires──> Build/Release Consolidation
                         └──requires──> Root Legacy Retirement

UX Redesign ──requires──> Stable v2 API Contracts

ARM Multi-arch Packaging ──requires──> Docker Buildx Pipeline + Runtime Validation
```

### Dependency Notes

- **UX refactor requires stable API contracts:** frontend efficiency depends on backend schema consistency.
- **Big-bang cutover requires release consolidation:** root and v2 split pipelines must be unified first.
- **ARM support requires build + runtime validation:** image build success alone is insufficient.

## MVP Definition

### Launch With (v1)

- [ ] Full v2-only app path replacing root legacy runtime
- [ ] Scraper behavior parity for currently working sources
- [ ] Core channel/playlist/EPG/config/status functionality validated end-to-end
- [ ] Updated UI with improved responsiveness and operational clarity
- [ ] Multi-arch images for `linux/arm/v7` and `linux/arm64`

### Add After Validation (v1.x)

- [ ] Advanced performance tuning and heavy query/task optimization
- [ ] Deeper Android TV interaction polish (remote UX specifics)

### Future Consideration (v2+)

- [ ] Worker-queue architecture for high-load async jobs
- [ ] Optional API auth model if deployment contexts require stronger isolation

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| v2-only cutover with parity | HIGH | HIGH | P1 |
| Scraper logic preservation | HIGH | MEDIUM | P1 |
| UI/UX modernization | HIGH | MEDIUM | P1 |
| ARM v7 + arm64 release support | HIGH | MEDIUM | P1 |
| Structural backend cleanup | HIGH | HIGH | P1 |
| Deep performance optimization | MEDIUM | HIGH | P2 |
| TV remote-specific UX enhancements | MEDIUM | MEDIUM | P2 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| Core scraping reliability | Variable quality | Often brittle around source changes | Preserve stable parser logic while cleaning architecture |
| UI operations usability | Often outdated/admin-hostile | Mixed | Deliver clear, fast, responsive operational UI |
| Multi-arch deployment | Sometimes partial | Often amd64-only | Explicit first-class support for arm/v7 and arm64 |

## Sources

- `.planning/codebase/CONCERNS.md` and `.planning/codebase/ARCHITECTURE.md`
- `docs/migration/development-progress.md`
- `docs/migration/development-phases.md`
- Existing v2 implementation and tests

---
*Feature research for: v2 consolidation migration*
*Researched: 2026-02-27*
