# Prepared follow-up batches

Prepared 2026-10-20 after the v2.2 issue reconciliation. These batches are scoped,
not implemented. Each should get its own PR into develop and relevant local
tests. Stop and ask the maintainer if the scope expands beyond these limits.

## Batch 4 — WARP and incoming remote connections (#93)

Goal: a verified operator recipe for a known reverse-proxy or client network
whose return traffic must bypass WARP. WARP stays opt-in.

1. Read the existing WARP routing/excluded-network implementation and current
   documented commands. Reproduce with a disposable container and a known client
   or proxy network, recording both incoming and return routes.
2. Verify that an explicit excluded CIDR survives the supported lifecycle
   (connect, reconnect, restart), and that local services remain reachable.
3. Document the supported configuration and its limits. Add focused command
   contract tests if changing a command or persisted setting.
4. Verify WARP connected/disconnected behavior and engine startup ordering.

Acceptance: the documented known-network case is reproducible, exclusions are
explicit, WARP remains optional, and no blanket routing bypass is introduced.
Do not implement a dynamic nftables client watcher. Arbitrary internet clients,
unknown proxy topology or host-level routing changes require a separate decision.
Ask for the affected topology if existing issue evidence cannot reproduce it;
do not infer a production network layout.

## Batch 5 — external outpace compatibility (#217)

Goal: establish a narrow, tested external-engine path. Do not add a bundled
outpace flavor or change the default engine.

1. Pin the upstream version/digest being evaluated and recheck its published
   compatibility matrix. The issue reports 0.2.0; that is not a promise about
   the current release.
2. Inventory every scraper probe and playback call, especially the existing
   `get_version` health probe versus outpace's `get_status` route. Only add a
   bounded capability fallback after verifying its response shape; an arbitrary
   HTTP 200 must never count as a healthy engine.
3. Use contract fixtures for readiness, JSON start, stats and lease stop.
   Preserve unknown transfer rates as unknown. Cover unsupported routes,
   malformed/error responses, timeouts and failed dedicated-checker selection.
4. Run a disposable external outpace container with its compatibility flag and
   test a maintainer-approved public live source. Verify direct web/tuner
   playback, two viewers sharing a source, one viewer disconnecting, and final
   cleanup. An unsuccessful live source is not compatibility proof.
5. Document supported behavior and remaining gaps with the tested revision.

Acceptance: no global protocol switch, no fallback from a failed configured
checker to playback, no stop of another viewer, and existing official-engine
tests still pass. If compatibility needs a new player architecture, routing
model or refactor, report the evidence and split that work for planning.

## Deferred work

#102's upstream Acexy creation race needs upstream evidence; #224's mid-stream
TS concatenation needs explicit continuity/discontinuity design. #99 VOD, #55
sports aggregation, #13 installers and #216 AI extraction exceed these bounded
batches. #155 alias removal remains deferred by maintainer decision.

Status update, 2026-10-21 at develop `e7e554e`: #234 HTTP/HLS streams and
#235 regional live providers were accepted, reviewed and merged through #241
for v2.2.0. They are no longer unimplemented proposals. Their mixed-protocol
TV-relay failover extension remains separate. #233 HTML guide conversion still
needs its own timezone, identity, ambiguity and maintenance contract.

## Recommended next v2.2.0 work

1. Finish warning cleanup and validate the current integrated release first.
2. #226: reproduce a direct-engine JSON-start call exceeding 15 seconds before
   deciding a bounded setting/caller-deadline fix. Preserve cancellation and
   final lease cleanup; the tuner video-read limits are already configurable.
3. #93: implement and verify the existing bounded known-network routing recipe
   above, with reconnect/restart evidence. It is the smallest prepared follow-up.
4. #217: validate external outpace compatibility as scoped above after playback
   behavior settles. Recheck the upstream release; the issue now also reports
   v0.4.0 evidence, not just the original v0.2.0 proposal.

#102 needs upstream Acexy race evidence. #233 HTML guides and #246 Gluetun port
forwarding are subsequent scope/design decisions, not silently committed to
v2.2.0. #246 needs a supported Gluetun/provider contract, port ownership and
restart/failure behavior. This order is a recommendation, not acceptance of
those features or a promise to hold the release for them.
