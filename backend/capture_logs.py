"""Bounded console capture for every container flavour; no application imports."""
from datetime import datetime, timezone
from pathlib import Path
import os
import sys

MAX_BYTES = 2 * 1024 * 1024
BACKUPS = 2


def capture(source, console, directory: Path, max_bytes: int = MAX_BYTES) -> None:
    path = directory / 'console.log'
    warned = False
    while chunk := source.readline(8192):
        try:
            console.write(chunk)
            console.flush()
        except (BrokenPipeError, OSError):
            pass  # Losing Docker's reader must not stop draining child output.
        try:
            record = datetime.now(timezone.utc).isoformat().encode() + b' ' + chunk
            if path.exists() and path.stat().st_size + len(record) > max_bytes:
                for index in range(BACKUPS, 0, -1):
                    old = path if index == 1 else directory / f'console.log.{index - 1}'
                    if old.exists():
                        old.replace(directory / f'console.log.{index}')
            # Reopen each time so rotation never leaves a writer on a retired inode.
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'ab') as output:
                output.write(record)
        except OSError:
            if not warned:
                print('Diagnostics capture unavailable; console output continues.', file=sys.stderr)
                warned = True


if __name__ == '__main__':
    capture(sys.stdin.buffer, sys.stdout.buffer, Path(sys.argv[1]))
