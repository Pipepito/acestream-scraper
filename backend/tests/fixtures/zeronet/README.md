# ZeroNet verification fixture

Unmodified method excerpts from `src/Content/ContentManager.py` at
zeronet-conservancy commit `81d3ffc6bdfb600e9a1d4a091f1ceb131d92c4f1`:
https://github.com/zeronet-conservancy/zeronet-conservancy/blob/81d3ffc6bdfb600e9a1d4a091f1ceb131d92c4f1/src/Content/ContentManager.py

Upstream license is included in LICENSE. The complete upstream source SHA-256 is
`6212979e65e61862c6ca364b930843f3a3eb2f5fcda542bb9ea4615ba05a8e34`.

The offline tests apply the actual installer patch to these methods and execute
them with in-memory site state and a signature-verifier test double. They test
verification control flow, not the cryptography implementation or peer discovery.
When changing the installer source pin, refresh these excerpts from that exact
commit and review every behavioral expectation. Included-manifest traversal is
intentionally left unchanged; it is tracked in upstream issue #333.
