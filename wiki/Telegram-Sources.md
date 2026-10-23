# Telegram sources

Integrations → Telegram sources reads selected groups/channels through **your own
Telegram account**. It uses MTProto, not a bot. The account must already belong to
each selected chat. The app never joins chats, sends messages or downloads media.

A user session nevertheless has the account's broader Telegram permissions. Treat
its encrypted file and encryption key as account credentials. Use an account you
control; revoke this application's session when it is no longer needed.

## Prepare private storage

Telegram is off until the operator configures:

| Setting | Purpose |
| --- | --- |
| `TELEGRAM_ADMIN_TOKEN` | Separate unpredictable admin credential, at least 32 characters. Required for **all** Telegram APIs, even if `API_TOKEN` is unset. |
| `TELEGRAM_SESSION_DIR` | Private persistent directory, default `/var/lib/acestream-telegram`. Contains only encrypted account data and the consumer lock. |
| `TELEGRAM_KEY_FILE` | Absolute path to a separate private Fernet key file. No default. |

Generate a key using the application's Python environment, without printing it:

```python
from pathlib import Path
from cryptography.fernet import Fernet
import secrets
import os

os.umask(0o077)
# Run in a private directory outside the app's config/database/log directories.
Path('telegram.key').write_bytes(Fernet.generate_key())
Path('telegram.key').chmod(0o600)
Path('telegram-admin.env').write_text('TELEGRAM_ADMIN_TOKEN=' + secrets.token_urlsafe(48) + '\n')
Path('telegram-admin.env').chmod(0o600)
```

For Docker, provide the admin env file with `--env-file`, mount the key read-only
at `/run/secrets/telegram.key`, set `TELEGRAM_KEY_FILE=/run/secrets/telegram.key`,
and mount a separate writable directory at `/var/lib/acestream-telegram`.
The session directory must be mode `0700`; the key and encrypted file must be
`0600`, owned/readable by the application user. Mount the key outside the session
volume. Every image flavor supports this integration; no extra listening port,
engine or sidecar is required. Outbound Telegram connectivity is required.
The image dependency stage includes `libffi-dev` for CFFI builds on ARMv7; no
compiler toolchain is added to the final image.

Do not put either secret under the scraper database/config directory, logs,
source exports, or ordinary backups. The app rejects session/key paths within
its database or log directory. Database backups contain source configuration and
message IDs, **not** the authorization session or API hash. If you deliberately
back up account access, keep the encrypted volume and key in separately protected
stores. Never include either in bug reports. Whole-host backups must explicitly
exclude these locations unless you intend to back up account credentials.

The key is operator-managed and never returned by an API. Rotation is deliberate:
revoke/remove the connection, stop the app, replace the key, restart, then connect
again. A missing/corrupt/wrong key is not silently replaced. If the key is lost,
terminate this app's session in Telegram → Settings → Devices before deleting the
unreadable `account.enc` and reconnecting with a new key.

## Connect

