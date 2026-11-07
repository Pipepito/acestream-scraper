# ARM64 `mod_detected` investigation

Test date: 2026-09-15. Host: Apple Silicon, Docker Desktop running native
`linux/arm64` containers. Repository baseline: `e93a75d` on `develop`.

## Confirmed launcher regression

The pinned `jopsis/acestream:v3.2.17-fix` distribution starts through
`aceserve.main()`. Our replacement Linux bootstrap instead called
`acestreamengine.Core.run()` directly. The bundled engine answered version and
health requests successfully but returned `mod_detected` for both tested channel
IDs. Unchanged upstream containers and the same bundled payload entered through
`aceserve.main()` delivered audio/video from those IDs.

The fix retains the engine version, immutable image pin, persistent home,
per-install device identity, command arguments, cache settings and supervisor.
It selects the distribution entry point using the installer's preserved
`main.py.oci-orig`. Legacy APK installations retain `Core.run()`. A missing or
failing OCI entry point exits with an error; it must not silently fall back to
Core and appear healthy with broken playback.

No engine binary or authentication decision was patched, and no alternate app
identity or account was introduced.

## Version comparison

Three channel IDs were selected from recently successful media checks in a
maintainer-provided installation. Initial inspection was read-only; the maintainer
later authorized fresh status checks on its dedicated checker. URLs, channel IDs
and private coordinates are excluded from this report.

| ARM64 build | Observation |
|---|---|
| Bundled 3.2.17-fix with the original Core launcher | `mod_detected` on both initial IDs; no playback URL |
| Unchanged upstream `v3.2.17-fix` | Both IDs started; captures of 24,117,248 and 25,165,824 bytes contained video and audio packets |
| Unchanged upstream `latest` (also reports 3.2.17) | Both IDs started; two 25,165,824-byte captures contained video and audio packets |
| Unchanged upstream `v3.2.15` | Both IDs started; 22,544,384 and 25,165,824 bytes with video and audio packets |
| Bundled 3.2.17-fix with the corrected entry point | Both IDs started; 14,155,776 and 25,165,824 bytes with video and audio packets |
| Unchanged upstream `arm64-v3.2.13`, tested later | Fresh ID lookup failed with `failed to load content`; not counted as a playback pass |

