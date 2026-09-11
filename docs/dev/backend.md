# Backend Development (FastAPI, Python, Copilot/AI)

## Prerequisites

- Python 3.11+ (ARM64/x86_64 compatible)
- [Poetry](https://python-poetry.org/) or `venv` + `pip`
- Docker (for full-stack, multi-arch builds)
- Git, Copilot/AI plugin for your IDE

## Repository Structure

```
backend/
├── app/
│   ├── api/          # FastAPI routers (per feature)
│   ├── core/         # Core settings, config, utils
│   ├── dtos/         # Pydantic schemas (DTOs)
│   ├── models/       # SQLAlchemy ORM models
│   ├── services/     # Scraper, playlist, EPG, etc.
│   ├── repositories/ # DB/data access
│   ├── static/       # React build output (served at /)
│   └── main.py       # FastAPI entrypoint
├── tests/            # pytest unit/integration tests
├── Dockerfile
└── requirements.txt
```

## Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Or, if using Poetry:
```bash
poetry install
poetry shell
```

## Running Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# React frontend will be available at /, API at /api/...
```

## Core Conventions

- **Type hints everywhere.**
- **One module per service/domain (scraper, playlist, EPG, etc.).**
- **Every request/response is a Pydantic DTO.**
- **All endpoints and DTOs are documented.**
- **Copilot/AI-friendly docstrings and inline comments.**

## Copilot/AI Usage

- When adding/changing APIs, always update the DTO and docstrings first.
- Use Copilot to generate service/test skeletons from DTOs and endpoint signatures.

## Example: Adding a New Endpoint

1. Define your DTO in `app/dtos/`.
2. Write a service method in `app/services/`.
3. Add your API route in `app/api/`.
4. Update tests.
5. Run and check `/openapi.json`.

## Testing

```bash
pytest
# or with coverage
pytest --cov=app
```

---

**See [`docs/architecture/api-structure.md`](../architecture/api-structure.md) for example DTOs and API structure.**