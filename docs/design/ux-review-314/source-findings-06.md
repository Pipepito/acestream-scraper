# Source evidence and unresolved application findings

Review 06, 7 November 2026. Application source: `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`. Local application base remains `7ccf16d383758aeeb78845e20e3716ddf97df10d`. Remote tips were rechecked without merging implementation into the design branch.

| ID / classification | Evidence and consequence | Disposition / owner |
|---|---|---|
| Observed recording opener defect | Prior read-only live audit captured private-HTTP `crypto.randomUUID` failure | Remains open #315. No application fix or fresh live reproduction in this session |
| Observed contrast / phone / slider defects | Prior light-success contrast, Network/pagination clipping and unnamed export sliders | Remain open #315/#317. New prototype passes do not fix the old application |
| SRC-F15 (source-only; historical document calls it F15) | `BulkOperations.tsx` per-row callback plus `AcestreamChannels.tsx` full-selection bulk call; category/country/language absent from `AcestreamChannelUpdate` | Isolated reproduction and actual request/payload regression required #315/#320. Do not confuse with historical prototype limitation F15 in fresh-audit.md |
| SRC-06-01 now/next artwork | `backend/app/schemas/channel.py` GuideSlot contains title/start/end; `frontend/src/hooks/useNowNext.ts` batches/refetches now-next. `EPGProgram.image_url`, channel logo and event image contracts already exist | Review existing guide response use or additive batch schema in future #319/#320. No invented image API or per-card unbounded fetch |
| SRC-06-02 OpenAPI auth description | `backend/openapi.json` 3.1 snapshot lacks security schemes/global security despite real access enforcement | Describe and test actual existing policies in future #318/#324. No anonymous-access inference |
| SRC-06-03 OpenAPI conflict description | Reorder snapshot describes 200/422; source includes stale/incomplete inventory conflict behavior | Add accurate declared errors and provider tests in future #320/#324; preserve atomic complete-catalogue transaction |
| Preserved new behavior | Online-only/Show all/refresh continuity; opt-in similar-name review; atomic manual/Search Add and Link; opt-in cleanup with separate schedule; tuner hiding | Source constraints retained in composed workflows and location map. No obsolete behavior restored |
| Corrected earlier design hypothesis | `GuideMatchingFields.tsx` and stream-check scope save immediately | Review 06 retains immediate save; older staged Save proposal withdrawn |
| Unproven performance hypothesis | No repeatable current application performance baseline collected | Remains unproven #323; static render speed and source loop inspection are not proof |

Backend support must be investigated through source review and isolated tests in a later authorized application session. The current design check validates operation references against a pinned schema but cannot demonstrate endpoints, queues, devices or media behavior. See [contract strategy](openapi-contracts-06.md).
