# Frontend Bold Redesign Pipeline Cluster Design

## Goal

Extend the measured-bold redesign to the scraper workflow cluster so `Scraper`, `AcestreamChannels`, and `TVChannels` feel like one connected operational pipeline: sources come in, channels are extracted, inventory is organized, and the result becomes ready for downstream EPG and playlist workflows.

## Scope

- `frontend/src/pages/Scraper.tsx`
- `frontend/src/pages/AcestreamChannels.tsx`
- `frontend/src/pages/TVChannels.tsx`
- related tests under `frontend/src/__tests__`
- verification notes in `docs/dev/frontend-design-review-evidence.md`

## Context

- The shared shell, theme tokens, and measured-bold hero pattern already exist.
- Dashboard, Health, Search, Playlist, EPG, WARP, and Settings now communicate stronger operational hierarchy.
- The remaining workflow gap is the scraper-to-channel pipeline, which still reads mostly as separate admin surfaces rather than one guided flow.
- User guidance for this phase: the scraper is important, but the extracted channels and their organization into TV channels matter more than making scrape controls feel flashy on their own.
- Chosen emphasis: show the full source-to-output flow rather than letting a single page dominate the entire redesign.

## Problem Statement

Right now this cluster is structurally competent but visually fragmented.

- `Scraper` reads like a URL table with actions rather than an intake stage for the wider system.
- `AcestreamChannels` has strong functionality but does not yet foreground inventory quality, assignment progress, or the fact that it is the bridge between scraping and TV-channel organization.
- `TVChannels` is clearer than the others, but it still feels mostly CRUD-led instead of like the final organization stage before EPG alignment and playlist output.
- Together, the three pages do not yet tell users where they are in the workflow or what the next useful action is.

## Design Direction

Treat this cluster as a pipeline chain:

1. `Scraper` = intake and scrape momentum
2. `AcestreamChannels` = extracted inventory review and routing
3. `TVChannels` = organization and downstream readiness

The pages should feel sequential without becoming a wizard. Each page must stand on its own, but the user should still sense that they are moving through a system with stages and outcomes.

To keep that pipeline visible across all three pages, each page must include a shared stage summary near the top of the page that makes the sequence explicit:

- `Sources` -> `Extracted channels` -> `TV organization`
- the current page stage should read as active/current
- the previous or next stage should be named in plain language so users understand where to go next

This shared stage summary can be implemented through compact labels, chips, or summary blocks, but it must be visibly consistent across the three pages. The goal is to prevent three disconnected hero treatments.

This means each page gets:

- a top summary that describes its role in the pipeline in plain language
- explicit status labels that explain readiness and next step
- section hierarchy that favors the most important working surface on that page
- action emphasis that reflects the stage of work rather than generic CRUD symmetry

## Page-Level Strategy

### Scraper

`Scraper` should become the intake dashboard for source URLs and scrape execution.

- The hero should summarize source readiness: enabled vs disabled inputs, recent scrape freshness, and whether the operator should run another scrape now or simply monitor results.
- The page should feel like the beginning of the pipeline: add sources, trigger scraping, then hand off mentally to extracted-channel review.
- The URL table remains the main working surface, but it should sit under a clearer operational summary instead of carrying all meaning by itself.
- If the current data model does not expose every ideal readiness metric, the hero should still use the strongest safe signals already available rather than inventing unsupported status language.

Hard hierarchy constraint:

- `Scraper` should have the lightest hero weight of the three pages.
- Its primary visual job is orientation and intake readiness, not dominating the whole cluster.
- The URL table and run actions should remain visible quickly below the summary.

### AcestreamChannels

`AcestreamChannels` should become the strongest working page in this cluster.

- The hero should frame the page as the inventory-routing stage: extracted channels are here, quality needs checking, and assignment to TV channels is the main throughput goal.
- The most important top-line cues are inventory size, status-check momentum, and assignment progress or remaining work.
- Filters should remain available, but they should read as support tools rather than the main story.
- The channel table remains dominant, because this is where review, cleanup, and assignment actually happen.
- Bulk actions should feel operational and throughput-oriented, not like isolated maintenance tools.

Fallback rule for incomplete data:

