#!/usr/bin/env python3
"""Dump the FastAPI app's current OpenAPI schema to ``backend/openapi.json``.

This is the canonical "what does the API actually look like right now"
artifact. The frontend ``npm run codegen`` step reads it and regenerates
typed bindings; the CI gate then asserts that the regeneration produces
no diff against the committed file. That keeps the frontend service
interfaces and the backend Pydantic schemas honest.

Run from the repo root:

    PYTHONPATH=backend backend/venv/bin/python backend/scripts/dump_openapi.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path


def _ensure_backend_on_path() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))


def main() -> int:
    _ensure_backend_on_path()

    # Importing main pulls in settings/database/lifespan but does not invoke
    # the lifespan context manager (TestClient does that), so this stays a
    # lightweight build-time operation.
    # Schema generation must not read an installation's DB/runtime configuration.
    with tempfile.TemporaryDirectory(prefix="scraper-openapi-") as temporary:
        os.environ['DATABASE_URL'] = f'sqlite:///{temporary}/schema.db'
        os.environ['LEGACY_DATABASE_URL'] = f'sqlite:///{temporary}/legacy.db'
        from main import app
        schema = app.openapi()
    target = Path(__file__).resolve().parents[1] / "openapi.json"
    target.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote OpenAPI schema to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
