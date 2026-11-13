# Remaining acceptance and external owners

## Integration and completion are separate

Maintainer decision, 2026-11-08: PR #325 is an integration step toward v2.3.0.
It may merge into `develop` for real-user testing before the UX epic is fully
accepted. Manual acceptance below is deferred to that feedback cycle, not marked
passed or removed. Further design changes can land through follow-up PRs.
Keep #314–#324 open until their individual remaining criteria are accepted.
Do not use automatic closing references for this integration PR.

Before integration, require passing automated validation for the exact final PR
head and current target, resolved review conversations, and the maintainer's
merge decision. A version or documentation follow-up creates a new head and
needs fresh required CI. Do not reuse an older commit's green status.

After integration, the trusted develop pipeline validates the merged revision
before publishing floating `develop*` images. Those previews can supply the
manual and participant evidence below. Record image digest and source commit,
not just the mutable tag. A merge, selected version or develop image does not
mean stable release, epic completion, accessibility conformance or final design
approval. Versioned v2.3.0 images and `latest` remain a separate manual release
from `main`. This document does not authorize a merge or publication.

## Automated evidence and follow-up

Application implementation snapshot: `e13a42ef`; final E2E harness `24fbb4eb`;
frontend fixtures `f09097aa`. The 2026-11-08 hosted validation of app head
`8ee7da19dd5c7e28c808c197bbad3d277127739f` against develop base
`cf952afc6b4489c02b7a675ff3d634cc13d98e0b` passed the full application gate
(2,619 backend tests, 121 frontend suites / 750 tests, zero failures/skips), all
15 image builds, five AMD64 and five ARM64 runtime checks, and ARMv7 packaging.
All 11 image security comparisons completed with zero new findings. Recheck
GitHub commit statuses for the current head; this is a dated snapshot, not proof
that subsequent changes passed. Prior failed attempts remain in the ledger.

The per-criterion scope remains in `acceptance.json`; automated outcomes and
commands are in `implementation-ledger.md`. Native ARMv7 engine qualification
remains experimental and requires real hardware independently of packaging.
The source-scan classification and existing dependency advisories below are
separate security/dependency follow-ups; neither is a manual UX test result.

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

## Feedback and acceptance record

For each session record the image digest/source commit, OS/device, browser and
assistive technology versions, preset, language, theme, task, expected/observed
behavior, pass/fail, severity and owning issue. Keep personal data, credentials
and private source URLs out of public evidence. Use consenting testers and owned
test installations/receivers; back up persistent data before development upgrades.

Start with viewing/filtering/stopping, recording schedule/edit/cancel (including
DST), source preview/save, guide matching/reorder/export, account permissions,
connection setup and recovery explanations. Check draft and playback continuity
when switching preferences. Fix consequential mistakes and accessibility blockers,
then repeat affected tasks on the new image. Keep design preferences separate
from correctness failures and retain the original observations.

Before declaring the epic complete or v2.3.0 ready for stable release, reconcile
all remaining criteria with observed evidence or an explicit maintainer scope
change. Integration into develop alone closes none of these acceptance items.
