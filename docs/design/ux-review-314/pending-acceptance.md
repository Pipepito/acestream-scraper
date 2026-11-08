# Remaining acceptance and external owners

Application snapshot: `e13a42ef`, E2E harness `24fbb4eb`, frontend fixtures
`f09097aa`, 2026-11-08. This is an outstanding-work register,
not a waiver. PR #325 remains draft and issues #314–#324 stay open. Passing local
checks cannot substitute for the evidence below. The per-criterion scope is in
`acceptance.json`; exact automated outcomes and earlier failures are in
`implementation-ledger.md`.

## Private validation compatibility · #317 / #324

Owner: repository maintainer / private infrastructure reviewer.

The read-only infrastructure snapshot is `0955626eee33149e88e83d5f95901bd131b065b5`.
Its fixed Jest configuration cannot parse WOFF2 imports and does not provide the
Fetch APIs used by React Router's data router. The earlier focused reproduction
failed before its tests ran. The final full
reproduction passes all 2,619 backend tests, lint and types, then reports 56 failed /
65 passed frontend suites: eight failed / 231 passed tests execute. Font-load
failures prevent the remaining tests from running; they are not passes or skips.
The observed errors are WOFF2 parsing and missing `Request`. A reviewable
compatibility change needs:

- A fixed font-asset mapping/stub for WOFF2 imports.
- A trusted jsdom environment exposing native Request, Response, Headers,
  AbortController and AbortSignal, matching the public test environment's behavior.
- The infrastructure's normal reviewed tool-bundle/checksum and runner lifecycle.
  Public app configuration must not select trusted host policy.

The pinned runtime wrapper also selects its ARM OCI layout assertion for a
non-native AMD64 image. AMD64 legitimately contains its Linux engine layout.
Separate explicitly emulated runtime probes provide supplemental evidence; they
do not turn the unmodified wrapper's failure into a pass. Review the platform
selection in private infrastructure and rerun its unchanged intended validations.

The same pinned image passes all 750 frontend tests with the public configuration,
plus lint/types, schema/client drift and both builds, without test warnings after
correcting three test fixtures. This is separate evidence, not a private gate pass.

No private policy, Jenkins definition, credential, job or protected branch has
been changed. The implementation request excluded these mutations; a separate
owner decision is pending. Native ARMv7 engine qualification remains experimental
and requires its documented hardware procedure, independently of successful builds.

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
