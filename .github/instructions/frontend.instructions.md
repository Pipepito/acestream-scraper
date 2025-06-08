# Copilot/AI Instructions – Frontend (React, TypeScript)

Welcome, Copilot/AI! This is the React frontend for Acestream Scraper.  
Here’s how you should assist:

---

## 1. General Rules

- All code in TypeScript, with types everywhere.
- Use React functional components and hooks.
- Use a UI library (Material UI or Chakra UI as configured).
- Components should be modular, single-responsibility, and reusable.

---

## 2. Project Structure

- `src/api/` – Auto-generated API client (from backend OpenAPI).
- `src/components/` – Reusable UI components (tables, forms, dialogs, etc).
- `src/pages/` – Main route-level views.
- `src/utils/` – Helpers, hooks, context.

---

## 3. API Usage

- Always use the auto-generated API client for backend communication.
- Types from the API client must be used for all request/response objects.

---

## 4. Copilot/AI Prompts

- “Write a React component for a paginated, filterable channel table using MUI DataGrid.”
- “Add a hook to fetch channels from the API and display loading/error states.”
- “Generate a form for adding a new channel using the generated DTO type.”
- “Write a test for the PlaylistDownloadButton component using React Testing Library.”

---

## 5. Error Handling

- Show clear UI messages for API/network errors.
- Validate all user input before submission.

---

## 6. SPA Routing

- Assume the app is served from `/` (no subdirectory).
- All routes should fallback to the main App component for SPA navigation.

---

## 7. Formatting/Linting

- Use Prettier, ESLint. No untyped or `any` code.
- All props and state must be typed.

---

## 8. Testing

- All new components and hooks must have Jest/RTL tests.
- Test edge cases (no data, errors, interactive UI).

---

## 9. Documentation

- All exported components must have TypeScript doc comments.
- Update README and docs for new features.

---

**When implementing a new UI feature, start by describing the requirements and expected props/state in a comment.**