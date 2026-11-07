# Notification webhook settings

Settings → Automation → Notifications stores one optional HTTP(S) webhook URL.
Empty disables notifications. The URL may contain a path, query, port or HTTP
credentials; these can carry the webhook secret. The API returns only its scheme
and host, with `•••` replacing secret-bearing components. Saving that masked
representation back preserves the original URL.

Saving validates URL syntax before writing: a host is required, and any supplied
port must be valid,
and whitespace, control characters, backslashes and fragments are rejected with
HTTP 422. A rejected update leaves the saved value unchanged. Apart from trimming
surrounding whitespace, valid URLs keep their original bytes, including encoded
paths and signed query strings. Saving does not resolve DNS or require a webhook
server to be online.

Delivery still uses the pinned outbound client and its current destination policy,
including metadata-address denial, private-address policy and no redirects.
Successful configuration does not prove delivery; use **Send test**.

Older versions could save malformed URLs and then fail while returning their
masked representation. These settings now read as `•••` with no host or secret.
The UI explains that the saved URL is invalid and disables **Send test**. Replace
the field with a complete valid URL, or clear it and save to disable notifications.
Other settings remain readable throughout recovery; no database editing is needed.

Regression coverage lives in `backend/tests/test_notification_webhook_validation.py`
and `frontend/src/__tests__/NotificationsSection.test.tsx`.
