#!/usr/bin/env python3
"""Stand-in for ffmpeg in player tests. Reads the output playlist path from
the last argv entry, prints a codec dump like ffmpeg does, then writes HLS
segments until it is terminated. Behaviour switches via env FAKE_FFMPEG_MODE:
  normal (default) | never_ready | exit_early | flood_stderr
"""
import os
import signal
import sys
import time
from pathlib import Path

mode = os.environ.get("FAKE_FFMPEG_MODE", "normal")
playlist = Path(sys.argv[-1])
directory = playlist.parent
directory.mkdir(parents=True, exist_ok=True)

sys.stderr.write("Input #0, mpegts, from 'http://engine':\n")
sys.stderr.write("  Stream #0:0[0x100]: Video: %s (High) ([27][0][0][0] / 0x001B), yuv420p, 1920x1080\n" % os.environ.get("FAKE_FFMPEG_VIDEO", "h264"))
sys.stderr.write("  Stream #0:1[0x101]: Audio: %s ([129][0][0][0] / 0x0081), 48000 Hz, stereo\n" % os.environ.get("FAKE_FFMPEG_AUDIO", "ac3"))
sys.stderr.flush()

if mode == "exit_early":
    sys.stderr.write("Error opening input: Connection refused\n")
    sys.exit(1)

running = True


def _term(*_):
    global running
    running = False


signal.signal(signal.SIGTERM, _term)
seq = 0
while running:
    if mode == "flood_stderr" and seq < 400:
        sys.stderr.write("\r" + ("frame=%d fps=25 q=-1.0 size=1024kB time=00:00:01.00 bitrate=8192kbits/s speed=1x" % seq) * 4)
        sys.stderr.flush()
    if mode != "never_ready":
        seg = directory / f"seg{seq:05d}.ts"
        seg.write_bytes(b"\x47" + b"\x00" * 187)
        keep = list(range(max(0, seq - 5), seq + 1))
        tmp = playlist.with_suffix(".m3u8.tmp")
        tmp.write_text("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:2\n#EXT-X-MEDIA-SEQUENCE:%d\n" % keep[0]
                       + "".join("#EXTINF:2.000000,\nseg%05d.ts\n" % i for i in keep))
        os.replace(tmp, playlist)
        for old in directory.glob("seg*.ts"):
            if int(old.stem[3:]) < keep[0]:
                old.unlink(missing_ok=True)
        seq += 1
    time.sleep(0.05)
sys.exit(0)
