# Channel Management Improvement Coding Prompt

You are a coding assistant tasked with implementing a robust, decoupled channel management system for the acestream-scraper project (V2). Your work must follow the detailed requirements and migration plan described in `channel_management_improvement_plan.md`.

## Objective

- Enable independent management of Acestream channels and TV channels.
- Support assignment of multiple Acestream channels to a single TV channel.
- Ensure playlist generation from Acestream channels, with optional TV channel/group filtering.
- Complete the migration from V1 patterns to a modern, maintainable architecture.

---

## Requirements

### 1. Backend

- Review and update models in `backend/app/models/models.py` for correct relationships.
- Ensure `AcestreamChannel.tv_channel_id` is nullable and supports many-to-one.
- Expose CRUD endpoints for both AcestreamChannel and TVChannel.
- Implement endpoints for assigning/unassigning Acestream channels to TV channels, and for listing all Acestream channels for a given TV channel.
- Update `playlist_service.py` to support filtering by TV channel/group and allow playlist download by TV channel/group.
- Update `channel_service.py` and `search_service.py` to support robust assignment logic.
- Create migration scripts if needed to decouple legacy channel data.

### 2. Frontend

- Split the current “Channels” page into:
  - `src/pages/AcestreamChannels.tsx` for Acestream channel management
  - `src/pages/TVChannels.tsx` for TV channel management
- Update navigation to allow easy switching between these pages.
- Implement assignment UX in both pages (dropdown, modal, or bulk assignment).
- In TV channel detail, show all assigned Acestream channels and allow management.
- In Acestream channel detail, allow assignment to a TV channel.
- Allow playlist download from Acestream channels page, with optional TV channel/group filter.

### 3. Testing

- Add backend tests for assignment logic, playlist generation, and CRUD for both models.
- Add frontend tests for new pages, assignment flows, and playlist download.

### 4. Documentation

- Update `docs/` with:
  - This prompt (`channel_management_improvement_prompt.md`)
  - The migration plan (`channel_management_improvement_plan.md`)
  - API and UX documentation for new flows

---

## Output Format

- All code must be production-ready, well-documented, and tested.
- Use clear commit messages referencing the plan and prompt.
- Document any architectural or UX decisions in the migration plan.

---

## References

- `docs/migration/channel_management_improvement_plan.md`: The full migration and improvement plan
- `backend/app/models/models.py`: Data models
- `backend/app/services/playlist_service.py`: Playlist logic
- `backend/app/services/channel_service.py`: Channel CRUD and assignment
- `backend/app/services/search_service.py`: Search/import logic
- `frontend/src/pages/Channels.tsx`: Current Acestream channel management page
- `frontend/src/pages/TVChannels.tsx` (to be created): TV channel management page
- `frontend/src/pages/AcestreamChannels.tsx` (to be created): Acestream channel management page

---

## Notes

- Follow the plan in `channel_management_improvement_plan.md` step by step.
- If you encounter ambiguity, document your assumptions and decisions in the plan.
- Prioritize maintainability, clarity, and test coverage.
