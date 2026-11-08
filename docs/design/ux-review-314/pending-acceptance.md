# Remaining acceptance and external owners

Application snapshot: `e13a42ef`, E2E harness `24fbb4eb`, frontend fixtures
`f09097aa`, 2026-11-08. This is an outstanding-work register,
not a waiver. PR #325 remains draft and issues #314–#324 stay open. Passing local
checks cannot substitute for the evidence below. The per-criterion scope is in
`acceptance.json`; exact automated outcomes and earlier failures are in
`implementation-ledger.md`.

## Private validation fixed; review/deployment pending · #317 / #324

Owner: repository maintainer / private infrastructure reviewer.

The owner authorized the private compatibility changes after the original delivery.
[Private PR #15](https://github.com/Pipepito/acestream-scraper-infra/pull/15), revision
`a057148d9dd923329a297bd81236935f0982e912`, supplies trusted WOFF2 mapping and
matching native Fetch APIs through individually mounted private helpers. The AMD64
wrapper now executes actual runtime checks under emulation; ARMv7 stays packaging-only.

All 362 infrastructure regressions pass with warnings treated as errors. The fixed
private full gate passes 2,619 backend tests and 121 frontend suites / 750 tests,
with zero failures/skips/test warnings/console errors, plus lint/types, drift,
builds and architecture/publication dry runs. Five AMD64 and five ARM64 runtime
checks and the ARMv7 engine packaging probe pass. All four rendered pipeline
files pass the live Jenkins Declarative validator after explicit owner authorization.
See `private-validation-compatibility.json` for exact revisions and immutable images.

The prior failed-policy evidence remains in the ledger. These new local results do
not claim that deployed Jenkins policy changed: the fix is on a review branch and
has not been merged or installed. Live CI needs the separately authorized reviewed
policy deployment. The owner explicitly requested no merge or deployment yet.
No credentials, jobs, protected branches, publication policy or live definitions
were changed. Native ARMv7 engine qualification remains experimental and needs its
hardware procedure independently of successful packaging checks.

## Manual assistive technology · #315 / #317 / #324

Owner: maintainer-designated accessibility reviewer, including fluent Spanish
listening. Use isolated data and record build, OS, browser/AT version, preset,
language, theme, steps, spoken output, outcome and issue-owned fixes.

Follow the approved [manual protocol](https://github.com/Pipepito/acestream-scraper/blob/de69e644428abe5d0e4149b4e437d37996c4b769/docs/design/ux-review-314/acceptance-protocols.md):
VoiceOver/macOS Safari, NVDA/Windows Firefox or Chrome, iOS VoiceOver and Android
TalkBack. Cover skip/navigation and drawer focus; recording/DST errors; retained
pending/dirty state and media during preferences; guide ambiguity/reorder; named
export range controls; permission/credential/stop/recovery confirmations.

The 63-state axe scan has zero violations after corrections, but 85 incomplete
rule instances remain explicitly triaged. Automated tree/keyboard assertions and
288 token contrast measurements are supporting evidence, not spoken-output passes.

## Native zoom and physical devices · #324

Owner: maintainer-designated device reviewer. Perform actual browser zoom at
200% and 400% from 1280px desktop width, EN/ES and both themes, including native
select/date/time popups, sticky controls, open dialogs and long errors. Use a small
iPhone and Android device in both orientations, real on-screen keyboards, Back
with dirty state, and OS reduced motion. Emulated 320/390px tests do not satisfy
this protocol. Receiver/media actions need separately authorized owned test
receivers and isolated data; never use a live household installation implicitly.

## Fluent Spanish and nontechnical participants · #316 / #317 / #324

Owner: product maintainer / research reviewer. Recruit 5–6 nontechnical online-TV
viewers, including at least two Spanish-dominant participants and an AT/keyboard
user if available, using the approved protocol linked above. Obtain consent and
keep identifying data out of public artifacts. Counterbalance all three presets.

Record unaided completion, consequential mistakes, recovery, hesitation, time and
confidence for viewing/status meaning, DST recording consequences, household
permissions, source/helper boundaries, guide/reorder/export, and system/recovery
meaning. Review exact Spanish wording and spoken feedback, not only resource-key
coverage. The proposed protocol targets require owner review; no participant
results or approval have been invented. Fix observed failures and rerun affected
flows before accepting the corresponding criteria.

## Historical scanner classification · #324

Owner: maintainer / security reviewer. The pinned source scan labels a synthetic
recording-intent UUID in `ServiceContracts.test.ts` as a generic API key, including
its original commit. It is nonsecret test data used only by the loopback listener.
The current test uses an unmistakably synthetic valid UUID; branch history is
preserved. Review the historical false-positive classification through the normal
private process. No inline suppression, private exception or force-push is included.


## Existing build advisories · #317 / #324

Owner: dependency/private-tooling maintainer. Application tests and lint report no
warnings, but image dependency installation still prints the existing npm
deprecations listed in the ledger and 26 audit findings (4 low, 22 moderate).
The affected deprecated package versions were compared with the integration base
and are unchanged. Existing container pip-root and debconf noninteractive notices
also remain visible. No warning suppression, forced dependency upgrade or private
ESLint/Jest policy change was used to hide them. Review upgrades with the pinned
private tooling; local test success is not a claim that these advisories vanished.
