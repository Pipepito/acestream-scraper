"""Bounded console capture for every container flavour; no application imports."""
from datetime import datetime, timezone
from pathlib import Path
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
BACKUPS = 2
WARP_LEVEL = re.compile(
    rb'^\d{4}-\d{2}-\d{2}T\S+\s+(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL)\b'
)
ANSI_STYLE = re.compile(rb'\x1b\[[0-9;]*m')


class WarpConsoleFilter:
    """Filter known routine records, retaining unknown output and issue details."""

    def __init__(self):
        self.visible = True
        self.line_start = True

    def allows(self, chunk: bytes) -> bool:
        if self.line_start:
            plain = ANSI_STYLE.sub(b'', chunk)
            level = WARP_LEVEL.match(plain)
            if level:
                self.visible = level[1] not in (b'TRACE', b'DEBUG', b'INFO')
            elif not (plain[:1].isspace() or plain.startswith(b'Per origin:')):
                # Supervisor/setup messages and unfamiliar formats fail open.
                self.visible = True
        # readline is bounded: the rest of a long line inherits its decision.
        self.line_start = chunk.endswith(b'\n')
        return self.visible


def capture(source, console, directory: Path, max_bytes: int = MAX_BYTES,
            name: str = 'console.log') -> None:
    path = directory / name
    warned = False
    prefix = f'[{Path(name).stem}] '.encode()
    line_start = True
    console_filter = WarpConsoleFilter() if name == 'warp.log' else None
    while chunk := source.readline(8192):
        try:
            if console_filter is None or console_filter.allows(chunk):
                # Prefix physical lines, not each bounded read of a long line.
                # Entrypoint messages already carry their own matching tag.
                tagged = prefix + chunk if line_start and not chunk.startswith(prefix) else chunk
                console.write(tagged)
                console.flush()
        except (BrokenPipeError, OSError):
            pass  # Losing Docker's reader must not stop draining child output.
        line_start = chunk.endswith(b'\n')
        try:
            record = datetime.now(timezone.utc).isoformat().encode() + b' ' + chunk
            if path.exists() and path.stat().st_size + len(record) > max_bytes:
                for index in range(BACKUPS, 0, -1):
                    old = path if index == 1 else directory / f'{name}.{index - 1}'
                    if old.exists():
                        old.replace(directory / f'{name}.{index}')
            # Reopen each time so rotation never leaves a writer on a retired inode.
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'ab') as output:
                output.write(record)
        except OSError:
            if not warned:
                print(f'[{Path(name).stem}] Diagnostics capture unavailable; console output continues.', file=sys.stderr)
                warned = True


if __name__ == '__main__':
    capture(sys.stdin.buffer, sys.stdout.buffer, Path(sys.argv[1]), name=sys.argv[2] if len(sys.argv) > 2 else 'console.log')
