# Migration Strategy Guide

This document outlines our approach to rewriting the Acestream Scraper application while maintaining compatibility and enabling a smooth transition from the current Flask-RESTX application to the new FastAPI + React stack.

## Phase 1: Setup and Infrastructure

### 1.1 Project Structure
```
acestream-scraper/          # Main repository
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/            # API routers
│   │   ├── core/           # Core settings, security
│   │   ├── dtos/           # Pydantic models
│   │   ├── models/         # SQLAlchemy models
│   │   ├── repositories/   # Data access layer
│   │   ├── services/       # Business logic 
│   │   ├── scrapers/       # Scraper implementations
│   │   ├── tasks/          # Background tasks
│   │   ├── utils/          # Helper utilities
│   │   ├── static/         # Frontend build output
│   │   └── main.py         # FastAPI entry point
│   ├── tests/              # Test suite
│   └── requirements.txt
├── frontend/               # React application  
│   ├── src/
│   │   ├── api/            # Generated API client
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── context/        # React context providers
│   │   └── utils/          # Helper utilities
│   └── package.json
└── docker-compose.yml      # Unified deployment
```

### 1.2 Initial Setup Tasks
- Initialize FastAPI application skeleton with SQLAlchemy, Alembic migrations, Poetry for dependencies
- Set up Docker build configuration for multi-arch support (x86_64 and arm64)
- Setup React application with TypeScript, router, API client generation
- Configure CI/CD pipeline for testing and releases

## Phase 2: Data Model Migration

### 2.1 Model Conversion
Convert SQLAlchemy models to modern, typed versions:

```python
# OLD MODEL
class AcestreamChannel(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(256))
    # ...other fields...

# NEW MODEL
class AcestreamChannel(Base):
    __tablename__ = "acestream_channels"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    # ...other fields with proper type hints...
```

### 2.2 DTO Creation
Create corresponding Pydantic schemas:

```python
class ChannelBaseDTO(BaseModel):
    """Base DTO for channel data."""
    name: str
    group: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    
class ChannelCreateDTO(ChannelBaseDTO):
    """DTO for channel creation."""
    id: str
    
class ChannelResponseDTO(ChannelBaseDTO):
    """DTO for channel response."""
    id: str
    is_online: bool = False
    last_checked: Optional[datetime] = None
    epg_update_protected: bool = False
    
    class Config:
        orm_mode = True
```

### 2.3 Database Migration
- Create Alembic migrations for any schema changes
- Implement data migration utility for transferring data from old to new format

## Phase 3: API Implementation 

### 3.1 Core Controllers (Priority Order)
1. Channel management
2. URL management and scraping
3. Playlist generation
4. EPG integration
5. Configuration and system endpoints
6. Health and status endpoints
7. WARP integration

### 3.2 Authentication (if needed)
- Implement OAuth2 with password flow or API key authentication
- Set up proper permissions and security utilities

### 3.3 OpenAPI Documentation
- Enhance all endpoint documentation for auto-generation
- Set up API client generation for the frontend

## Phase 4: Frontend Implementation

### 4.1 Component Library
- Build core UI component library with Material UI or similar framework
- Implement theming and responsive design 

### 4.2 Pages/Views (Priority Order)
1. Dashboard/Overview
2. Channel management
3. URL/source management  
4. Playlist generation
5. EPG configuration
6. System settings and health

### 4.3 State Management
- Implement React Query or similar for API state
- Context providers for application-wide state

## Phase 5: Integration Testing and Finalization

### 5.1 Testing
- End-to-end API tests
- UI component and integration tests
- Load testing for core functionality

### 5.2 Performance Optimization
- API response optimization
- Frontend bundle optimization
- Caching strategy for frequent operations

### 5.3 Documentation
- Update all user-facing documentation 
- Create comprehensive API reference
- Add in-app help and guidance

## Data Migration Guide

### Database Migration Script

```python
async def migrate_data(old_db_path: str, new_db_path: str):
    """Migrate data from old SQLite database to new database."""
    # Create engines
    old_engine = create_engine(f"sqlite:///{old_db_path}")
    new_engine = create_engine(f"sqlite:///{new_db_path}")
    
    # Setup session factories
    old_session = sessionmaker(bind=old_engine)()
    async_session = async_sessionmaker(new_engine)
    
    # Migrate channels
    channels = old_session.query(OldAcestreamChannel).all()
    async with async_session() as session:
        for old_channel in channels:
            new_channel = NewAcestreamChannel(
                id=old_channel.id,
                name=old_channel.name,
                # Map all other fields
            )
            session.add(new_channel)
        await session.commit()
    
    # Migrate other tables...
```

## Rollback Strategy

In case of migration issues, we'll maintain these safeguards:

1. The old application will continue running in parallel during migration
2. Database backups will be created before migration
3. The new application will be deployed alongside the old one  
4. Only after full validation will we switch traffic to the new application
