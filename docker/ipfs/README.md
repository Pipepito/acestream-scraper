# Kubo security build

The production image cross-compiles Kubo v0.43.1 from upstream commit
`acc53c093810a8fe9a4bc2f023f0b1e0c1d629b5`, with the source archive SHA-256
verified by `docker/scripts/install-ipfs.sh`. The official release binary still
contains vulnerable Go libraries, so this build uses Go 1.27.3 and the reviewed
`go.mod`/`go.sum` here. It identifies itself as a security rebuild, not an
unmodified upstream binary.

The module changes update go-jose to 4.1.6, x/net to 0.62.0 and gRPC to 1.83.2,
including the versions selected for their transitive dependencies. Image builds
verify module checksums and compile with `-mod=readonly` and `GOTOOLCHAIN=local`.
They do not resolve `latest` or rewrite these locks. AMD64 and ARM64 use the same
source and locks; ARMv7 keeps its documented external-gateway requirement.

For an update, check the official release and security advisories, verify the
source archive, resolve the reviewed versions in a disposable checkout, then
review and copy both module files. Update the source checksum and toolchain guard
together. Run the offline add/cat, daemon/API and persistent-repository checks in
`docker/testdata/security_dependency_smoke.py`, all supported image builds and a
fresh scan of the actual image. Do not infer safety from module versions alone.