Upstream sources: [packaging repository](https://github.com/jopsis/docker-acestream-aceserve)
and [published engine tags](https://hub.docker.com/r/jopsis/acestream/tags).
Tested manifest digests:

- `v3.2.17-fix`: `sha256:506c4215115d8b0ac1e24f4c67c954f0dbf86e4b4ea508582e497d8c920e9933`.
- `latest`: `sha256:5460eda6198e436dfa28ee070ea6bbe775aaebc5435ef48aa773625b5912c8db`.
- `v3.2.15`: `sha256:7c5928c32d12e6c6179e9f3286c5932f7d5043c648f6eec3213c804dc0383191`.
- `arm64-v3.2.13`: `sha256:8d8b04c7885b4982d88badabf776cd48c99e486bd02e1db1c4b5abc134bbfdc4`.

These observations support repairing the launcher, not changing the engine pin.
They do not establish that an older version is generally more reliable.

The corrected bundled engine also completed a 300-second playback run, delivering
166,723,584 bytes. Its retained sample contained H.264 video and MP2 audio packets.
This was a repeat of a successfully resolved ID, not a fresh-ID availability test.

### Browser playback on the Mac

After restarting that engine with the exact committed bootstrap and DNS helper
(SHA-256 matches verified against the repository), the rebuilt app was configured
to use it through a local Docker host endpoint. Both app and engine ran on the
same Mac. The app's player visibly rendered the second test channel at 1920×1080:
the video element reported `paused=false`, `readyState=4` and 24.826 seconds of
playback. The app converted E-AC-3 audio to AAC. An actual screenshot of the
playing football stream was delivered to the maintainer; broadcast imagery is
not committed to the repository.

The first channel produced HLS but failed in the in-app browser. The second
channel's successful browser playback does not resolve that separate failure or
the fresh-ID lookup limitation below. This test used a previously resolved ID;
it did not replay a saved media recording or use the maintainer's remote engine.

## Playback/checker DNS collision

Running the playback and checking engines together exposed an independent race:
both upstream DNS threads bind `/dev/socket/dnsproxyd`. The losing listener raises
`Address already in use`, then its `finally` block removes the winning listener's
socket path. Both engines remain running, but new bionic DNS clients cannot reach
the listener.

`bionic_dns.py` coordinates ownership with an OS file lock. Exactly one process
calls the upstream listener; the other waits. If the owner exits, the waiting
engine acquires the lock, removes the stale socket and starts listening. The lock
file is never removed, preventing competing lock inodes. Configuration and DNS
selection remain per container; no public resolver is imposed on users.

A two-process regression test verifies concurrent access and takeover after the
owner exits. The local dual-engine image retained a live socket and answered DNS
requests after this change. In the canonical rebuilt image, stopping the checking
engine through the app's service API transferred the lock to the playback engine;
the surviving listener returned a successful DNS reply. The checker was then
started again.

## Initial network failures

Later in the same session, fresh content-ID lookups failed in unchanged upstream
3.2.17 containers too. The previously successful engine continued delivering its
two cached channels, but failed to resolve a third uncached ID. An explicit DNS
server in a disposable test container did not restore fresh lookups. The controlled
WARP comparison below subsequently isolated a network-path dependency.

The patched app's tuner and Acexy tests consequently hit lookup timeouts rather
than `mod_detected`. They are **not** counted as successful end-to-end ID-based
playback tests. Replaying the two transport descriptors already downloaded by the
successful engine through a private temporary HTTP server allowed the patched
bundled playback engine to deliver two 25,165,824-byte captures, with H.264 video
and MP2/E-AC-3 audio. This isolates media delivery from the unavailable lookup path;
it does not prove fresh ID lookup works.

The canonical `scraper-acestream-acexy` ARM64 image built successfully from the
repository with both engines and Acexy enabled. Descriptor replay delivered
25,165,824 bytes with H.264 video and E-AC-3 audio for one source; the other source
returned a playback URL but timed out while reading media. This partial result is
recorded separately from the earlier two-source success with the patched image.

The tests do not establish long-term stability, Raspberry Pi behavior, ARMv7
runtime behavior, or availability of every source. The matching ARMv7 image's
bootstrap was inspected without execution and also calls `aceserve.main()`;
ARMv7 remains experimental.

## Fresh-state WARP comparison

The reference server runs the native Linux 3.2.11 engine with WARP connected.
Fresh checks on its dedicated engine verified all three channels as online.
Local comparisons used the same pinned ARM64 3.2.17-fix image and the same IDs:

| Local test | Result |
|---|---|
| New container, WARP disabled, empty engine state | All three lookups returned `failed to load content` after about 45.2 seconds each |
| New container, WARP connected, empty engine state | All three IDs resolved in 4.43, 0.37 and 0.57 seconds; every capture contained audio/video |
| Previously unused checker in the WARP container, tunnel disconnected | The first ID returned `failed to load content` |
| Same checker, same ID, WARP reconnected, no engine restart | Lookup succeeded and delivered 12,058,624 bytes with H.264/MP2 packets |
| Rebuilt image with startup/DNS improvements, fresh engine state, WARP connected | All three app checks reported `found`, online and verified media; checks completed in 12.51, 5.17 and 5.84 seconds |

In the rebuilt image, direct engine requests resolved those IDs in 0.40, 0.40
and 0.44 seconds and delivered audio/video. The app tuner delivered 134,217,728
bytes over 120.53 seconds; Acexy delivered 50,397,184 bytes over 128.60 seconds.
Both returned HTTP 200 and their captured samples contained identified video and
audio packets. These tests used the engines bundled in the new container, without
copying resolver databases, transport descriptors or state from earlier tests.

A persistent Android-runtime process using the production resolver answered DNS
before, during and after WARP disconnect/reconnect, selecting the tunnel servers,
Docker's original servers, then the tunnel servers again. The final container
also recovered after a full Docker restart: WARP, both engines and Acexy were
running, and the app rendered live video at 1920×1080 (`readyState=4`, unpaused,
83.907 seconds of playback). A fresh screenshot was delivered to the maintainer.

This establishes fresh-ID playback through WARP on the Mac. It does not identify
the precise external network block or imply that every installation needs WARP.
The 45-second failures came from the engine itself; simply extending the app's
HTTP timeout would not repair that route. Keep the existing configurable check
timeout and retry behavior.

Two reliability improvements accompany this evidence:

- When `WARP_ENABLE_NAT=true`, startup waits for WARP's JSON status to report
  `Connected`. A zero exit code from the CLI only means the daemon answered;
  it also succeeds while disconnected or connecting. Exhausting the existing
  readiness budget fails startup instead of launching engines before the tunnel.
- The ARM Python resolver rereads the container's nameservers before DNS work,
  following WARP connect/disconnect rewrites. A transient empty, missing or invalid
  file retains the last valid servers and produces a bounded warning. It never
  imposes a public DNS provider. Both engines and their shared listener use this
  behavior.

No native resolver ABI patch, binary modification, forced WARP default or increased
playback timeout was introduced. Raw bionic connectivity diagnostics still have
limitations outside Android; they are not used as a substitute for verified media.

Validation for the reliability follow-up: 30 bootstrap, DNS, WARP-startup and
manifest tests plus 32 WARP API/status tests passed. The canonical ARM64 image
built successfully, and documentation, manifest, strict legacy-path and shell
syntax checks passed. Images were built locally, not published.

## Rechecking

Offline regression and packaging contracts:

The focused suite below passed all 37 tests. Documentation validation, strict
legacy-path validation and shell syntax checks also passed. The canonical local
image build below completed; no images were published.

```bash
PYTHONPATH=backend backend/venv/bin/pytest -q \
  backend/tests/test_android_engine_bootstrap.py \
  backend/tests/docker/test_acestream_manifest.py \
  backend/tests/test_engine_cache_cleanup.py \
  backend/tests/test_check_engine_config.py
python3 scripts/ci/validate_docker_manifest_metadata.py
```

Build the canonical ARM64 image locally without publishing:

```bash
bash scripts/ci/build_multiarch_images.sh \
  --flavor scraper-acestream-acexy --platforms linux/arm64 \
  --load --tag acestream-scraper:arm64-entrypoint-fixed
```

For live verification, use disposable engine state, at least two currently working
IDs, and unique request PIDs. Require actual audio/video packets in the response;
HTTP 200, `get_version`, a playback URL or a peer count alone is insufficient.
Test a fresh ID as well as a cached one, restart the engine, and repeat with the
dedicated checker enabled. Stop the DNS-owning engine and confirm the survivor
retains DNS resolution. Preserve other users' playback and production data.
