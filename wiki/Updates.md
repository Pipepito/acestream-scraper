# Version history and updates

Open **System → Changelog** to read the changes included in your installation.
The history is bundled with the app and works without internet access. A “What's
new” notice opens the notes for the installed version; reading or dismissing it
remembers that choice in your browser. Development builds can contain notes for
a version that has not been published yet.

When a newer stable GitHub release is published, the app can show a separate
notice with a link to its release notes. It checks while the app is open, at most
every six hours after a successful check. Each version is announced once per
browser. Offline connections, GitHub outages and rate limits stay quiet; they do
not prevent using the app. Drafts and prereleases do not trigger notices.

Updates are always manual. The app never downloads or installs an update:

- **Docker:** pull the updated image for your chosen flavor/tag and recreate the
  container using the same configuration and persistent volumes. If you pin a
  version tag, select the new version first. Back up persistent data before
  upgrading; see [installation and upgrades](Installation.md).
- **Native installation:** download the latest release and update your local
  installation, dependencies and built frontend using the
  [installation instructions](Installation.md). Back up persistent data first.

A fresh installation can still show its local “What's new” notice. That notice
means those notes belong to the installed build; it does not mean an update is
available. A development build and stable release with the same version number
will not produce a newer-version notice.