1. Register an application at [my.telegram.org](https://my.telegram.org) to obtain
   an `api_id` and `api_hash`. An application key alone does not authorize messages.
2. Open Integrations through HTTPS, or through localhost (an SSH local tunnel is
   suitable). Plain HTTP over the LAN is rejected for Telegram controls. Behind
   HTTPS proxies, set `FORWARDED_ALLOW_IPS` to the actual proxy addresses and have
   the proxy overwrite forwarded headers; never trust arbitrary internet peers.
3. Unlock Telegram settings with the separate admin token. If ordinary `API_TOKEN`
   protection is enabled, its normal login is required too. The Telegram token is
   held only in this page's memory, never in browser storage or URLs.
4. Enter your API ID/hash and phone number with country code. Enter the code
   Telegram sends, then your two-step verification password when prompted.
   Authorization expires after five minutes. Codes/passwords are not saved.
5. Add sources from joined chats. Refresh the chooser after membership changes.
   The chooser currently lists up to 500 joined dialogs and 100 forum topics.

Phone/code login is supported; QR login is not required. One account may have up
to 25 sources. Locking/leaving the settings page clears its credentials but keeps
collection running. **Disconnect** stops collection until Reconnect or app restart;
it keeps the encrypted session. **Revoke session and remove account** asks Telegram
to log out, then removes sources and observations. If Telegram cannot confirm
revocation, encrypted data is retained so you can retry. An already-revoked session
can be removed. Catalogue streams remain available.

## Select and preview

The same processing path is used for live updates, edits, history and previews:

1. Selected chat and optional topic.
2. Sender allowlist (empty means all senders).
3. Include/exclude keyword or bounded regex filters.
4. Automatic extraction or the shared extraction recipe.
5. ID validation, deduplication and additive import.

Resolve usernames to stable user/channel IDs, or enter known IDs. Recognizable
labels are display aids; `7raul:` in a message and broadcast signatures are not
identities. Anonymous admins can post as the group/channel. A human-only allowlist
will not match those posts. Forwarded posts use the posting account by default;
original-author mode uses Telegram's origin identity when available. Hidden origin
names do not bypass an allowlist.

Automatic extraction recognizes adjacent name/ID lines in mixed prose, preserving
flags, and explicit `acestream://` links in text, captions and link entities.
Bare IDs are optional. Distinct IDs with the same name remain distinct streams.
Hashes embedded in unrelated HTTP URLs are ignored. Ordinary chatter is a no-match,
not a failed source. For other layouts, open **Edit extraction recipe**, starting
from the Telegram pair preset, and use the existing repeating-record/name/ID builder.
User regex runs in the shared bounded disposable process, never on the event loop.

**Test against recent messages** evaluates up to ten recent messages without
catalogue writes and shows message/sender IDs, matched pairs, filter/no-match
outcomes, invalid records and duplicates (including IDs already in the catalogue).
The API allows up to 30 preview messages. The builder also accepts a pasted sample.

Playlist URL discovery is not enabled: links in promotions are not fetched.
The optional W3U/M3U discovery workflow remains dependent on the shared reviewed
playlist importer in issue #257. Sports-event interpretation (#55) and films/series
metadata (#99) are separate features; titles/posters never become playable streams.

## Progress, edits and recovery

New sources default to **new messages only**, recording the current latest message
as their starting boundary. Opt in to up to 1,000 recent messages and optionally
exclude messages older than a selected date. Pause preserves progress; Resume
catches up from that progress. Downtime catch-up is incremental, ten forward
messages per source per pass; a large backlog stays queued and is never skipped
just because it exceeds one batch.

New/edited event hints enter a queue capped at 512. History polling recovers missed
new-message hints from the durable cursor. Restart, manual scan, queue saturation,
and periodic reconciliation compare retained messages for edits/deletions in
batches of ten. Sources share a serial consumer; repeated scan requests coalesce.
This bounded Telegram queue does not occupy the global maintenance FIFO. Telegram
flood waits have a visible retry time; network failures use capped exponential
backoff. Membership loss pauses that source's processing until access is restored.
A configured inaccessible chat never falls back to another chat.

A message's observation, stream inserts and forward cursor commit together.
Replay is idempotent. Only the latest revision, extracted IDs and timestamp are
retained for at most **1,000 messages per source and 30 days**; message bodies are
not persisted. Edits/deletions outside that retained window are not reconciled.
Changing filters/recipes re-evaluates retained observations, not an unlimited chat
history. Removed matches/deleted messages clear their observation but do not delete
streams, including streams referenced elsewhere or retained manually. Existing
names, favorites, TV assignments, disabled flags and verified signal status are
preserved. Imports do not initiate engine checks; normal checking remains in charge.

A filesystem lease prevents two processes from using one encrypted session. Keep
one application worker as required by the existing database lock. On restore, use
the matching database and encrypted session/key; a different account's sources
are never automatically attached to the new connection.

## Database upgrades

Telegram revision `20261023_1500` follows the combined catalogue/events revision
`20261023_1400`. Normal startup upgrades existing installations; Telegram rollback
to that predecessor removes only Telegram tables and preserves channels,
catalogues and events. Imported streams remain in the catalogue.

The unmerged Telegram prototype used `20261022_1200`, which belongs to W3U
catalogues in develop. Databases created with that prototype are not normal
upgrade inputs: do not reuse its ambiguous stamp or blindly restamp it. Use a
fresh test database, or restore the pre-prototype backup before upgrading.

## Validation

Automated tests use fake transports and synthetic messages. They cover the six
representative pairs, CRLF/emoji, bounded regex, identity filters, replay,
pause/resume, edits/deletions, migration upgrade/downgrade, encryption permissions,
lease exclusion, authorization, queue saturation and flood waits. No real account
is connected by CI. Real-account validation is opt-in: connect a dedicated test
account, verify new/edit/delete behavior in a joined test chat, restart the app,
then revoke it and confirm its session disappears in Telegram → Settings → Devices.
Record that manual result separately; automated tests are not proof of a live login.

References: [Telegram app registration](https://core.telegram.org/api/obtaining_api_id),
[authorization](https://core.telegram.org/api/auth),
[Telethon sessions](https://docs.telethon.dev/en/stable/concepts/sessions.html).
