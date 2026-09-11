# Bundled ZeroNet manifest verification

The installer applies a narrow compatibility patch to zeronet-conservancy commit
`81d3ffc6bdfb600e9a1d4a091f1ceb131d92c4f1`. On 2026-09-11 this remained upstream
`main`; recheck upstream before changing the pin.

Upstream [issue #331](https://github.com/zeronet-conservancy/zeronet-conservancy/issues/331)
reports matching manifests being rejected because `verifyContent()` compares a
`Path` with a string. The patch compares paths on both sides of that condition and
restores string comparisons for the root manifest size limit and root dispatch.
It leaves `inner_path` a string so first-download accounting and signature checks
retain their existing behavior. Invalid paths, site addresses, relative filenames
and signatures must still fail. Oversized root manifests abort the download task.

The patch runs before dependency installation on amd64 and arm64. ARMv7 remains
an unsupported bundled platform; external nodes are not modified. Supervision,
health probes and persistent data layout are unchanged. The patch accepts its
original, partially patched and fully patched forms, validates expected occurrence
counts within `verifyContent()`, and parses the result before writing. Unexpected
source changes fail the build. Installation metadata identifies the upstream pin;
the installed checkout additionally contains this local modification.

## Verification

```bash
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_zeronet_verification.py
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_install_zeronet.py
```

The first suite is offline and runs in both quick and full CI profiles. It executes
unmodified upstream method excerpts after applying the actual installer patch.
It covers patch drift/idempotency, root accounting, root dispatch, size enforcement,
invalid paths/addresses/filenames, signature rejection and include-rule enforcement.
The signature verifier is a test double: these tests exercise enforcement of its
verdict, not the cryptographic implementation. The second suite includes a Docker
build, real-signature verification and startup/state-persistence smoke when Docker
is available. Its `zeronet_manifest_smoke.py` helper runs under the bundled Python
with networking disabled and checks valid, tampered, unsigned, wrong-path and
oversized signed manifests. It can also run against an existing image with
`--apply-patch`, applying the reviewed installer patch inside the disposable
container; this checks the runtime but does not replace an installer image build.

## Remaining upstream defects

Included/user manifests can still fail in `getRules()` because `Path.parts` is a
tuple and upstream calls `.pop()` on it. See
[issue #333](https://github.com/zeronet-conservancy/zeronet-conservancy/issues/333).
Repairing rule traversal and signing needs separate tests for parent includes,
delegated signers and certificates. This patch restores root-manifest downloads;
it does not claim all sites or publishing workflows are repaired.

Do not adopt upstream
[PR #335](https://github.com/zeronet-conservancy/zeronet-conservancy/pull/335)
wholesale: it bypasses failed signature verification. DHT discovery changes are
separate from manifest validation; additional trackers cannot repair this rejection.
