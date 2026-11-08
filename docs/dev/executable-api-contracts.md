# Executable API contracts

FastAPI/Pydantic remains the source for `backend/openapi.json` and the generated
TypeScript declarations. `scripts/ci/run_v2_test_suite.sh --profile full` regenerates
both and rejects drift before running the complete application tests.

`frontend/src/__tests__/ServiceContracts.test.ts` calls production services through
an isolated HTTP listener. The captured method, URL, headers and serialized body
are checked by `backend/scripts/validate_api_contracts.py` using maintained
`openapi-core` OpenAPI 3.1 validation. Current coverage includes 35 requests across
channels, recordings, setup, sources, guides, events, Telegram, media servers,
tuner, saved searches and playback/notification settings. This is an explicit coverage subset,
not a claim that every operation has consumer coverage.

Consumer schemas close declared objects to catch ignored write fields while
retaining intentionally extensible maps. This test-only transformation does not
change backend compatibility. Tests preserve null, empty, omitted, zero and false
values; Telegram response metadata and creation-only history are excluded from
updates. Its administrative header never travels with unrelated service calls.

`backend/tests/contracts/test_openapi_wire.py` validates real endpoint responses,
including permission, conflict and validation outcomes. Telegram's synthetic
transport suite additionally validates successful status/login/preview and redacted
failure responses. Negative contracts reject wrong routes/methods, missing/extra/
invalid fields, response status/body/media-type drift and missing Telegram tokens.

Downloads use their actual media types. XMLTV and CSV must not declare a JSON
response. ZIP downloads use an OpenAPI 3.1 media-type declaration without applying
a JSON string schema to raw bytes, as specified by the
[OpenAPI binary format guidance](https://spec.openapis.org/registry/format/binary).
The provider tests separately parse XML/CSV/ZIP and assert format structure,
attachment headers, privacy/cache behavior and rejection of a JSON content type.
Streaming ownership, disconnect cleanup, recording priority and authorization
remain separate semantic/runtime tests; schema validation cannot prove them.

Run focused contracts from the repository root:

```sh
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/contracts/test_openapi_wire.py backend/tests/test_telegram_sources.py
npm --prefix frontend test -- --runInBand ServiceContracts.test.ts
```

These tests use owned synthetic state and transport, never live Telegram accounts,
notification recipients, TV receivers or production catalogue data. Full completion
still requires the repository's complete validation and acceptance requirements.
