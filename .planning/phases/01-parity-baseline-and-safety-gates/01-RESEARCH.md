# Phase 1: Parity Baseline and Safety Gates - Research

**Researched:** 2026-02-27  
**Domain:** Scraper parity baselining, output validation, and migration quality gates  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Baseline Coverage
- Use a broad baseline source set that includes all configured sources, not a minimal representative subset.
- Include all configured sources regardless of current status (active, flaky, disabled, legacy), but track status category in reporting.
- Include auth/region-dependent sources in baseline with explicit environment requirement tags.
- Require field-level parity checks (`id`, `name`, `group`, `logo`, `tvg_id`, `tvg_name`, source linkage) plus playlist/EPG output validity.

### Baseline Scoring and Source Classes
- Disabled/legacy sources are included in baseline but scored separately from gate-critical active sources.
- Disabled/legacy sources are non-blocking by default unless explicitly promoted to gate-critical.

### Baseline Artifacts
- Use versioned golden snapshots for baseline comparison.
- Golden snapshot updates require explicit approval/change control.

### Metadata Tolerance
- Use loose/fuzzy tolerance for metadata parity on noisy fields.
- Strict normalized equality is not required for metadata matching in this phase.

### Baseline List Governance
- Baseline source list is change-controlled.
- Additions/removals require explicit review note and baseline update.

### Claude's Discretion
- Specific parity computation format and implementation details.
- Exact fuzzy-matching heuristics and threshold values.
- How non-discussed areas (gate strictness and report format specifics) are represented in initial planning proposals.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCRP-01 | Preserve existing HTTP/M3U scraping behavior in v2 | Baseline source manifest, scraper parity regression tests, gated comparison report |
| SCRP-02 | Preserve existing ZeroNet scraping behavior in v2 | ZeroNet-included baseline list, dedicated parity coverage in test matrix |
| SCRP-03 | Preserve persisted channel core fields and linkage | Field-level comparator contract and schema-aware assertions |
| SCRP-04 | Keep playlist + EPG outputs valid on representative datasets | Playlist/EPG validity tests and snapshot-backed output checks |
| QUAL-04 | Require measurable phase acceptance gates | CI-friendly gate runner + checklist evidence contract |
</phase_requirements>

## Summary

Phase 1 should create a single, repeatable parity contract that is reused by every later migration phase. The contract needs three layers: baseline inventory (what is checked), comparator policy (how parity is judged), and gate execution (when changes are blocked or allowed). This keeps scraper logic stable while permitting cleanup work around it.

The baseline must include all configured source classes (active/flaky/disabled/legacy + env-dependent) with explicit scoring semantics: active gate-critical sources block the phase gate, disabled/legacy sources are reported but non-blocking unless promoted. This matches the user’s requirement for broad visibility without false failures from known non-critical sources.

**Primary recommendation:** Build parity around versioned snapshot artifacts plus automated gate commands, then treat every phase transition as a parity re-certification.

## Standard Stack

### Core
| Library/Tool | Version Source | Purpose | Why Standard Here |
|--------------|----------------|---------|-------------------|
| `pytest` | `backend/requirements.txt` | Regression harness and assertions | Already the dominant backend test runner |
| `sqlalchemy` | `backend/requirements.txt` | Persistence-level field checks | Existing repository/model stack |
| Existing scraper modules (`http.py`, `zeronet.py`) | `backend/app/scrapers/` | Ground truth scrape behavior under test | Avoids introducing new scraper code paths |

### Supporting
| Library/Tool | Version Source | Purpose | When to Use |
|--------------|----------------|---------|-------------|
| `pytest` fixtures in `backend/tests/conftest.py` | Existing | Deterministic test setup for DB + services | Baseline and output parity tests |
| YAML/JSON baseline manifest files | Project artifact | Source inventory + snapshot governance | Baseline definition and change control |
| GitHub workflow file | Existing CI pattern in `.github/workflows/` | Automated safety gate execution | Pull requests and pre-cutover checks |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| In-repo snapshots + pytest | External golden dataset service | Higher operational complexity for no Phase 1 benefit |
| Python gate runner | Shell-only orchestration | Less structured reporting and category scoring |

