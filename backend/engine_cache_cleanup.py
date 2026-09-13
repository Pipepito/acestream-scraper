"""Reclaim abandoned bundled-engine media cache without following symlinks.

Runs outside the application/event loop. Cache directories must be private to
this container: /proc cannot reveal users of a shared volume on another host.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import stat
import sys

LOG = logging.getLogger("engine-cache")


def open_inodes(proc: Path = Path("/proc")) -> set[tuple[int, int]]:
    """Fail closed on unreadable process state; vanished processes are normal."""
    inodes = set()
    if not (proc / "self" / "fd").is_dir():
        raise OSError("Process file inspection unavailable")
    for process in proc.iterdir():
        if not process.name.isdecimal():
            continue
        try:
            for descriptor in (process / "fd").iterdir():
                try:
                    info = descriptor.stat()
                    inodes.add((info.st_dev, info.st_ino))
                except FileNotFoundError:
                    continue
            # mmap users can close their original file descriptor.
            for line in (process / "maps").read_text().splitlines():
                fields = line.split(None, 5)
                major, minor = fields[3].split(":")
                inodes.add((os.makedev(int(major, 16), int(minor, 16)), int(fields[4])))
        except FileNotFoundError:
            continue
    return inodes


def open_directory(path: Path) -> int:
    """Open each component without following a symlink, including ancestors."""
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("Cache path must be absolute without parent components")
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def clean_cache(path: Path) -> tuple[int, int]:
    """Reclaim regular cache files only while the owning engine is stopped.

    The supervisor serializes this with engine launches and kills the previous
    process group first. Open/mapped files held by other local processes remain.
    """
    removed = size = 0
    try:
        root = open_directory(path)
    except FileNotFoundError:
        return removed, size
    try:
        busy = open_inodes()
        for _, _, names, directory in os.fwalk(".", follow_symlinks=False, dir_fd=root):
            for name in names:
                try:
                    info = os.stat(name, dir_fd=directory, follow_symlinks=False)
                    if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) in busy:
                        continue
                    os.unlink(name, dir_fd=directory)
                    removed += 1
                    size += info.st_size
                except FileNotFoundError:
                    continue
    finally:
        os.close(root)
    return removed, size


def cache_paths(slug: str) -> list[Path]:
    if slug == "acestream-check":
        return [Path("/var/lib/acestream-check/cache")]
    if slug != "acestream":
        raise ValueError("Unknown engine")
    return list(dict.fromkeys([
        Path.home() / ".ACEStream" / ".acestream_cache",
        Path(os.environ.get("ACESTREAM_HOME", "/var/lib/acestream")) / ".ACEStream" / ".acestream_cache",
    ]))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[engine-cache] %(message)s")
    for path in cache_paths(sys.argv[1]):
        try:
            count, size = clean_cache(path)
            if count:
                LOG.info("Removed %d leftover cache files (%d bytes)", count, size)
        except (OSError, ValueError):
            # No paths or process details in diagnostic logs. Failure must never
            # prevent the supervisor from recovering the engine.
            LOG.warning("Cache cleanup skipped: cache or process state unavailable")


if __name__ == "__main__":
    main()
