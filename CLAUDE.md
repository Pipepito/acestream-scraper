## Design Context

For frontend design guidance in this worktree, also use `docs/dev/frontend-design-checklist.md` and `docs/dev/frontend-theme-reference.md` alongside this context.

### Users
This product is for single users with little or no technical knowledge who need guidance while managing an AceStream setup. They use the interface as an operational control panel for channels, EPG data, playlists, scraper tasks, WARP, and system health, and the product should help them move through each workflow without assuming deep technical expertise.

### Brand Personality
The brand should feel bold, powerful, and operational. The voice should be clear, direct, and supportive so users feel fast, confident, and slightly delighted rather than intimidated by a technical tool.

### Aesthetic Direction
The current product already points toward a structured operational dashboard: Material UI, IBM Plex Sans, a left-nav app shell, light-mode defaults, teal and blue as primary accents, and compact cards and sections for dense information. Future design work should support both light and dark themes, keep the product feeling Linear-like in polish and clarity, introduce warmer accents where they add emphasis or friendliness, and avoid looking like a playful consumer app, a generic admin template, or an overly dark hacker interface.

### Design Principles
- Prefer guided, low-friction flows over expert-only controls so non-technical users can complete operational tasks with confidence.
- Keep information dense but well-structured, using clear hierarchy, sectioning, and status signals to make the system feel fast and controllable.
- Make operational state obvious: health, progress, errors, and next actions should be easy to scan and hard to misunderstand.
- Build a polished dual-theme system that starts from the existing teal/blue foundation and uses warmer accents sparingly for emphasis, feedback, and approachability.
- Meet WCAG AA expectations, respect reduced-motion preferences, and use more than color alone to communicate status or meaning.
