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


def test_a_jump_back_across_the_pcr_wrap_counts_as_a_jump_back(caplog):
    clock = _Clock()
    watch = ClockWatch("abc", clock=clock)
    top = ts_clock.PCR_WRAP
    with caplog.at_level(logging.INFO, logger=ts_clock.__name__):
        for t in (5.0, 5.5, top - 10.0):
            watch.feed(_chunk(t))
            clock.now += 0.5
    assert [r.getMessage() for r in caplog.records] == ["TV relay source clock went back 15.5 s content_id=abc"]
    assert watch.back_jumps == 1


def _single_jump(back_seconds, after_seconds):
    """A source that plays steadily, then jumps back once."""
    clock = _Clock()
    watch = ClockWatch("abc", clock=clock)
    t = 500.0
    for _ in range(int(after_seconds / 0.5)):
        watch.feed(_chunk(t))
        t += 0.5
        clock.now += 0.5
    watch.feed(_chunk(t - back_seconds))
    return watch


def test_one_large_jump_back_in_the_first_seconds_makes_a_source_jumpy():
    watch = _single_jump(161.9, after_seconds=2.0)
    assert watch.back_jumps == 1 and watch.early_loop and watch.jumpy


def test_one_jump_back_is_not_jumpy_when_late_small_or_a_new_clock_base():
    late = _single_jump(161.9, after_seconds=60.0)
    small = _single_jump(5.0, after_seconds=2.0)
    new_base = _single_jump(3000.0, after_seconds=2.0)
    for watch in (late, small, new_base):
        assert watch.back_jumps == 1 and not watch.early_loop and not watch.jumpy


def test_the_summary_is_written_even_without_jumps_so_a_zero_can_be_read(caplog):
    clock = _Clock()
    steady = ClockWatch("abc", clock=clock)
    blind = ClockWatch("def", clock=clock)
    for t in (10.0, 10.5, 11.0):
        steady.feed(_chunk(t))
        clock.now += 0.5
    blind.feed(b"not a transport stream")
    with caplog.at_level(logging.INFO, logger=ts_clock.__name__):
        steady.summary()
        blind.summary()
    lines = [r.getMessage() for r in caplog.records]
    assert any("content_id=abc back_jumps=0" in m and "pcr_samples=3" in m for m in lines)
    assert any("content_id=def back_jumps=0" in m and "pcr_samples=0" in m for m in lines)
