# Tactile artwork — integration preview and publication authorization

8 November 2026, based on PR #325 head `7771e2556399de77b0db61ae3f34618b1ce9d2a0`.
The owner authorized publication in PR #325 on 9 November 2026, explicitly lifting
the earlier private-publication hold. Generated-asset redistribution terms remain
unverified; preserve the manifest and RIGHTS.md without inferring a new licence.

## Integration

- One local, responsive `CategoryArtwork` component supplies the shared library
  across all three presets and both themes. Labels stay outside the image. If a
  category asset fails, use the neutral asset once, then a solid surface/message.
- Real programme artwork retains priority. In Watch/Live TV cards, its fallback
  explicitly describes **channel** decoration selected only from the saved channel
  category. Unknown channel categories use neutral, never name-based guesses.
  Lime retains text-only channel rows. Coral uses a 200px side thumbnail from
  the small breakpoint upward, rather than stretching decoration across a wide
  single-column row; phones stack artwork above details.
- Expanded programme details in the existing schedule use the actual programme
  category and real image URL already returned by that query. Hidden details do
  not mount artwork. No new guide requests or batched API contract changes.
- Event sport decoration retains existing football/tennis resources and extends
  motorsport/general sport using source sport metadata. Compact 3:1 slots use
  contain, preserving tall objects.

The 405-entry programme lookup comes from the separately inspected richer guide,
not installed server categories. Compound labels remain intact. Placeholder values
are ignored when a useful category is present; conflicting specific sports choose
general sport, and other unresolved conflicts choose neutral. Channel and event
lookups remain separate from programme metadata.

The installed guide snapshot lacked categories/artwork, and most inspected channel
categories were empty. Neutral decoration is therefore expected in this preview.
No metadata import or source switch accompanies the visual integration.

## Review validation

The owner explicitly authorized focused frontend tests, typecheck/lint, a build
and browser checks for this private app-preview iteration. Full application,
Docker/architecture and live playback validation remains pending. Preview config,
backend coordinates, logs and captures stay outside the repository.

The running instance predates the PR's `/tv-channels/browse` and `/inventory`
endpoints. The private Vite config supplies a temporary, read-only adapter for
those two routes using complete bounded reads of the existing catalogue. Other
API operations use the existing instance. This adapter is local tooling, not a
backend compatibility promise or a change to the PR's service layer. It is not
needed when this frontend runs with its matching PR backend.

Final focused checks for this worktree: four Jest suites / 37 tests passed;
TypeScript, ESLint with zero allowed warnings, and the app/helper builds passed.
The built-app read-only visual matrix passed 18/18 cases across three presets,
both themes, 390/768/1440px and EN/ES, with no observed page/console/API errors or
write requests. Separate checks verified the VPN/HMR connection, expanded guide
artwork, 42 image hashes, and ten local catalogue-adapter cases. Captures and
logs are private; no live playback or server edits were exercised.

Dependency installation retained the branch lockfile. npm reported existing
deprecated development/transitive packages and unapproved optional install scripts;
those notices were retained. Initial local Vite config-loader/deprecated-HMR
warnings were resolved using native config loading and the current `server.ws`
options. Final app checks and the final dev-server startup emitted no warnings.

This is a visual review integration, not publication or release readiness.