## Architecture Patterns

### Recommended Project Structure

```text
backend/tests/parity/
  baseline_sources.yaml
  snapshots/
  parity_compare.py
  test_scraper_parity.py
  test_output_parity.py
scripts/phase_gates/
  phase1_gate_runner.py
docs/migration/
  phase1-parity-gates.md
```

### Pattern 1: Manifest -> Comparator -> Gate
**What:** Treat baseline data definition, parity logic, and gate execution as separate artifacts.  
**When to use:** Any phase where scraper-adjacent code can affect outputs.  
**Example:**

```python
baseline = load_baseline_manifest("baseline_sources.yaml")
result = compare_snapshot(baseline, current_run, fuzzy_fields={"name", "group"})
assert result.critical_failures == 0
```

### Anti-Patterns to Avoid
- **Hidden baselines in test code:** makes change control invisible.
- **Single pass/fail score for all source classes:** conflicts with non-blocking legacy/disabled policy.
- **Manual-only parity approval:** violates QUAL-04 measurable gate requirement.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test orchestration framework | New custom runner framework | `pytest` + thin gate wrapper | Lower maintenance, already integrated |
| Data persistence parser | New ad-hoc DB layer | Existing SQLAlchemy model/repo stack | Avoids duplicated query semantics |
| CI engine | Bespoke scripts outside workflow system | `.github/workflows` execution | Reproducible branch gating |

**Key insight:** Phase 1 is about codifying proof, not inventing new runtime architecture.

## Common Pitfalls

### Pitfall 1: Over-curated baseline selection
**What goes wrong:** Teams only validate "clean" sources and miss regressions on noisy real inputs.  
**How to avoid:** Baseline manifest must include all configured source classes with category labels.

### Pitfall 2: Strict metadata equality on noisy fields
**What goes wrong:** Benign formatting/name drift produces false blockers.  
**How to avoid:** Use fuzzy tolerance policy for noisy metadata while keeping key identity/linkage strict.

### Pitfall 3: Snapshot drift without governance
**What goes wrong:** Golden files are silently updated and regressions get normalized away.  
**How to avoid:** Require explicit baseline version bump + review note for snapshot changes.

## Code Examples

### Field-level parity contract

```python
required_fields = ["id", "name", "group", "logo", "tvg_id", "tvg_name", "source_url"]
for field in required_fields:
    assert field in channel_record
```

### Output validity checks

```bash
pytest -q backend/tests/parity/test_scraper_parity.py
pytest -q backend/tests/parity/test_output_parity.py
```

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Feature-by-feature manual parity checking | Centralized parity harness + gate runner | Lower regression risk and faster cutover confidence |
| Unstructured migration notes | Versioned baseline contracts | Auditable quality gates |

## Open Questions

1. **How large should the initial baseline snapshot set be for CI runtime targets?**
   - What we know: Broad source coverage is required.
   - What's unclear: Exact CI time budget for full vs sampled gate runs.
   - Recommendation: Define `quick` and `full` gate profiles in Phase 1 gate runner.

2. **Which metadata fields need fuzzy thresholds beyond exact match?**
   - What we know: Name/group and related noisy metadata need loose tolerance.
   - What's unclear: Final threshold values per field.
   - Recommendation: Start conservative and store thresholds in manifest for explicit review.

## Sources

### Primary (HIGH confidence)
- `.planning/phases/01-parity-baseline-and-safety-gates/01-CONTEXT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/codebase/STACK.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/TESTING.md`
- `backend/app/services/scraper_service.py`
- `backend/app/scrapers/http.py`
- `backend/app/scrapers/zeronet.py`
- `backend/app/services/playlist_service.py`
- `backend/app/services/epg_service.py`

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH (already established in repo)
- Architecture patterns: HIGH (aligned with current backend + test organization)
- Pitfalls: HIGH (directly tied to explicit user decisions and current migration context)

**Research date:** 2026-02-27  
**Valid until:** 2026-03-29
