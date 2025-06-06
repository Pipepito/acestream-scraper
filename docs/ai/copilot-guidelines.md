# Copilot/AI Guidelines for This Project

This project is designed to be developed and maintained with GitHub Copilot and other AI code assistants. Following these guidelines will help you leverage AI effectively during the rewrite process.

---

## General Guidelines

- **Type everything:** Python (type hints), TypeScript (interfaces/types) for better code completion and error prevention.
- **Docstrings/comments:** Every class, function, endpoint, and DTO must have a clear docstring explaining purpose and usage.
- **Explain intent and contracts:** Write out what you want to accomplish in plain English before generating code.
- **Keep functions focused:** Each function/class should have a single responsibility for better maintainability.
- **Modular code:** Separate DTOs, services, routes, and utilities into their own files and folders.
- **Tests are first-class:** Use AI to generate and update tests with every feature.
- **Include examples:** When writing docstrings, include example usage to make code more self-documenting.
- **Error handling:** Explicitly handle all errors and edge cases in a consistent way.

---

## Effective AI Prompt Structure

1. **Provide context:** Briefly explain what you're working on and how this piece fits in.
2. **Be specific:** Clearly state what you need, including exact field names, types, and requirements.
3. **Reference existing code:** If relevant, reference existing patterns or code in the project.
4. **Specify format:** Mention the format you want (Python/TypeScript, specific libraries, etc.).
5. **Mention edge cases:** Note important edge cases or error conditions to handle.

---

## AI Prompt Examples

### Backend Development

#### Models and DTOs
```
"Create a Pydantic DTO for a channel with these fields:
- id: str
- name: str
- tvg_id: Optional[str]
- tvg_name: Optional[str]
- logo: Optional[str]
- group: Optional[str]
- is_online: bool (default: False)
- last_checked: Optional[datetime]

Include proper docstrings and example usage in the docstring.
Create a base class for common fields and extend it for request/response variants."
```

#### API Routes
```
"Generate a FastAPI route to list all channels with these features:
- Pagination (page number and size parameters)
- Optional filtering by online status, group, and name search
- Proper error handling for invalid parameters
- Comprehensive OpenAPI documentation
- Dependency injection for the channel service

Use async/await and follow our existing error handling pattern."
```

#### Services
```
"Create a channel service with methods for:
1. Finding channels by various criteria (online status, group, name pattern)
2. Checking if a channel is online by connecting to Acestream engine
3. Creating and updating channel information
4. Batch importing channels from URLs

The service should use our repository pattern and handle all edge cases.
Include logging for important operations."
```

### Frontend Development

#### Components
```
"Write a React component using TypeScript and Material UI for displaying a channel card:

Requirements:
- Show channel name, logo, group, and online status
- Display a colored dot based on online status (green for online, red for offline)
- Include timestamp of last status check
- Show buttons for: Check Status, Edit, Delete that call provided callbacks
- Support hover effects and selection state
- Be responsive (different layouts for mobile/desktop)

Follow our existing component patterns with proper prop types and documentation."
```

#### API Integration
```
"Create a React Query hook for fetching and managing channel data:

Requirements:
- Function to get all channels with filtering options
- Function to get a single channel by ID
- Function to update a channel
- Function to check channel status
- Function to delete a channel

Include proper error handling and loading states.
Use TypeScript for all types and follow our API structure."
```

#### Tests
```
"Write Jest tests for the ChannelCard component:

Include tests for:
1. Rendering with all required props
2. Displaying online vs offline states correctly
3. Button click handlers being called correctly
4. Responsive behavior
5. Edge cases (missing data, long text)

Use React Testing Library and follow our existing test patterns."
```

---

## Best Practices for Working with AI

1. **Iterate:** Don't expect perfect code on the first try. Ask for improvements or alternatives.
2. **Review carefully:** AI may introduce subtle bugs or make incorrect assumptions.
3. **Learn from the AI:** Pay attention to patterns and practices it introduces, which can improve your coding.
4. **Be explicit:** The more specific your instructions, the better the output will be.
5. **Document your approach:** Note how you solved problems so others can learn from your process.
6. **Split complex tasks:** Break down large features into smaller, manageable pieces for the AI.

---

## Copilot/AI Workflow

1. **Describe your feature or fix in a comment.**
2. **Let Copilot/AI generate the skeleton.**
3. **Review, refactor, and add typing/docstrings.**
4. **Write/verify tests.**
5. **Update documentation as needed.**

---

## Reviewing Copilot/AI Output

- Check for type safety and correct imports.
- Review for side effects and single-responsibility adherence.
- Ensure all classes/functions have docstrings.
- Always run/test before committing AI-generated code.

---

## Documentation/DTO Updates

- When adding new endpoints, always update the OpenAPI schema and DTO documentation.
- When updating models, describe changes in the PR or commit message.
- Keep documentation in sync with code changes.

---

---

## Linting/Formatting

- Use `black`, `flake8`, `isort` (Python) and `eslint`, `prettier` (TypeScript).
- Fix all linter warnings before merging.

---

**For more advanced AI usage, see `docs/architecture/api-structure.md` for DTO and endpoint design best practices.**