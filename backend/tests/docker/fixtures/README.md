# Docker test fixtures

`sample-h264-ac3.m2ts` is a 2-second H.264 + AC-3 MPEG-TS clip. It stands in
for an AceStream engine's output in `test_ffmpeg_build.py`, which proves the
image's minimal static ffmpeg can copy-remux TS -> HLS and transcode AC-3 ->
AAC on every image platform. `SHA256SUMS` pins its bytes.

Regenerate with:

```bash
mkdir -p backend/tests/docker/fixtures
docker run --rm -v "$PWD/backend/tests/docker/fixtures:/out" lscr.io/linuxserver/ffmpeg:latest \
  -f lavfi -i testsrc2=size=64x64:rate=5 -f lavfi -i sine=frequency=440:sample_rate=48000 \
  -t 2 -c:v libx264 -preset ultrafast -pix_fmt yuv420p -c:a ac3 -b:a 64k -f mpegts /out/sample-h264-ac3.m2ts
(cd backend/tests/docker/fixtures && shasum -a 256 sample-h264-ac3.m2ts > SHA256SUMS && cat SHA256SUMS && ls -la)
```

Regenerate only with a full ffmpeg; the image's minimal build has no video or
AC-3 encoders. `.m2ts` keeps TypeScript tooling globs away from the file.
