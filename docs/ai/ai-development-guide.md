# AI Development Guide for Acestream Scraper Rewrite

This document provides guidelines and examples for using AI assistants like GitHub Copilot to help with the rewrite of the Acestream Scraper application. Following these guidelines will help ensure that the AI can provide the most helpful assistance.

## Folder Structure and Organization

The v2 application is structured to be AI-friendly with clear separation of concerns:

```
v2/
├── app/                    # FastAPI application
│   ├── api/                # API routers
│   │   ├── channels.py     # Channel APIs
│   │   ├── playlists.py    # Playlist APIs
│   │   └── ...             # Other API modules
│   ├── core/               # Core functionality
│   │   ├── config.py       # Application configuration
│   │   ├── security.py     # Security utilities
│   │   └── dependencies.py # FastAPI dependencies
│   ├── dtos/               # Pydantic models for API
│   │   ├── channel.py      # Channel DTOs
│   │   ├── playlist.py     # Playlist DTOs
│   │   └── ...             # Other DTO modules
│   ├── models/             # SQLAlchemy models
│   │   ├── acestream_channel.py
│   │   ├── tv_channel.py
│   │   └── ...             # Other model modules
│   ├── repositories/       # Data access layer
│   │   ├── base.py         # Base repository class
│   │   ├── channel_repo.py # Channel repository
│   │   └── ...             # Other repositories
│   ├── services/           # Business logic
│   │   ├── channel_service.py
│   │   ├── playlist_service.py
│   │   └── ...             # Other service modules
│   └── main.py             # Application entry point
├── frontend/               # React application
└── tests/                  # Test suite
```

## AI Prompt Examples

### Backend Development

#### Creating a Model

```
Create a SQLAlchemy model for the AcestreamChannel class that maintains the same table structure as the current application. Use SQLAlchemy 2.0 style with type annotations. The model should have these fields:

- id (String, primary key)
- name (String)
- added_at (DateTime, default to UTC now)
- last_processed (DateTime, nullable)
- status (String, default to 'active')
- source_url (Text, nullable)
- scraped_url_id (Integer, foreign key to scraped_urls.id, nullable)
- group (String, nullable)
- logo (Text, nullable)
- tvg_id (String, nullable)
- tvg_name (String, nullable)
- m3u_source (Text, nullable)
- original_url (Text, nullable)
- is_online (Boolean, default to False)
- last_checked (DateTime, nullable)
- check_error (Text, nullable)
- epg_update_protected (Boolean, default to False)
- tv_channel_id (Integer, foreign key to tv_channels.id, nullable)
```

#### Creating a Repository

```
Create a ChannelRepository class that extends the BaseRepository for the AcestreamChannel model. Include methods for:

1. Finding a channel by ID
2. Finding channels by name pattern
3. Finding online channels
4. Finding channels by group
5. Finding channels that need status checking (last_checked older than X hours)
6. Updating a channel's online status
7. Batch creating channels from a list of channel data

Use async SQLAlchemy queries and proper error handling.
```

#### Creating a Service

```
Create a ChannelService class that handles the business logic for channel operations. The service should:

1. Use the ChannelRepository for data access
2. Include methods for CRUD operations
3. Include a method for checking a channel's online status by connecting to the Acestream engine
4. Include methods for batch operations like checking all channels
5. Use proper logging and error handling
6. Be designed for dependency injection through FastAPI
```

#### Creating an API Endpoint

```
Create a FastAPI router for channel operations with these endpoints:

1. GET /channels - List all channels with filtering options
2. GET /channels/{id} - Get a single channel by ID
3. POST /channels - Create a new channel
4. PUT /channels/{id} - Update a channel
5. DELETE /channels/{id} - Delete a channel
6. POST /channels/{id}/check - Check if a channel is online
7. POST /channels/check-all - Check all channels
8. GET /channels/status - Get status summary (count of online/offline channels)

Use proper request/response models, path parameters, query parameters, dependency injection, and OpenAPI documentation.
```

### Frontend Development

#### Creating a React Component

```
Create a React component for displaying a channel card with TypeScript props. The component should:

1. Display the channel name, logo, group, and online status
2. Show online status with a colored indicator (green for online, red for offline)
3. Show the last checked time
4. Include buttons for actions: check status, edit, and delete
5. Use Material UI components
6. Include proper TypeScript types for all props
7. Use React hooks where appropriate
```

#### Creating an API Client

```
Create a TypeScript API client for the channel endpoints using Axios. The client should:

1. Include methods for all channel API endpoints
2. Use TypeScript interfaces for request and response types
3. Handle error responses and provide appropriate error messages
4. Include request timeout handling
5. Support cancellation of requests
6. Use proper TypeScript typing
```

## Best Practices for AI-Assisted Development

1. **Be specific in your prompts** - Include details about the desired functionality, error handling, and edge cases.

2. **Provide context** - Mention related files or components that the AI should be aware of.

3. **Use iterative development** - Start with a basic implementation and then refine it with additional prompts.

4. **Review and test code thoroughly** - AI-generated code may need adjustments to work correctly in your specific context.

5. **Maintain consistent coding style** - Describe your preferred style in prompts (naming conventions, formatting, etc.)

## Example Workflow for Creating a New Feature

1. **Define the feature** - Clearly state what the feature should do and how it integrates with the rest of the application.

2. **Create backend components** - Models, repositories, services, and API endpoints.

3. **Create frontend components** - UI components, API clients, and state management.

4. **Test the feature** - Write unit tests and manually test the feature.

5. **Refine and optimize** - Improve error handling, performance, and user experience.

## Common Patterns

### Error Handling

```python
# Backend error handling pattern
try:
    result = await service.perform_operation()
    return result
except NotFoundException as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
except ValidationException as e:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                      detail="An unexpected error occurred")
```

### Repository Pattern

```python
# Repository pattern
class BaseRepository:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

class ChannelRepository(BaseRepository):
    async def find_by_id(self, channel_id: str) -> Optional[AcestreamChannel]:
        query = select(AcestreamChannel).where(AcestreamChannel.id == channel_id)
        result = await self.db_session.execute(query)
        return result.scalars().first()
```

### Dependency Injection

```python
# FastAPI dependency injection pattern
@router.get("/{channel_id}", response_model=ChannelResponseDTO)
async def get_channel(
    channel_id: str,
    channel_service: ChannelService = Depends(get_channel_service)
):
    channel = await channel_service.get_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel
```
