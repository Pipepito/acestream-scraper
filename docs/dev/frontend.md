# Frontend Development (React, TypeScript, Copilot/AI)

## Prerequisites

- Node.js 20+ (ARM64/x86_64 compatible)
- npm or yarn
- Copilot/AI plugin for your IDE
- (Optional) orval or openapi-generator-cli for auto-generating API client

## Repository Structure

```
frontend/
├── src/
│   ├── api/            # Generated API client (from backend OpenAPI)
│   ├── components/     # Reusable UI components
│   ├── pages/          # Route-level views
│   ├── utils/          # Helpers, hooks, context
│   ├── App.tsx
│   └── index.tsx
├── public/
├── Dockerfile
├── package.json
└── tsconfig.json
```

## Setup

```bash
cd frontend
npm install
npm run dev
```

## Copilot/AI Usage

- Use JSDoc/type annotations for all props and exports.
- Write a short comment above each component’s main function for Copilot/AI.
- Use the generated API client for all backend communication (see below).

## API Client Generation

- After backend API changes, regenerate the API client:
  - Use [orval](https://orval.dev/) or `openapi-generator-cli`:
    - `npx orval --config orval.config.js`
    - or
    - `openapi-generator-cli generate ...`
- Always use the generated types/hooks in your components.

## Example: Adding a New UI Feature

1. Use Copilot to scaffold a new component (describe props and state).
2. Use the generated API client to fetch/update data.
3. Add the component to a page or layout.
4. Write a test (Jest/React Testing Library).

## Testing

```bash
npm test
```

---

**See [`docs/architecture/api-structure.md`](../architecture/api-structure.md) for DTOs and API contract.**