# Frontend language and presentation

The application has one English/Spanish catalogue and one set of controllers.
Presentation (`lime`, `coral`, `cyan`), light/dark mode and language are independent
browser preferences. Cyan is the unknown/first-visit presentation. A saved language
wins; otherwise Spanish browser languages select Spanish, with English as fallback.
Storage failures leave the current session usable and offer retry in the selector.
No preference changes a React key, router, query client or media owner.

`src/i18n/resources.ts` owns navigation/core messages. `src/i18n/messages/ui-en.json`
and `ui-es.json` own feature copy; `en.ts` and `es.ts` expose their typed keys.
These pure data files do not need executable-code coverage instrumentation. English source text is the typed key; keys may contain
punctuation because namespace/key separators are disabled. Spanish must provide
every key. `useUiText` subscribes components to language changes. `uiText` reads the
current language for formatters and event handlers. Do not translate user names,
channel titles, programme descriptions, source names, URLs, IDs or entered values.
Application-owned labels and legacy protocol diagnostics can use `translateKnown`;
unknown values remain verbatim. New API error handling must select translated copy
by stable codes, never by comparing an English error sentence.

Use complete sentences with named interpolation values, and i18next `_one` /
`_other` resources for counts. Do not add English plural suffixes in components.
`getLocale` selects display formatting independently of schedule timezone. Machine
ISO dates, timezone/DST conversion and stored numeric values must stay unchanged.
Core/access/recovery resources are bundled so an unavailable translation request
cannot prevent access or recovery. Missing keys fall back to English.

The standalone extraction helper initializes its own language preference and uses
`recipes/messages.generated.ts`. It imports neither the application bootstrap nor
the complete application catalogue. Regenerate this subset with
`npm run recipes:messages`; `prebuild:recipes` checks drift. Recipe worker results
retain their protocol messages and original extracted content; localization happens
at the result/error presentation boundary. Never add application API calls to the
standalone helper.

`Localization.test.tsx` checks resource coverage/interpolation, standalone parity,
plural selection, chosen-language formatting and unchanged original names.
`i18n/pseudo.ts` provides test-only expansion without modifying interpolation
values. Native assistive-technology and fluent Spanish participant evidence is
tracked separately in the epic implementation ledger; automated checks do not
substitute for those reviews.

Migration is ongoing under #317: runtime field labels, status/reason enumerations,
remaining composed feedback and complete sentence/plural consolidation must be
reconciled before language acceptance. The existence of a translated resource does
not prove that every rendered state uses it.

Account and Cast HTTP failures preserve their legacy `detail` body and status and
add optional `X-Error-Code` metadata. Clients translate that stable code, never
match English server wording. The OpenAPI response headers document its format.
Remote-player probes carry an optional `reason` enum for password, pairing, wrong
player and unreachable outcomes. The canonical editor retains the raw result and
renders guidance in the current language; original protocol diagnostics remain
under Technical details. None of these presentation fields grants permission or
alters account transport, receiver ownership or network admission.

For feedback that stays visible, retain data or a message factory instead of a
translated string. `confirm(() => ({ ... }))` resolves its descriptor on each
language render without reopening the modal or settling its promise. `useSnackbar`
accepts a string or `() => string`; factories preserve the notification lifetime
and retranslate its content. `useUiText` subscribes to changes and returns a
language-independent translator so asynchronous callbacks do not retain the old
language. Catalogue names and raw protocol diagnostics remain verbatim.

Event validation uses stable `EVENT_*`/Pydantic reason types with bounded field
locations. Translate these types, never private request input or English sentences.
The event API omits validation input/context, and the maintained schema documents
this redacted response. Corrections retain their reviewed revision across refetches;
a later server revision must produce a conflict rather than silently replace a draft.

Page-scoped `notify` callbacks accept a string or a message factory. Retained
feedback resolves the factory during render so changing language updates the same
notice. Keep raw probe/error results in editor state and derive translated copy
at render time. Do not capture an already translated verdict in a factory.
Scheduled-job summaries use the typed `jobs` namespace with count-aware complete
messages and locale-aware numbers; protocol metrics remain unchanged.

Telegram diagnostics carry additive `message_code` fields and `X-Error-Code`
headers. Fixed legacy details remain available to existing clients; the current
UI translates codes and protocol states while preserving chat/source names.
The backend resolves codes for persisted diagnostic text without a data migration.
Source writes project only writable configuration fields, so response diagnostics
never leak into the strict Telegram input schema.
