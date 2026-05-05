# Phase 1: Parity Baseline and Safety Gates - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Define parity and migration gate rules for scraper/output behavior verification so later phases can be objectively approved or blocked. This phase clarifies decision rules and evidence expectations; it does not add new product capabilities.

</domain>

<decisions>
## Implementation Decisions

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

</decisions>

<specifics>
## Specific Ideas

- Keep parity scope broad to avoid false confidence from curated source subsets.
- Environment-dependent sources should remain visible in parity posture rather than being excluded.
- Golden snapshots should function as auditable baseline contracts.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-parity-baseline-and-safety-gates*
*Context gathered: 2026-02-27*
