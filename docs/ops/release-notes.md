# Release notes and update notices

## Write once

`frontend/changelog/vX.Y.Z.md` is the canonical user-facing release history.
Keep the selected newest version equal to root `version.txt`. Edit its summary,
Added/Improved/Fixed sections and upgrade instructions during feature work;
review it in develop → main. PR descriptions and readiness documents link here.

The supported Markdown subset is a version H1, a one-line summary paragraph,
H2 section titles and one-line bullets. Explicit HTTPS GitHub links are supported
for PRs, issues and contributors, for example `[PR #270](https://github.com/Pipepito/acestream-scraper/pull/270)`.
Other inline formatting, HTML, nested lists and non-GitHub links are rejected.
The offline view renders the same supported links without interpreting HTML.
Keep technical links and detailed procedures in the wiki. Historical entries
are curated summaries; this does not rewrite previously published GitHub releases.

Credit community implementation work by verified GitHub handle and PR number.
Keep a concise Thanks section that distinguishes implementation contributions
from ideas, reports and reproductions; avoid repeating the same contributor
across multiple bullets.
Check authorship and merged commits against the release branch; distinguish
contributed code from suggestions, and describe partial fixes without implying
that their umbrella issue is complete. Use explicit HTTPS GitHub links for handles and issue/PR references so attribution
is clickable in both the offline view and GitHub publication.

Run `cd frontend && npm run changelog`, then commit both the Markdown and generated
`frontend/src/data/changelog.ts`. `prebuild` and `prestart` reject drift. The main
Docker build also checks `version.txt`; the standalone frontend context checks
its generated snapshot. The built SPA contains the full history and makes no
network request to display it. No new Markdown runtime dependency is needed.

## Manual release, automatic notes publication

The existing release job still requires explicit operator confirmation on main:

1. Phase 1 runs the full application gate, validates the notes and builds the
   versioned images. Each versioned OCI index records the source commit, version
   and SHA-256 of its canonical Markdown. Jenkins archives the notes and their
   provenance in `.ci-release-artifacts/release-notes.{md,json}`.
2. Operators validate the versioned images on the canary as before.
3. A separate confirmed run with `PUBLISH_LATEST=true` resolves the version tag
   to an immutable index digest, retrieves the notes from its recorded Git commit,
   checks the version/hash and main ancestry, and promotes that digest without
   rebuilding. Missing provenance, unavailable commits or mismatches fail closed.
   Later commits on main cannot replace the built release's notes.
4. After platform verification and an exact latest digest check, Jenkins records
   successful promotion metadata, then uses `github-publish` to create the Git tag
   and GitHub release. The body is byte-for-byte canonical Markdown. Wiki
   publication follows. Develop and phase 1 never publish GitHub releases.

Dry runs never create tags, releases or images. Phase-1 dry runs retain the notes
preview alongside the preflight summary; promotion dry runs only print the plan
and perform no registry/GitHub calls. The shared FIFO lock remains unchanged.
Existing version images created before this contract cannot be promoted by it;
use a new version built with provenance instead of fabricating annotations.

The existing `github-publish` credential needs repository Contents write access
and permission to create `v*` tags under the live ruleset. No credential or Jenkins
configuration is changed by this implementation. Version tags/releases are never
force-updated. An existing tag is peeled and must point to the exact image commit;
an existing published release must have identical notes and stable status.

## Retry GitHub publication

If GitHub publication fails, images have already been promoted. Correct the
credential/network/ruleset issue and retry only:

```bash
python3 scripts/ci/publish_github_release.py --metadata phase5-build-result-release-metadata.json
```

Run from the trusted release checkout with the `github-publish` token provided as
`GITHUB_PUBLISH_TOKEN` through the existing secure credential mechanism. Keep the
archived promotion JSON and Git history available. The helper rechecks latest's
digest and the committed notes hash. It safely resumes after tag creation or an
ambiguous release-creation response; matching publication is a no-op. A different
tag/release or newer latest blocks the retry. Do not rebuild or enable forced
version overwrite just to retry notes publication. Editing published notes on
GitHub would diverge from existing offline images; correct future notes in Git.

## Published update notification

The app requests authenticated `GET /api/v1/system/updates` after normal startup.
The backend contacts only the public repository's fixed GitHub latest-release
endpoint, without app credentials, redirects or environment proxies. Requests
run off the event loop, are bounded in size/time and shared through a nonblocking
process cache (six hours after success, fifteen minutes after failure). No
background startup dependency or database migration is introduced.

Only a strictly newer numeric stable version is announced; drafts, prereleases,
malformed responses, timeouts and rate limits remain quiet. Browser polling is
six-hourly while the app is open. GitHub must be reachable to discover new releases;
the installed changelog remains available offline. Container marker files select
Docker instructions; other installations get native instructions.

A notice records the announced version per browser as soon as it is shown, so
reloads do not repeatedly announce it. Denied storage falls back to memory for
that tab session. Docker users pull their chosen updated image and recreate the
container with existing configuration/volumes. Native users download and update
the installation themselves. No update is installed and no container is restarted
by this feature. A development build with the selected version equal to the
published version does not receive an update notice.
