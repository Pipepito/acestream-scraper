"""Encrypted, private account storage outside DB/ordinary backups.

The operator supplies a separate 0600 Fernet key file. Losing it requires
revoking the session in Telegram and connecting again. No automatic replacement.
"""
from app.services.telegram.errors import TelegramActionError

import fcntl
import json
import os
from pathlib import Path
import stat
from cryptography.fernet import Fernet, InvalidToken
from app.config.settings import get_settings


def read_private(path: Path, limit: int) -> bytes:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077 or metadata.st_size > limit:
            raise TelegramActionError('Telegram secret files must be regular, private files (0600)')
        return stream.read(limit + 1)


class Vault:
    def __init__(self) -> None:
        settings = get_settings()
        self.root = Path(settings.TELEGRAM_SESSION_DIR)
        key_path = Path(settings.TELEGRAM_KEY_FILE)
        if not settings.TELEGRAM_KEY_FILE or not key_path.is_absolute() or not self.root.is_absolute():
            raise TelegramActionError('Configure a separate Telegram key file and absolute session directory')
        from app.repositories.startup_recovery import database_path
        # Secret volume must not live under the application DB/config or logs.
        forbidden = [database_path().parent.resolve(), Path(os.environ.get('LOG_DIR', '/app/logs')).resolve()]
        if any(self.root.resolve().is_relative_to(p) or key_path.resolve().is_relative_to(p) for p in forbidden):
            raise TelegramActionError('Keep Telegram secrets outside the database and log directories')
        if key_path.resolve().is_relative_to(self.root.resolve()):
            raise TelegramActionError('Mount the Telegram key separately from encrypted sessions')
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.root.is_symlink() or self.root.stat().st_mode & 0o077:
            raise TelegramActionError('Telegram session directory must be private (0700)')
        try:
            self.cipher = Fernet(read_private(key_path, 128).strip())
        except TelegramActionError:
            raise
        except (OSError, ValueError):
            raise TelegramActionError('Cannot read a valid Telegram encryption key. Check the key mount and private file permissions.') from None
        self.path = self.root / 'account.enc'
        self.lock = None

    def acquire(self) -> None:
        fd = os.open(self.root / 'consumer.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            os.close(fd)
            raise TelegramActionError('Another process owns the Telegram session') from None
        self.lock = fd

    def close(self) -> None:
        if self.lock is not None:
            os.close(self.lock)
            self.lock = None

    def load(self) -> dict | None:
        if not self.path.exists():
            return None
        try:
            return json.loads(self.cipher.decrypt(read_private(self.path, 16384)))
        except (InvalidToken, OSError, ValueError):
            raise TelegramActionError('Cannot decrypt the saved Telegram account. Restore its original key, or revoke the session in Telegram before resetting private storage.') from None

    def save(self, data: dict) -> None:
        encrypted = self.cipher.encrypt(json.dumps(data).encode())
        temporary = self.root / 'account.tmp'
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encrypted)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)
        fd = os.open(self.root, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def remove(self) -> None:
        self.path.unlink(missing_ok=True)
