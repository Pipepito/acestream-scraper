# PR #325 integration snapshot

9 November 2026. Integration branch: `pepe/pr325-zzstreams-sync`.

- Merge `develop` at `6af09770` into PR head `7771e255`, retaining rolling MARCA
  imports, shared EPG identities, bilingual feedback and unsaved editor guards.
  Keep the PR's v2.3.0 selection and the incoming v2.2.1 changelog entry.
- Include the category/artwork implementation from the preserved category preview.
  Category migration `20261109_1300` follows shared EPG migration `20261109_1200`;
  their revision identifiers are distinct. Regenerate OpenAPI and TypeScript types.
- Include the committed ZZSTREAMS design package from `b7345480`, preserving the
  PR's implementation evidence. The separately published Pages site is unchanged
  by this source integration. Its historical checks remain dated evidence, not
  acceptance of this combined application revision.
- The owner explicitly authorized both workstreams and publication of the tactile
  artwork. Its provenance retains the original model/credit ledger and unresolved
  licensing assessment; publication authorization is not a new licence grant.
- Retain the exact WebKit read-cancellation classification, startup auth fixture,
  and mobile playback checks for advancing video and unchanged session ownership
  while scrolling between player and catalogue.

Focused integration checks passed: 52 backend tests (categories, migration, shared
EPG inventory, event providers and maintenance), 94 frontend tests in eight suites,
frontend lint/typecheck, E2E typecheck, and the production frontend build. Design
artifact checks passed with 4,077 local links, 674 fragments, 876 gallery exports
and no generated drift. These focused checks do not replace full validation.
The built UI also passed 56 focused browser cases across Chromium, Firefox and
WebKit (category discovery, events/MARCA, changelog and startup). Desktop/mobile
category screenshots use isolated mocked catalogue data. The preview was stopped
and port 18861 verified free after these checks. `workspace-doctor` passed.

The exact combined commit must pass `workspace-validate run` before pushing.
Its retained run report owns final application, Docker and browser acceptance;
older cancelled runs and the design-only checks cannot supply that receipt.
