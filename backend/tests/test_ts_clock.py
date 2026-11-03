"""The relay logs a source whose own clock (PCR) jumps back, without touching the bytes."""
import asyncio
import logging

from app.services import ts_clock
from app.services.ts_clock import ClockWatch, watch_clock


def _packet(pid, pcr_seconds=None):
    """One 188-byte TS packet, with a PCR in its adaptation field when given."""
    head = bytes([0x47, (pid >> 8) & 0x1F, pid & 0xFF])
    if pcr_seconds is None:
        return head + bytes([0x10]) + bytes(184)
    base = int(pcr_seconds * 90000) & ((1 << 33) - 1)
    pcr = bytes([(base >> 25) & 0xFF, (base >> 17) & 0xFF, (base >> 9) & 0xFF, (base >> 1) & 0xFF,
                 ((base & 1) << 7) | 0x7E, 0x00])
    adaptation = bytes([7, 0x10]) + pcr
    return head + bytes([0x30]) + adaptation + bytes(184 - len(adaptation))


def _chunk(pcr_seconds, pid=0x100):
    return _packet(pid) * 3 + _packet(pid, pcr_seconds) + _packet(pid) * 3


class _Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_a_clock_going_back_is_logged_once_per_burst(caplog):
    clock = _Clock()
    watch = ClockWatch("abc", clock=clock)
    with caplog.at_level(logging.INFO, logger=ts_clock.__name__):
        for t in (100.0, 100.5, 101.0, 61.0, 61.5, 30.0):
            watch.feed(_chunk(t))
            clock.now += 0.5
    lines = [r.getMessage() for r in caplog.records]
    assert lines == ["TV relay source clock went back 40.0 s content_id=abc"]
    assert watch.back_jumps == 2 and round(watch.worst_back, 1) == 40.0


def test_a_steady_clock_and_a_wrapping_pcr_log_nothing(caplog):
    clock = _Clock()
    watch = ClockWatch("abc", clock=clock)
    top = ts_clock.PCR_WRAP
    with caplog.at_level(logging.INFO, logger=ts_clock.__name__):
        for t in (top - 1.0, top - 0.5, 0.0, 0.5):
            watch.feed(_chunk(t))
            clock.now += 0.5
    assert caplog.records == [] and watch.back_jumps == 0


def test_a_jump_far_ahead_of_the_wall_clock_is_logged(caplog):
    clock = _Clock()
    watch = ClockWatch("abc", clock=clock)
    with caplog.at_level(logging.INFO, logger=ts_clock.__name__):
        watch.feed(_chunk(10.0))
        clock.now += 1
        watch.feed(_chunk(100.0))
    assert [r.getMessage() for r in caplog.records] == ["TV relay source clock jumped ahead 89.0 s content_id=abc"]


def test_only_the_first_pcr_pid_counts_and_misaligned_chunks_are_read():
    watch = ClockWatch("abc", clock=_Clock())
    watch.feed(b"\x00\x01" + _chunk(50.0, pid=0x100) + _chunk(5.0, pid=0x200))
    assert watch.back_jumps == 0


def test_the_wrapper_passes_every_byte_through_and_summarises(caplog):
    chunks = [_chunk(100.0), _chunk(60.0), b"not a transport stream"]

    async def source():
        for c in chunks:
            yield c

    async def read_all():
        return [c async for c in watch_clock(source(), "abc")]

    with caplog.at_level(logging.INFO, logger=ts_clock.__name__):
        assert asyncio.run(read_all()) == chunks
    assert any("summary content_id=abc back_jumps=1" in r.getMessage() for r in caplog.records)


def test_a_step_ahead_between_two_samples_is_logged_even_without_a_wall_jump(caplog):
    clock = _Clock()
    watch = ClockWatch("abc", clock=clock)
    with caplog.at_level(logging.INFO, logger=ts_clock.__name__):
        for t in (10.0, 10.5, 18.0, 18.5):
            watch.feed(_chunk(t))
            clock.now += 0.5
    assert [r.getMessage() for r in caplog.records] == ["TV relay source clock stepped ahead 7.5 s content_id=abc"]
    assert watch.forward_steps == 1 and not watch.jumpy


def test_a_burst_of_steady_chunks_is_not_a_step(caplog):
    clock = _Clock()
    watch = ClockWatch("abc", clock=clock)
    with caplog.at_level(logging.INFO, logger=ts_clock.__name__):
        clock.now += 16.0  # sixteen seconds of nothing, then the buffer at once
        for i in range(40):
            watch.feed(_chunk(100.0 + i * 0.4))
            clock.now += 0.01
    assert caplog.records == [] and watch.forward_steps == 0


def test_two_jumps_back_make_a_source_jumpy():
    clock = _Clock()
    watch = ClockWatch("abc", clock=clock)
    for t in (100.0, 100.5, 90.0, 90.5, 80.0):
        watch.feed(_chunk(t))
        clock.now += 0.5
    assert watch.back_jumps == 2 and watch.jumpy and watch.watched_seconds == 2.0
