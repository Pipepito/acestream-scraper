# Design specification — review 03

> Review 04 update (7 November 2026): [expanded composed coverage](coverage-review-04.md), [workflow fields/interactions](workflow-specification.md), [current verification](verification-review-04.md) and [task refinements](task-refinements-04.md) supersede historical composition gaps. Prior live defects remain open. No user approval or application implementation is implied.

Status: **proposed / in review**. This supplements the complete [coverage contract](whole-app-coverage.md); it does not approve a rebrand or application changes.

## Comparable directions

| Proposal | Composition | Suitable use | Tradeoff |
| --- | --- | --- | --- |
| A · Calm/practical | Inter hierarchy, quiet warm surfaces, strong dividers, one accent action, restrained imagery. | Default administration: sources, access, guides, recovery. | Less television personality; can look generic if content hierarchy is weak. |
| B · Expressive/TV | Same fields, controls and flows; limited Barlow display title, stronger section rule and accent marker, larger viewing artwork. | Viewing, recordings, possibly setup. | Longer Spanish titles occupy more height; avoid condensed type in fields and error text. |

Both support coral/navy and lime-neutral accents. Compare [A](admin-prototype.html?view=recordings&direction=calm&palette=coral&theme=light) and [B](admin-prototype.html?view=recordings&direction=broadcast&palette=lime&theme=dark). Change just Direction for a controlled typography comparison; change just Accent for a palette comparison. Recommended blend: A for task work, B only for viewing headings/art. This is a recommendation, not approval. No new product name or production logo.

## Foundations and component contract

- Primitive → semantic → component tokens remain the implementation architecture. Use existing MUI theme/layout, PageHeader, StatusLine, ContentSection, ConfirmDialog and RowActionsMenu. Prototype CSS is disposable; no parallel frontend.
- Body 16/24–25; controls/data 14/20–22; secondary 12/18. Metadata 11 px is limited to review chrome, provenance and nonessential overlines. Essential help should be 14 px in final product. Titles 28–36 (A), limited 38–54 display (B); sentence case, no uppercase instructions.
- 4 px spacing unit; field gaps 20–24; sections 24–32; desktop page gutters 32–48; phone 16. Controls 44 px minimum design target; 6–8 px corners. No decorative glow, nested cards, animated background video or chart ornament.
- Semantic roles: canvas, surface, subtle, primary/secondary text, divider/control boundary, accent/action text, selected, success/warning/error, focus. Accent never means online or safe. Status always carries text and, where helpful, an icon. Selected controls need programmatic state.
- Use 3 px visible focus with offset; check actual adjacent colors. Button/field boundary is separate from the decorative divider. Disabled state requires a reason where absence of permission/capability is relevant.
- Existing font assets retain OFL notices. A font migration awaits the decision log; application IBM Plex remains current until then.

## Layout and navigation

1440: 224 px navigation; flexible main with optional 280 px context rail. At 1150 the context rail moves below primary content; at 800 navigation becomes an inline demonstration menu (production drawer must trap/restore focus correctly). At 500 forms/actions stack; records become cards; no core action disappears. Verify 320/390/768/1440 plus zoom, long strings and on-screen keyboard. Review toolbar is not product UI; presentation captures hide it.

Keep current URLs and query context. Preserve all nine compatibility redirects. Proposed labels: Channel sources / Fuentes de canales; Streams / Emisiones; TV channels / Canales de TV; Programme guide / Guía de programación; Connections / Conexiones. Explain a stream as a playable source, not a TV-channel synonym.

Events moves from observed Manage to proposed Watch because its agenda is viewing content; source/provider tools remain contextual. Connections overview is an orientation layer; every current integration URL remains directly reachable. Do not mount all integration queries there. Navigation examples are not a proposal to remove routes missing a mockup.

## Editing and consequences

Preserve the newly merged availability, similar-name review, atomic Add and Link and offline-cleanup contracts in the [current-source delta](current-source-delta.md). Similar stream-to-TV hints are separate from guide matching; offline hiding is separate from deletion. The new shared TVChannelLinkField should be reused in manual/search flows.

Save per coherent server transaction. No global Save across recording, scheduling, guide configuration and notifications unless an explicit API contract supports it. This avoids false atomicity and ambiguous partial success.

Every section displays pristine, dirty, pending, saved, failed and stale states. Pristine/invalid/pending Save is disabled. Cancel restores that section's saved baseline. A failed save retains values. Internal dirty navigation offers Stay or Discard; language/theme changes retain draft values, selection, scroll/focus and media. Page unload uses supported native protection; no promise of draft recovery after a crash.

Immediate exceptions remain explicit: favourite/number edits, service commands, discovery, copy, refresh, Stop watching. Number commits on Enter/blur and blank clears. Commands do not join a settings draft.

| Action | Required review / success wording | Invariant |
| --- | --- | --- |
| Disable recordings | “Stop N active recordings and cancel M schedules? Saved files remain.” / “¿Detener N grabaciones y cancelar M programaciones? Se conservan los archivos.” Show unknown counts honestly and recheck. | Existing disable behavior preserved; persistence required for recording. |
| Stop recording | “Stop recording now? The captured part remains available if finalized successfully.” / “¿Detener ahora? La parte capturada estará disponible si finaliza correctamente.” | Do not promise complete file or use Delete wording. |
| Cancel schedule | “This programme will not be recorded.” / “Este programa no se grabará.” | Other schedules and saved files unchanged. |
| Delete files | Named programme, all saved parts, irreversible. Protected/active/held media rejected. | Original and compatible files follow current deletion contract. No fake undo. |
| Change permissions | Warn that this account is signed out and its API credentials revoked. | No broadening of access; remote control separate from casting. |
| Remove source | Count source-owned streams and assigned subset; retain TV channels; checkbox default remains current on. Explain unchecking retains streams. | No silent destructive-default change. Orphan cleanup separately reviewed. |
| Recovery fresh | Back up DB/migration files, then replace catalogue and reconfigure catalogue settings. Accounts remain separate. | No account reset or fail-open. |
| Recovery readable | Back up first; sources first; damaged rows can be skipped; listings/activity not copied. | Do not imply all data can be recovered. |

