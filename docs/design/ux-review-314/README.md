# TV UX visual review — draft 02

Visual references for [epic #314](https://github.com/Pipepito/acestream-scraper/issues/314), prepared on 7 November 2026 from the UX audit, owner-provided designer guide and subsequently supplied frontend bundle.

These are proposals for refinement. They do not change the application, establish final brand approval, or represent completed implementation tasks. The mockups use synthetic channels, programmes and settings. The illustrated player artwork is a placeholder, not live footage.

## Designer bundle and reuse decision

Read the [coverage and reuse assessment](designer-frontend-assessment.md) for the native screens, missing capabilities, API differences, assets and verification. The supplied frontend is a useful viewing/discovery reference; its code is not a complete application replacement.

Its actual coral/navy styling differs from both the original lime PDF and an unused cyan proposal inside the bundle. Board 12 adapts the implemented palette to our general-TV layout. Final palette and font choices remain a refinement decision in #316.

| Reference | Purpose |
| --- | --- |
| [07 · Designer catalogue](images/07-designer-home-desktop.png) | Supplied desktop interface with synthetic channels. |
| [08 · Designer categories](images/08-designer-categories-desktop.png) | Discovery layout and sports-biased category fallbacks. |
| [09 · Designer sources](images/09-designer-sources-desktop.png) | Reusable add-and-extract flow. |
| [10 · Designer dashboard](images/10-designer-dashboard-desktop.png) | Backend-dependent summary; backend deliberately absent. |
| [11 · Designer phone layout](images/11-designer-home-phone.png) | Actual responsive catalogue at 390 px. |
| [12 · Coral general-TV study](images/12-coral-general-tv-study.png) | Optional adaptation; compare with the lime board 02. |
| [13 · Designer channel dialog](images/13-designer-player-dialog.png) | Player/detail presentation with no media session. |

![Coral/navy general-TV study](images/12-coral-general-tv-study.png)

Boards 07–11 and 13 are the supplied frontend rendered against intercepted synthetic data. They do not demonstrate a connected installation or working playback. Board 12 is our separate proposal.

## Original guide-based proposals

| Board | Purpose | Related tasks |
| --- | --- | --- |
| [01 · Current settings](images/01-current-state.png) | Two unchanged audit captures with annotations about technical controls and settings ownership. | #316, #318, #319 |
| [02 · Proposed Live TV](images/02-live-tv-desktop.png) | Dark desktop viewing layout with player, current programme and persistent channel catalogue. | #316, #319 |
| [03 · Proposed Settings](images/03-settings-desktop.png) | Light desktop settings, purposes/help, advanced disclosure and a consistent save area. | #316, #318 |
| [04 · Proposed TV channels](images/04-channels-desktop.png) | Visible core filters, numbers/favourites, guide links and honest signal states. | #316, #320 |
| [05 · Bilingual phone layouts](images/05-mobile-bilingual.png) | Actual 390 px EN/ES renders; interface labels translate while programme titles and channel names remain original. | #317, #318, #319 |
| [06 · Design foundations](images/06-design-foundations.png) | Guide-derived palette, font roles, spacing, focus targets, semantic states and both themes. | #316 |

![Proposed Live TV desktop layout](images/02-live-tv-desktop.png)

![Proposed settings desktop layout](images/03-settings-desktop.png)

![Proposed channel inventory](images/04-channels-desktop.png)

![English and Spanish phone layouts](images/05-mobile-bilingual.png)

![Proposed design-system foundations](images/06-design-foundations.png)

![Current settings audit evidence](images/01-current-state.png)

## Standalone preview

Open [index.html](index.html) locally in a browser for the review gallery. Open [prototype.html](prototype.html) for the HTML/CSS concept. Keep its adjacent `assets/` directory so the fonts load. No network connection or installation configuration is required. Try the [coral/navy variant](prototype.html?view=live&theme=dark&palette=coral) alongside the default lime direction.

The prototype demonstrates three surfaces: Live TV, Settings and TV channels. EN/ES/theme controls, channel search/favourites and selected feedback are local demonstrations. Other navigation and actions are illustrative; it does not stream, record, authenticate, discover devices or change a server. Detailed behavior remains governed by the issue acceptance criteria, including state preservation during language changes.

The prototype is a disposable design reference outside the canonical frontend. Do not copy it wholesale into application source. Implementation should use the existing React/TypeScript/MUI patterns, typed localization resources and shared components described by the linked tasks.

## Decisions to refine

- Type roles, density and spacing; Inter for UI and limited Barlow Condensed display use are a proposal.
- Navigation labels and phone navigation. Some destinations are represented by grouped entry points, not removed capabilities.
- Canonical setting ownership and contextual links; the Settings mockup is an example section, not a complete field inventory.
- Final palette: original lime guide or implemented coral/navy direction, with semantic status colors kept separate; reconcile the unused cyan proposal.
- Final English/Spanish terminology and copy. Original channel/programme data stays outside UI translation.

The original designer PDF is not republished. The current-state board uses two settings captures selected to avoid private source lists, account details and public server addresses. Mockup channels and programmes are fictional.

## Evidence and limits

Planning/source baseline: `develop` at `7ccf16d383758aeeb78845e20e3716ddf97df10d`. The live audit installation's exact commit was not established.

- All 13 images were rendered and visually inspected. Six are supplied-frontend captures using synthetic data; one is current-app evidence; six are proposals.
- The final prototype passed 96 layout cases: Live TV, Settings and Channels × EN/ES × lime/coral × light/dark × 320/390/768/1440 px. No horizontal document overflow or script exceptions were observed. The initial export also had 30 screen/layout checks.
- Demonstration checks exercised language switching, channel search and local-only save feedback. The initial gallery loaded all six original images and linked to the prototype; the expanded gallery is checked separately below.
- Sample contrast ratios: main light text 15.89:1; secondary light text 5.56:1; dark text on lime 16.28:1; secondary dark text 7.86:1; success text 5.88:1; waiting text 6.28:1. These are sampled pairs, not a complete state audit.
- These checks do not constitute accessibility certification, application regression validation, or completion of any implementation task.

For this design-reference-only branch, the maintainer explicitly selected visual/prototype, documentation and link checks instead of the full application/Docker/E2E matrix. This scope-specific waiver does not apply to subsequent application implementation. The final repository documentation validator, local Markdown/HTML/CSS reference checks, expanded-gallery image/layout checks and whitespace checks passed. See [verification.md](verification.md) for commands, counts and scope.

## Asset provenance

Inter and Barlow Condensed were obtained from the official [Google Fonts repository](https://github.com/google/fonts). Their SIL Open Font License notices are included in [Inter-OFL.txt](assets/Inter-OFL.txt) and [Barlow-OFL.txt](assets/Barlow-OFL.txt); retain them when redistributing the font files.

The UI layouts, simple line icons and vector landscape are code-native review artwork. This branch does not introduce a new application name or brand mark.

The designer reference screenshots contain supplied artwork solely to review the supplied interface. Selected production assets still need the provenance checks described in the assessment; the original archive and media masters stay outside Git.
