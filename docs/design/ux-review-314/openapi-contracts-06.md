# OpenAPI contract testing and design reference integrity

Review 06 · source pinned to `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`. The owner requested future contract tests against `openapi.json`, with one shared implementation for all styles. This session adds design reference checks only; it changes no application tests, dependencies, schema or CI configuration.

## Existing chain and observed limits

FastAPI/Pydantic → `backend/openapi.json` → `frontend/src/types/api-generated.ts` → shared frontend services. `backend/scripts/dump_openapi.py` generates the snapshot; frontend `npm run codegen` uses `openapi-typescript`. The inspected full-suite script regenerates both, but its explicit drift comparison checks generated TypeScript. Future work must compare the schema snapshot too.

The pinned schema is OpenAPI **3.1.0**, with **260 paths, 333 operations and 300 component schemas**. Existing focused backend contract tests cover selected responses and key sets; they are useful starting evidence, not a general schema conformance suite. Shared `apiClient.ts` already owns credentials, token/CSRF behavior and error handling. Three preset-specific clients would violate the design architecture.

The [machine-readable map](openapi-contract-map.json) records every available operation ID, parameters, request-body schema, responses and 130 design/resource bindings. All 473 field occurrences are inventoried; 24 currently have an exact explicit source-model property reference. The other fields include local/derived values, environment options and adapters whose transformations must be implemented and tested from the field/source specification. The checker does **not** infer a wire key from a label, nor claim those 449 entries are payload-validated.

Run:

```sh
python3 docs/design/ux-review-314/openapi_contracts.py --check --self-test
```

This checks pinned schema hash, operation existence, HTTP method, operation ID and referenced schema properties, plus three negative reference cases. It makes no requests. It is a reference-integrity check, not a hand-written partial JSON Schema validator. Synthetic prototype outcomes never demonstrate API success.

## Future executable contract suite

| Layer | Required test | Failure must mean | Owner |
|---|---|---|---|
| Schema drift | Generate fresh OpenAPI under isolated test configuration; compare canonical snapshot and generated TS against committed files | Unreviewed endpoint/schema drift blocks completion | #316/#324 |
| Consumer request | Exercise each shared service through its actual serializer; intercept method/path/query/header/content type/body and validate against an OpenAPI 3.1-capable validator | Wrong path, method, enum, missing field, unexpected body or coercion is rejected before a request is treated as valid | #318–#322 |
| Provider response | Run isolated FastAPI requests with synthetic DB/services; validate actual status, content type, headers and response body against the operation's declared response | An implementation returning undocumented shape/status fails | #315 and feature owner |
| Semantic contract | Independently assert auth/transport, last-admin, transaction isolation, atomic Add/Link/reorder, stale preview rejection, recording priority and media ownership | Schema-valid data cannot excuse incorrect behavior | #315/#318–#322 |
| Presentation parity | Run identical feature scenarios with each preset; compare outgoing requests, eligibility, state transitions and results | A style changes behavior or loses work | #316/#324 |
| Non-JSON / streaming | Separate contracts for playlists, XMLTV, diagnostics/downloads and media; bounded headers/status/stream lifecycle checks | JSON validation is not incorrectly applied to a binary or streaming response | #319/#320/#322 |

Use a maintained validator supporting OpenAPI 3.1 / JSON Schema 2020-12; evaluate compatibility during the separately authorized implementation. No tool/library selection or dependency installation is approved by this document. Avoid a second hand-maintained API model. Consumer fixtures should reference generated types but still validate runtime serialization; TypeScript alone cannot detect a wrong endpoint or ignored extra key.

For unknown keys, do not silently strengthen every provider model in one step. Validate consumer payloads against the intended declared fields, add a failing regression for ignored metadata, and separately review any backend `extra='forbid'` compatibility change. Test missing, null, empty, zero and false independently. Path parameters, repeated query values, API aliases and ASGI/reverse-proxy prefixes need explicit cases.

## Gaps requiring future application work

- **Authentication is incompletely described by the snapshot:** no global security declaration or security schemes. Real middleware/service restrictions remain authoritative; the schema's omission never means anonymous access is allowed. Document the existing auth/CSRF/transport contract accurately before relying on generated security tests. #318/#324.
- **Error responses are incomplete:** for example reorder declares 200/422 while source enforces stale/incomplete conflicts. Add accurate error schemas/status declarations and provider tests; do not weaken the behavior to match an incomplete document. #320/#324.
- **F15 source finding:** bulk stream metadata UI fields do not match `AcestreamChannelUpdate`, and the per-row callback can send the full selected batch repeatedly. Reproduce with isolated data before claiming a defect or fix. Capture the actual request count and unchanged/applied fields. #315/#320.
- **Now/next artwork gap:** `EPGProgram.image_url`, TV logos and explicit event artwork already exist. `GuideSlot`/TV now-next currently supplies title/start/end only. Rich programme cards need a reviewed use of an existing guide response or an additive batch-contract change with no N+1 lookup pattern. No image API is invented by the prototype. #319/#320.

General application slowdown remains unproven (#323). A correct schema and passing design checks do not establish performance, media behavior or production security.