Prototype confirmation buttons only demonstrate copy/focus. Product must obtain current impact/capabilities before submission and handle races.

## Nine composed families and state behavior

| Family | Core decision / EN–ES copy | State differences and implementation mapping |
| --- | --- | --- |
| Recordings | “Saved / Upcoming / History” · “Guardadas / Próximas / Historial” | Saved requires ready playable files; partial shows missing intervals. Upcoming includes scheduled/active; History includes deleted/missed/cancelled. Settings shared, compatible copy preserves originals. Recordings/RecordingDialog/RecordingPlayback. |
| Guide matching | “Review matches” · “Revisar coincidencias” | None selected initially. Source-qualified identity visible. Ambiguous row goes to review; unknown does not block watching. Changed preview clears authorization and needs re-review. EPG/useEPGMatching/guideSetupService. |
| Accounts/access | “Accounts and access” · “Cuentas y acceso” | Not-enabled activation, admin/nonadmin, public viewing and IPTV separate. Permission change consequences precede Save. One-time secrets never in screenshots. AccessSettings/AccountSetup/accessService. |
| Source setup | “Add and find channels” / “Save source only” · “Añadir y buscar canales” / “Solo guardar fuente” | Saving succeeds before queue/import. Failed import retains source and channels. Distinct queue/result/verified state. Shared SetupSources/Scraper service flow; type-specific fields need composed variants. |
| Connections | “Where would you like to watch?” · “¿Dónde quieres ver la TV?” | Browser/TV/external player/media server remain different. Missing receiver: same-network help/manual entry; no fabricated browser pairing. Effective address single owner. Existing integration sections/services. |
| System | “What needs attention” · “Qué necesita atención” | Checking outage independent of playback; never checker fallback. Waiting≠Running; exception count≠offline. Partial scan≠zero; free space per filesystem. SystemDashboard/storage/job services. |
| Setup | “Start with channels” · “Empieza por los canales” | Guide optional, engine-free valid. Sources save as added; Finish only onboarding completion. Advanced runtime settings preserve deployment values/precedence. Setup/RuntimeSetup. |
| Recovery | “Retry startup” · “Reintentar inicio” | Network/auth failure not database-empty. Safe retry before salvage/fresh. Masked diagnostics remain available under normal auth even without DB. StartupGate/startupService. |
| Helper | “Sample → Choose fields → Test and copy” · “Muestra → Elegir campos → Probar y copiar” | No installation connection in standalone. Paired records, manual/JSON/regex and heavy-input paths preserved. Shared recipes entrypoints; never fetch active user URLs from mockup. |

The prototype state menu shows only meaningful demonstration states. Loading has no fabricated percentage; empty differs from filtered-empty in implementation; permission errors cannot be solved by Retry. Unsaved and destructive variants are not attached to read-only system views. Each feature still needs unique pending/success/validation/failure details; generic state examples are not complete coverage.

## Localization and accessibility

All app-owned text includes visible/accessible labels, controls, tooltips, errors, confirmations, dates, counts and library UI. Keep channel/programme/source names, user text, URLs, IDs, schema fields and raw logs original. Synthetic Northlight/Coastlines names intentionally remain unchanged in Spanish. Locale and IANA timezone are independent. Never reschedule a job/recording on language change.

Use semantic resource keys and full messages in production, typed through the planned i18n foundation; the prototype's two-string helper is not that architecture. Avoid DOM translation or string matching of English errors. Spanish requires fluent contextual review, plural/zero/unknown tests and ~40% pseudo-localization expansion.

Keep one main landmark, page h1, meaningful h2/h3 hierarchy, labelled fields with help/error association, polite status feedback and assertive error only where needed. Modal initial focus goes to safe action, Escape closes when permitted, focus returns to opener; no auto-submit or automatic destructive retry. Guide row labels include both identities. Desktop table relationships become named phone groups, not missing headers.

Reduced motion removes animation; no auto-playing artwork. Real 200% text scaling and 400% reflow, VoiceOver/NVDA, virtualized-list navigation and real phone testing remain #324 obligations, not satisfied by viewport screenshots.

## Decision log

| Decision | Proposed choice | Approval |
| --- | --- | --- |
| Product identity | Keep AceStream Scraper. | Existing requirement; no rebrand. |
| Administration tone | Calm A; optional expressive B on viewing pages. | Review pending; user requested alternatives. |
| Palette/fonts | Compare coral/lime and Inter/limited Barlow against existing IBM Plex. | Open. |
| Source import intent | Explicit Add and find vs Save only; same shared flow. | Design recommendation; behavior review pending. |
| Canonical editors | Field ledger below; links preserve return context. | Design review pending. |
| Task scope | Existing ten issues; no completion based on mockups. | User requirement. |

[Field ledger](field-ledger.md) · [Coverage](coverage-review-03.md) · [Task refinements](task-refinements.md).
