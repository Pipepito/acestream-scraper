"""Cache reclamation must never reach engine identity or symlink targets."""
import os
from pathlib import Path

import pytest

import engine_cache_cleanup as cleanup


@pytest.fixture
def cache(tmp_path, monkeypatch):
    directory = tmp_path.resolve() / ".ACEStream" / ".acestream_cache"
    directory.mkdir(parents=True)
    monkeypatch.setattr(cleanup, "open_inodes", lambda: set())
    return directory


def test_cleans_media_but_preserves_state_directories_and_symlinks(cache):
    state = cache.parent / "acestream.conf"
    state.write_text("identity")
    (cache / "leftover.tmp").write_bytes(b"abc")
    segments = cache / "_hls_example"
    segments.mkdir()
    (segments / "1.ts").write_bytes(b"defg")
    (cache / "state-link").symlink_to(state)
    (cache / "directory-link").symlink_to(cache.parent, target_is_directory=True)
    os.mkfifo(cache / "pipe")

    assert cleanup.clean_cache(cache) == (2, 7)
    assert state.read_text() == "identity"
    assert segments.is_dir()
    assert (cache / "state-link").is_symlink()
    assert (cache / "directory-link").is_symlink()
    assert (cache / "pipe").exists()
    assert cleanup.clean_cache(cache) == (0, 0)


def test_preserves_open_or_mapped_inode(cache, monkeypatch):
    media = cache / "live.cache"
    media.write_bytes(b"active")
    info = media.stat()
    monkeypatch.setattr(cleanup, "open_inodes", lambda: {(info.st_dev, info.st_ino)})
    assert cleanup.clean_cache(cache) == (0, 0)
    assert media.exists()


def test_refuses_cleanup_when_process_inspection_fails(cache, monkeypatch):
    media = cache / "leftover"
    media.write_text("keep")

    def denied():
        raise PermissionError("unreadable process")

    monkeypatch.setattr(cleanup, "open_inodes", denied)
    with pytest.raises(PermissionError):
        cleanup.clean_cache(cache)
    assert media.exists()


def test_refuses_symlink_root_or_ancestor(cache):
    link = cache.parent.parent / "linked-state"
    link.symlink_to(cache.parent, target_is_directory=True)
    with pytest.raises(OSError):
        cleanup.clean_cache(link / cache.name)
    link2 = cache.parent / "linked-cache"
    link2.symlink_to(cache, target_is_directory=True)
    with pytest.raises(OSError):
        cleanup.clean_cache(link2)


def test_missing_cache_is_harmless(cache):
    assert cleanup.clean_cache(cache / "absent") == (0, 0)


def test_proc_inventory_includes_open_and_mapped_files(tmp_path):
    proc = tmp_path / "proc"
    (proc / "self" / "fd").mkdir(parents=True)
    descriptors = proc / "123" / "fd"
    descriptors.mkdir(parents=True)
    media = tmp_path / "media"
    media.write_text("data")
    (descriptors / "3").symlink_to(media)
    (descriptors / "4").symlink_to(tmp_path / "vanished")
    (proc / "123" / "maps").write_text("1-2 r--p 00000000 08:01 42 /mapped/media\n")
    info = media.stat()
    assert cleanup.open_inodes(proc) == {(info.st_dev, info.st_ino), (os.makedev(8, 1), 42)}


def test_paths_keep_checker_and_playback_separate(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ACESTREAM_HOME", str(tmp_path / "arm-state"))
    assert cleanup.cache_paths("acestream") == [
        tmp_path / "home/.ACEStream/.acestream_cache",
        tmp_path / "arm-state/.ACEStream/.acestream_cache",
    ]
    assert cleanup.cache_paths("acestream-check") == [Path("/var/lib/acestream-check/cache")]
    with pytest.raises(ValueError):
        cleanup.cache_paths("other")
