# Frontend Bold Redesign Design

## Goal

Shift the frontend from a safe admin-template feel to a measured-bold operational product that feels more memorable, more guided, and more alive without sacrificing clarity for low-technical users.

## Context

- Audience: single users with limited technical knowledge managing an AceStream setup
- Product role: operational control panel for channels, scraper tasks, playlists, EPG, WARP, and system health
- Brand: bold, powerful, operational, direct, supportive
- Existing constraints: Material UI, IBM Plex Sans, teal/blue identity, compact dashboard rhythm, WCAG AA expectations, dual-theme support, reduced-motion support
- Chosen hero workflow: scraper activity
- Chosen intensity: measured bold

## Current Problems

- Shared tokens and layout primitives are strong, but many pages still look like a generic admin dashboard
- Hierarchy is too flat: repeated cards, similar section weight, limited scale contrast
- Scraper freshness and operational motion do not own the visual identity of the product
- The shell feels competent but emotionally neutral, especially on top-level pages
- Older pages still rely on card accumulation and explanatory copy rather than action-led composition

## Design Direction

The app should feel like an operational pulse board rather than a template dashboard. The visual center of gravity is live work: scraper cadence, system readiness, queue movement, and next actions. The redesign uses stronger hierarchy, a more intentional shell, and a warmer signal accent to make freshness and urgency feel legible at a glance.

This is not a maximalist redesign. The interface stays practical, light-mode friendly, and dense enough for operational use. Boldness comes from contrast, composition, and emphasis rather than decorative effects.

## Visual Strategy

### Personality lane

- Measured bold, not theatrical
- Linear-like polish with more operational tension
- Teal/blue remains structural
- Warm amber/rust signal appears only where freshness, attention, or queue pressure matter

### Hero moment

Scraper activity becomes the signature visual story. The most important pages should give live status, last run cadence, and follow-through more emphasis than generic metrics. Users should feel the product is actively helping them judge whether the system is moving.

The hero must also tell low-technical users what to do next:

- If scraper state is healthy/fresh, the hero should confirm that no immediate action is needed and point to the next optional workflow.
- If scraper state is stale or idle, the hero should explain that refresh may be needed and expose the main follow-up action first.
- If scraper state is failed or blocked, the hero should move into a warning/error treatment with explicit plain-language next-step guidance rather than only showing raw status.
- If supporting systems such as WARP or stream capacity are limiting scraper work, the hero should surface that dependency in the same top-level decision area.

### Typography

- Keep IBM Plex Sans for consistency with project guidance
- Increase contrast between title, meta, and body roles
- Use tighter, larger page titles and more assertive section leads
- Use compact uppercase meta labels for operational signals such as freshness, next run, protection, and readiness

### Color

- Push neutrals toward blue-green tinting so the shell feels intentional
- Keep teal/blue as the base identity
- Use warm accent sparingly for activity, timing, readiness, and attention states
- Avoid purple gradients, glassmorphism, neon dark themes, and decorative gradient text

Dark-theme guardrails:

- Warm accents must stay readable against dark surfaces and should never become glowing neon highlights.
- Surface contrast should preserve the same semantic hierarchy as light mode: canvas, shell, raised section, and alert/status layers must remain visually distinct.
- Shell emphasis in dark mode should still feel operational and polished, not like a generic dark admin template.

### Layout and space

- Reduce repeated equal-weight cards
- Let one focal section dominate each page
- Use stronger spacing rhythm: tighter data groupings, larger breaks between major sections
- Keep top-level pages left-aligned and action-led rather than center-balanced

### Motion

- Use restrained opacity/transform entrances for top-level sections and status bands
- Keep reduced-motion behavior intact by shortening or removing transitions
- No blur-heavy or novelty motion

Freshness, readiness, and queue pressure must never rely on motion alone. Motion can reinforce state changes, but every important operational cue also needs persistent text, icon, label, border, or layout contrast.

## Component and Page Rules

### App shell

- Strengthen the left-nav and top app bar so the shell feels like a persistent operations frame
- Add a subtle canvas treatment and shell accenting that suggests live system activity without adding noise
- Keep navigation readable and compact, but make the active route more decisive

### Page header

- Increase page-title drama through scale and weight contrast
- Support status/meta copy that feels operational rather than descriptive
- Keep primary actions obvious and first in responsive layouts

### Content sections

- Move away from interchangeable outlined cards
- Use stronger surface separation, edge treatment, and internal spacing rhythm
- Preserve shared primitive contracts so improvements propagate consistently

### Dashboard

- Replace the current generic readiness block with a scraper-led hero surface
- Combine readiness, freshness, and next actions into a single dominant composition
- Make recent activity feel like a live feed rather than a default list block
- Use explicit operational labels such as freshness, next run, protection, or attention needed so meaning does not depend on color alone

### Health

- Promote overall system status into a clearer command summary
- Keep totals secondary to actionable readiness
- Reduce the feeling of three equal statistic cards
- Make the primary state answer: is the system ready, what is limiting it, and where should the user go next

### Search

- Make search feel like a guided acquisition workflow, not just form + table
- Emphasize the query/action path and selected-result momentum
- Preserve accessibility and table clarity
- Use plain-language guidance near the primary query and batch-add path so users understand what to do without prior operational knowledge
- Keep progressive disclosure for secondary detail; the main search-and-add path should remain obvious at first glance

### Playlist

- Make the download/share path feel more direct and more productized
- De-emphasize redundant instructions
- Keep advanced filters present but visually subordinate
- Keep the advanced path clearly labeled as optional, with the basic download/share flow remaining obvious even when advanced controls are expanded

## Accessibility and Usability

- Maintain WCAG AA contrast in both themes
- Preserve keyboard access and focus-visible treatments
- Continue using semantic theme tokens rather than hard-coded colors
- Keep loading, warning, error, and success states explicit with text and icon support
- Do not hide critical actions on mobile; adapt layouts instead
- For scraper freshness, readiness, queue pressure, and protected-routing state, always pair color with redundant cues such as labels, icons, border emphasis, or structural placement

## Acceptance Criteria

The redesign is acceptable only if all of the following are true:

- A top-level page has one clearly dominant focal area rather than several equal-weight cards.
- Scraper/readiness state communicates both status and next action in plain language.
- Search and playlist flows feel guided for low-technical users, with advanced options visually secondary.
- Light and dark themes preserve the same hierarchy and avoid generic dark-dashboard styling.
- The app feels more distinctive and operational without introducing decorative effects that weaken usability.

## Implementation Scope

Phase 1 of this redesign should focus on shared theme and shell changes plus the most visibly generic top-level pages:

- `frontend/src/theme.ts`
- `frontend/src/theme.d.ts`
- `frontend/src/components/NavBar.tsx`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/layout/PageHeader.tsx`
- `frontend/src/components/layout/ContentSection.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Health.tsx`
- `frontend/src/pages/Search.tsx`
- `frontend/src/pages/Playlist.tsx`
- related tests under `frontend/src/__tests__`

## Verification Expectations

- Verify light and dark themes
- Verify one phone-width and one desktop-width path
- Verify keyboard access for navigation and primary actions
- Verify touched loading, empty, success, warning, and error states where present
- Record review evidence in `docs/dev/frontend-design-review-evidence.md`
- Use `docs/dev/frontend-design-checklist.md` and `docs/dev/frontend-theme-reference.md` as required review gates during implementation and verification
