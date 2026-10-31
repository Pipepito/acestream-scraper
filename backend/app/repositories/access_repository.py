"""Private, independently migrated SQLite authority. Never part of source exports."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
from uuid import uuid4

from app.config.settings import get_settings
from app.schemas.access import AccessPolicy
from runtime_config import config_path

_INITIALIZE = threading.RLock()


def digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AccessRepository:
    def __init__(self, path: Path | None = None):
        self.path = path or config_path(get_settings().DATABASE_URL).with_name('access.db')
        self.marker = self.path.with_suffix('.required')

    def initialize(self, *, fresh: bool = False):
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import create_engine
        with _INITIALIZE:
            if self.marker.exists() and not self.path.exists():
                raise RuntimeError('Authentication storage is missing; restore access.db or use local recovery')
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
            if self.path.is_symlink() or not self.path.is_file():
                raise RuntimeError('Invalid authentication storage')
            os.chmod(self.path, 0o600)
            engine = create_engine('sqlite:///' + str(self.path))
            try:
                cfg = Config()
                cfg.set_main_option('script_location', str(Path(__file__).resolve().parents[2] / 'auth_migrations'))
                # parents[2] is app's parent (backend).
                with engine.connect() as connection:
                    cfg.attributes['connection'] = connection
                    command.upgrade(cfg, 'head')
            finally:
                engine.dispose()
            with self.transaction() as db:
                db.execute('INSERT OR IGNORE INTO access_state VALUES (1, ?, ?)',
                           ('pending' if fresh else 'open', AccessPolicy().model_dump_json()))

    @contextmanager
    def transaction(self):
        if not self.path.is_file() or self.path.is_symlink():
            raise RuntimeError('Authentication storage is unavailable')
        db = sqlite3.connect(f'file:{self.path}?mode=rw', uri=True, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def state(self):
        if not self.path.exists() and not self.marker.exists():
            return 'open', AccessPolicy()
        with self.transaction() as db:
            row = db.execute('SELECT mode, policy FROM access_state WHERE id=1').fetchone()
            if not row or row['mode'] not in ('open', 'pending', 'accounts'):
                raise RuntimeError('Invalid authentication policy')
            if self.marker.exists() and row['mode'] != 'accounts':
                raise RuntimeError('Authentication policy does not match protection marker')
            return row['mode'], AccessPolicy.model_validate_json(row['policy'])

    @staticmethod
    def user_view(row):
        return dict(id=row['id'], username=row['username'], administrator=bool(row['administrator']),
                    enabled=bool(row['enabled']), permissions=json.loads(row['permissions']))

    def user(self, *, username=None, user_id=None):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM users WHERE ' + ('username=?' if username is not None else 'id=?'),
                             (username.casefold() if username is not None else user_id,)).fetchone()
            return dict(row) if row else None

    def users(self):
        with self.transaction() as db:
            return [self.user_view(r) for r in db.execute('SELECT * FROM users ORDER BY username')]

    def bootstrap(self, username, password_hash, enabled):
        with self.transaction() as db:
            row = db.execute('SELECT mode FROM access_state WHERE id=1').fetchone()
            if row['mode'] == 'accounts' or db.execute('SELECT 1 FROM users LIMIT 1').fetchone():
                raise ValueError('User management has already been configured')
            if not enabled:
                db.execute("UPDATE access_state SET mode='open' WHERE id=1")
                return None
            user_id = uuid4().hex
            db.execute('INSERT INTO users VALUES (?, ?, ?, 1, 1, ?)', (user_id, username.casefold(), password_hash, '[]'))
            # Marker precedes commit: an interrupted activation fails closed.
            fd = os.open(self.marker, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
            os.write(fd, b'User management requires access.db\n')
            os.fsync(fd)
            os.close(fd)
            db.execute("UPDATE access_state SET mode='accounts' WHERE id=1")
            return user_id

    def create_user(self, username, password_hash, administrator, permissions):
        user_id = uuid4().hex
        with self.transaction() as db:
            if db.execute('SELECT count(*) FROM users').fetchone()[0] >= 100:
                raise ValueError('Account limit reached')
            try:
                db.execute('INSERT INTO users VALUES (?, ?, ?, ?, 1, ?)',
                           (user_id, username.casefold(), password_hash, administrator, json.dumps(permissions)))
            except sqlite3.IntegrityError:
                raise ValueError('That username is unavailable') from None
        return self.user_view(self.user(user_id=user_id))

    def update_user(self, user_id, update):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
            if not row:
                raise LookupError('Account not found')
            if row['administrator'] and row['enabled'] and not (update.administrator and update.enabled):
                if db.execute('SELECT count(*) FROM users WHERE administrator=1 AND enabled=1').fetchone()[0] <= 1:
                    raise ValueError('Keep at least one enabled administrator')
            db.execute('UPDATE users SET administrator=?, enabled=?, permissions=? WHERE id=?',
                       (update.administrator, update.enabled, json.dumps(update.permissions), user_id))
            self._revoke(db, user_id)
        return self.user_view(self.user(user_id=user_id))

    @staticmethod
    def _revoke(db, user_id):
        db.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))
        db.execute('DELETE FROM credentials WHERE user_id=?', (user_id,))

    def set_password(self, user_id, password_hash):
        with self.transaction() as db:
            if not db.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash, user_id)).rowcount:
                raise LookupError('Account not found')
            self._revoke(db, user_id)

    def create_session(self, user_id, token):
        now = time.time()
        with self.transaction() as db:
            db.execute('DELETE FROM sessions WHERE expires_at<=? OR last_seen<=?', (now, now - 43200))
            db.execute('DELETE FROM sessions WHERE id IN (SELECT id FROM sessions WHERE user_id=? ORDER BY created_at DESC LIMIT -1 OFFSET 9)', (user_id,))
            db.execute('INSERT INTO sessions VALUES (?, ?, ?, ?, ?)', (digest(token), user_id, now, now, now + 604800))

    def session_user(self, token):
        now = time.time()
        with self.transaction() as db:
            row = db.execute('SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.id=? AND s.expires_at>? AND s.last_seen>? AND u.enabled=1',
                             (digest(token), now, now - 43200)).fetchone()
            if row:
                db.execute('UPDATE sessions SET last_seen=? WHERE id=?', (now, digest(token)))
                return self.user_view(row)
        return None

    def revoke_session(self, session_id):
        with self.transaction() as db:
            db.execute('DELETE FROM sessions WHERE id=?', (session_id,))

    def sessions(self):
        with self.transaction() as db:
            return [dict(r) for r in db.execute('SELECT s.id, u.username, s.created_at, s.last_seen, s.expires_at FROM sessions s JOIN users u ON u.id=s.user_id WHERE expires_at>? AND last_seen>? ORDER BY last_seen DESC', (time.time(), time.time() - 43200))]

    def save_policy(self, policy):
        with self.transaction() as db:
            db.execute('UPDATE access_state SET policy=? WHERE id=1', (policy.model_dump_json(),))

    def update_policy(self, changes):
        """Merge independent settings forms without overwriting another section."""
        with self.transaction() as db:
            row = db.execute('SELECT policy FROM access_state WHERE id=1').fetchone()
            policy = AccessPolicy.model_validate({**json.loads(row['policy']), **changes})
            db.execute('UPDATE access_state SET policy=? WHERE id=1', (policy.model_dump_json(),))
        return policy

    def disable(self):
        with self.transaction() as db:
            db.execute('DELETE FROM sessions')
            db.execute('DELETE FROM credentials')
            db.execute('DELETE FROM users')
            db.execute("UPDATE access_state SET mode='open' WHERE id=1")
        self.marker.unlink(missing_ok=True)

    def credentials(self):
        with self.transaction() as db:
            return [dict(r) for r in db.execute('SELECT id, label, kind, created_at FROM credentials ORDER BY created_at DESC')]

    def issue_credential(self, user_id, label, kind, token):
        result = dict(id=uuid4().hex, label=label, kind=kind, created_at=time.time())
        with self.transaction() as db:
            if db.execute('SELECT count(*) FROM credentials').fetchone()[0] >= 100:
                raise ValueError('Credential limit reached; revoke an unused credential')
            db.execute('INSERT INTO credentials VALUES (?, ?, ?, ?, ?, ?)',
                       (result['id'], digest(token), user_id, label, kind, result['created_at']))
        return {**result, 'token': token}

    def credential_user(self, token, kind):
        with self.transaction() as db:
            row = db.execute('SELECT u.* FROM credentials c JOIN users u ON c.user_id=u.id WHERE c.digest=? AND c.kind=? AND u.enabled=1', (digest(token), kind)).fetchone()
            return self.user_view(row) if row else None

    def revoke_credential(self, credential_id):
        with self.transaction() as db:
            db.execute('DELETE FROM credentials WHERE id=?', (credential_id,))
