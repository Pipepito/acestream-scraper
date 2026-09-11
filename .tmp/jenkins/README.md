# Jenkins job config snapshots

The `*-config.xml` files in this directory are **read-only snapshots** of the live job
configuration on the Jenkins controller (`http://192.168.1.210:8080/`, folder
`Acestream-Scraper`). They are kept for reference and diffing only; Jenkins does not read
them, and editing them here changes nothing on the controller.

| File | Live source |
| --- | --- |
| `acestream-scraper-pr-config.xml` | `http://192.168.1.210:8080/job/Acestream-Scraper/job/acestream-scraper-pr/config.xml` |
| `acestream-scraper-release-config.xml` | `http://192.168.1.210:8080/job/Acestream-Scraper/job/acestream-scraper-release/config.xml` |

Last re-synced: 2026-08-28 (verbatim `GET .../config.xml`).

To refresh a snapshot (Jenkins user + API token live in the untracked `infra-details.md`; never commit them):

```bash
TOKEN=$(sed -n 's/^TOKEN=//p' infra-details.md)
for j in acestream-scraper-pr acestream-scraper-release; do
  curl -sS -u "pipepito:$TOKEN" -o ".tmp/jenkins/$j-config.xml" \
    "http://192.168.1.210:8080/job/Acestream-Scraper/job/$j/config.xml"
done
```

Snapshots contain only credential *ids* (for example `github-builder-app`), never secret values.
