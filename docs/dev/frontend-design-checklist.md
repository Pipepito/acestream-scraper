# Frontend Design Checklist

Use this checklist as yes/no gates before building UI and before merging UI changes.

## Before Building

- [ ] Yes/No: User guidance is clear for low-technical users, with the next action labeled plainly and risky controls explained or de-emphasized.
- [ ] Yes/No: Hierarchy and scanability make the primary status, action, and decision obvious within a few seconds.
- [ ] Yes/No: State clarity is planned for loading, empty, success, warning, and error states with text or icon support beyond color alone.
- [ ] Yes/No: Component consistency reuses existing shared patterns before introducing page-local styling.
- [ ] Yes/No: Responsive behavior is planned for at least one mobile width and one desktop width without hiding core actions.
- [ ] Yes/No: Accessibility expectations cover WCAG AA contrast, keyboard access, and practical screen-reader support.
- [ ] Yes/No: Motion and feedback stay purposeful, restrained, and usable with reduced motion.
- [ ] Yes/No: Theme integrity is preserved by planning for both light and dark themes and preferring semantic theme values.

Preferred patterns to use unless the workflow has a strong reason not to:

- page header
- content section
- status treatment
- form section and form actions
- table or dense list container
- empty, loading, and error states

## Before Merging

- [ ] Yes/No: User guidance still helps low-technical users complete the primary flow without relying on assumed operational knowledge.
- [ ] Yes/No: Hierarchy and scanability still hold up under real data, dense sections, and the primary action path.
- [ ] Yes/No: State clarity makes health, progress, success, warning, empty, and error outcomes easy to understand and act on.
- [ ] Yes/No: Component consistency matches shared layout, section, status, and action patterns used elsewhere in the product.
- [ ] Yes/No: Responsive behavior remains understandable and actionable at mobile and desktop widths with no awkward overflow.
- [ ] Yes/No: Accessibility checks confirm contrast, keyboard navigation, focus visibility, and non-color status cues.
- [ ] Yes/No: Motion and feedback remain explicit for loading and save states and still work well with reduced motion enabled.
- [ ] Yes/No: Theme integrity is intact in both light and dark themes without new hardcoded page-local styling.

## Minimum Review Matrix

- [ ] Verify light theme and dark theme rendering for the touched UI.
- [ ] Verify one mobile width and one desktop width.
- [ ] Verify one keyboard path for the primary action flow.
- [ ] Verify loading, empty, error, and success-feedback states where present.
