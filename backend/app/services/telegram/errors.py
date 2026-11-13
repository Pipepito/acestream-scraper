"""Fixed Telegram diagnostics; codes localize both live and persisted messages.

The English detail remains compatible with existing clients. Unknown library text
must still be sanitized by the manager before crossing the API boundary.
"""
MESSAGE_CODES = {'Telegram is disabled. Configure a Telegram admin token of at least 32 characters and a separate encryption key.': 'TELEGRAM_DISABLED',
 'Enter the Telegram admin token configured on this server.': 'TELEGRAM_ADMIN_TOKEN',
 'Use HTTPS or a localhost connection for Telegram administration.': 'TELEGRAM_HTTPS',
 'Open Telegram settings from this application origin.': 'TELEGRAM_ORIGIN',
 'Telegram request is too large': 'TELEGRAM_TOO_LARGE',
 'Invalid Telegram input. Check the fields and limits.': 'TELEGRAM_INVALID_INPUT',
 'Telegram request timed out; retry shortly.': 'TELEGRAM_TIMEOUT',
 'Telegram is processing a batch. Try again shortly.': 'TELEGRAM_BUSY',
 'Telegram rate limit. Wait until the displayed retry time.': 'TELEGRAM_RATE_LIMIT',
 'Telegram action could not complete. Check connection, chat access and source settings.': 'TELEGRAM_ACTION_FAILED',
 'Enable an existing source before scanning': 'TELEGRAM_ENABLE_SOURCE',
 'Telegram did not confirm revocation': 'TELEGRAM_REVOCATION',
 'Chat access lost': 'TELEGRAM_CHAT_LOST',
 'Chat access lost. Refresh joined chats and select a chat you belong to.': 'TELEGRAM_CHAT_ACCESS',
 'Choose a Telegram user or channel identity': 'TELEGRAM_IDENTITY',
 'Connect your Telegram account first': 'TELEGRAM_CONNECT_FIRST',
 'Log out the existing account before connecting another': 'TELEGRAM_LOGOUT_FIRST',
 'Wait a few seconds before requesting another code': 'TELEGRAM_WAIT_CODE',
 'Reconnect or log out the saved account first': 'TELEGRAM_SAVED_ACCOUNT',
 'Enter the code sent by Telegram.': 'TELEGRAM_ENTER_CODE',
 'Authorization expired. Disconnect and start again.': 'TELEGRAM_LOGIN_EXPIRED',
 'Enter your Telegram two-step verification password.': 'TELEGRAM_ENTER_PASSWORD',
 'Collection is stopped. Reconnect to catch up.': 'TELEGRAM_STOPPED',
 'Account removed. Existing catalogue streams are preserved.': 'TELEGRAM_REMOVED',
 'Source no longer exists': 'TELEGRAM_SOURCE_MISSING',
 'Topic is unavailable. Refresh the topic list.': 'TELEGRAM_TOPIC_MISSING',
 'The Telegram code is incorrect. Enter the latest code.': 'TELEGRAM_CODE_INVALID',
 'The Telegram code expired. Disconnect and request a new code.': 'TELEGRAM_CODE_EXPIRED',
 'The Telegram two-step verification password is incorrect.': 'TELEGRAM_PASSWORD_INVALID',
 'Enter a valid phone number including the country code.': 'TELEGRAM_PHONE_INVALID',
 'Telegram rejected the API ID or hash. Check your registered application.': 'TELEGRAM_API_INVALID',
 'Telegram rate limit. Collection resumes after the displayed retry time.': 'TELEGRAM_COLLECTION_RATE_LIMIT',
 'Telegram authorization expired. Log out and connect again.': 'TELEGRAM_AUTH_EXPIRED',
 'Telegram operation failed. Check connection, access and settings, then retry.': 'TELEGRAM_OPERATION_FAILED',
 'Authorization expired. Start again.': 'TELEGRAM_START_AGAIN',
 'Telegram secret files must be regular, private files (0600)': 'TELEGRAM_PRIVATE_FILE',
 'Configure a separate Telegram key file and absolute session directory': 'TELEGRAM_KEY_PATH',
 'Keep Telegram secrets outside the database and log directories': 'TELEGRAM_SECRET_LOCATION',
 'Mount the Telegram key separately from encrypted sessions': 'TELEGRAM_SEPARATE_KEY',
 'Telegram session directory must be private (0700)': 'TELEGRAM_PRIVATE_DIRECTORY',
 'Cannot read a valid Telegram encryption key. Check the key mount and private file permissions.': 'TELEGRAM_KEY_INVALID',
 'Another process owns the Telegram session': 'TELEGRAM_SESSION_OWNED',
 'Cannot decrypt the saved Telegram account. Restore its original key, or revoke the session in Telegram before resetting private storage.': 'TELEGRAM_DECRYPT_FAILED',
 'At most 25 Telegram sources are supported': 'TELEGRAM_SOURCE_LIMIT',
 'Create a new source to select a different chat': 'TELEGRAM_SOURCE_CHAT',
 'Chat access lost. Rejoin in Telegram, then scan again.': 'TELEGRAM_REJOIN',
 'Extraction failed. Test the source recipe before retrying.': 'TELEGRAM_EXTRACTION_FAILED'}


def message_code(message: str) -> str | None:
    return MESSAGE_CODES.get(message) if message else None


class TelegramActionError(ValueError):
    pass
