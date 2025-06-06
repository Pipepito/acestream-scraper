# Acestream Scraper Rewrite (AI-Driven, Fullstack)

This project is a **modern, AI-assisted rewrite** of Acestream Scraper, featuring:

- **FastAPI** backend (Python, async, fully typed, OpenAPI-first)
- **React** frontend (TypeScript, modular, reusable components)
- **Unified deployment:** Both frontend and backend served from the same endpoint for seamless SPA/API experience.
- **Multi-arch Docker:** x86_64 and arm64 support.
- **Copilot/AI-first workflow:** All code, docs, and DTOs are written and documented for maximum Copilot/codegen effectiveness.

---

## Quickstart

**Development:**

- See [`docs/dev/backend.md`](docs/dev/backend.md) for backend setup instructions (Python, Copilot, local dev).
- See [`docs/dev/frontend.md`](docs/dev/frontend.md) for frontend setup (React, TypeScript, Copilot).
- See [`docs/architecture/api-structure.md`](docs/architecture/api-structure.md) for how the API/DTOs are organized.
- See [`docs/architecture/deployment.md`](docs/architecture/deployment.md) for Docker, single-endpoint serving, and multi-arch notes.

**AI/LLM/Copilot Usage:**

- See [`docs/ai/copilot-guidelines.md`](docs/ai/copilot-guidelines.md) for using Copilot or other LLMs to extend or maintain the project.

---

## Project Structure

```
.
├── backend/             # FastAPI app
├── frontend/            # React app (TypeScript)
├── docs/                # Full project documentation
├── docker-compose.yml   # Unified dev/prod stack
└── README.md
```

---

## Key Features

- All scraper logic and core algorithms retained and modularized.
- Modern, reusable, testable Python and TypeScript code.
- Fully documented OpenAPI schema – auto-generates frontend API client.
- Responsive, feature-rich UI (React) with search, status, playlist, and configuration.
- ARM64-ready, efficient Docker builds.
- Designed for ongoing AI/Copilot-assisted development.

---

## Contributing

1. Read [`docs/ai/copilot-guidelines.md`](docs/ai/copilot-guidelines.md) to get the most out of Copilot/AI.
2. Use the provided scripts/linting/formatting tools.
3. All contributions (code, docs, or tests) must be type-annotated and documented.

---

## License

MIT License