- If exact assignment-progress or quality metrics are not available, the page should fall back to safe inventory language such as total extracted channels, whether checks or assignments are available, and explicit next-step guidance rather than fabricated percentages or readiness scores.

Hard hierarchy constraint:

- `AcestreamChannels` should be the strongest page in this cluster.
- It should receive the clearest top summary and the strongest working-surface emphasis.
- Filters must not visually outrank the inventory table or the assignment path.

### TVChannels

`TVChannels` should feel like the organization and downstream-readiness stage.

- The hero should explain that this is where channel structure becomes stable enough for EPG pairing and output workflows.
- The key cues are how complete the catalog feels, whether the inventory is active and organized, and what cleanup or categorization work remains.
- The inventory table still leads, but the page should more clearly signal that these edits are shaping final output quality rather than only maintaining records.
- Empty or filtered-zero states should reinforce the operational path: broaden filters, add channels, or return upstream if the inventory is not ready.

Fallback rule for incomplete data:

- If the page cannot safely derive exact completeness or EPG-readiness metrics, it should use plain operational language about organization, categorization, active inventory, and next-step cleanup rather than pretending to know final output quality.

Hard hierarchy constraint:

- `TVChannels` should feel stronger than `Scraper` but calmer than `AcestreamChannels`.
- It is the organizing/output stage, not the loudest operational checkpoint.

## Shared Visual Rules For The Cluster

- Keep the measured-bold hero pattern already established in phase 1 and phase 2.
- Do not give all three pages identical hero intensity. The sequence should feel intentional:
  - `Scraper`: informative intake summary
  - `AcestreamChannels`: strongest operational focus
  - `TVChannels`: organized output summary with strong but calmer finish
- The three pages must share visibly related stage language so users can recognize the cluster as one pipeline even when routes change.
- Use plain-language labels such as `Source readiness`, `Inventory status`, `Assignment progress`, `Output readiness`, or similar text that explains meaning without relying on color.
- Use warm accents only when pointing to freshness, attention, backlog, or incomplete routing work.
- Preserve left-aligned, action-led composition and avoid card repetition or decorative metrics.

## Interaction And UX Rules

- Primary actions should match the page stage:
  - `Scraper`: add URL, scrape all enabled, refresh
  - `AcestreamChannels`: review inventory, bulk actions, assign TV channel
  - `TVChannels`: add/edit/organize channels and prepare them for downstream use
- The user should always be able to tell what to do next from the hero or first section without reading the full table.
- Supporting tools such as filters, CSV export, grouping, and dialogs should stay intact but become visually subordinate to the main operational path.
- Mobile layouts must preserve the same stage meaning; the summaries can stack, but they must not disappear.

## Accessibility And Verification Expectations

- Preserve semantic headings, accessible button names, table controls, and dialog flows.
- Keep keyboard access intact for key actions on each page.
- Maintain WCAG AA contrast and non-color status communication.
- Verify one phone-width and one desktop-width path for each touched page.
- Verify loading, empty, warning/error, and success-feedback states where they already exist.
- Record results in `docs/dev/frontend-design-review-evidence.md`.

Minimum verification targets:

- `Scraper` tests should assert a visible source-to-output stage summary, source-readiness guidance, and a clear next-step reference to extracted channels.
- `AcestreamChannels` tests should assert that the page opens with the strongest inventory-routing summary in the cluster, keeps the channel table primary, and keeps filters secondary.
- `TVChannels` tests should assert output-organization guidance, explicit downstream readiness language, and recovery guidance for zero-result or empty inventory states.
- Supporting tests should continue to cover accessible names and key action controls for scrape actions, assignment actions, and TV-channel organization actions.

## Acceptance Criteria

This phase is successful only if all of the following are true:

- `Scraper`, `AcestreamChannels`, and `TVChannels` read as connected stages of one pipeline.
- `Scraper` clearly communicates source readiness and scrape momentum.
- `AcestreamChannels` becomes the clearest review-and-routing page in the cluster.
- `TVChannels` communicates organization and downstream readiness rather than only CRUD maintenance.
- The redesign improves guidance and hierarchy without hiding dense operational controls.
- The cluster still feels consistent with the measured-bold shell and prior redesigned pages.
