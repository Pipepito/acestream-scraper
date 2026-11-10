# Collaborator safety

Trusted GitHub collaborators can push application branches without gaining Jenkins
administration, host-build approval or publication permissions. Forks and origin
branches receive the same automatic isolated checks, including the complete
application suite, and the same public result on the pull request.

Pipeline definitions, host cleanup, runner construction and publishing are owned
by the private infrastructure repository. Jenkins uses deployed, pinned definitions;
creating or editing a public Jenkinsfile has no effect. Private visibility alone is
not the boundary: repository write permissions, fixed policy, container isolation,
owner approval and scoped credentials enforce it together.

Only the owner administers Jenkins. Other authenticated local accounts are
read-only and cannot build, configure, cancel or approve. Host work (installing
proposed dependencies, building images) binds the exact PR/head/base/target and
is checked against GitHub before and after running. It is authorized
automatically only for a pull request the owner opened from this repository
while the owner is its sole writer; adding any other writer returns every pull
request to manual owner approval. Another contributor's change is approved by
the owner when it reaches build or dependency inputs, and otherwise gets no host
work before merge.
Publishing credentials are outside the PR-job folder. Read [the CI contract](jenkins-ci.md)
for contributor expectations and the private repository for operational procedures.

Before inviting a collaborator, verify the deployed policy and owner-only ACLs,
GitHub branch restrictions, isolated automatic checks, rejected non-owner/stale
approvals, and credential visibility. Repository files do not activate live rules.
Do not report incomplete or historical image validation as a successful current build.

## Finding approval requests

GitHub's `PR Validation / develop` description distinguishes a wait for the
maintainer from queued checks. In Jenkins, the PR build summary links to its corresponding approved
validation build. Pending approval builds have an `APPROVAL REQUIRED — PR #…` name,
a clickable history badge and a direct approval link in their overview. Approval links stay inside Jenkins; the new approval status points back to
the public PR. Approval remains restricted to the owner and exact revision.
