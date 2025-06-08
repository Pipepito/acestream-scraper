# Acestream Scraper v2

This is a complete rewrite of the Acestream Scraper application using modern technologies.

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- Pydantic
- aiohttp
- BeautifulSoup

### Frontend
- React with TypeScript (strict TypeScript only, no JavaScript files)
- Material UI
- React Query
- React Router

## Directory Structure

```
v2/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/
│   │   │   │   ├── channels.py
│   │   │   │   ├── scrapers.py
│   │   │   │   └── epg.py
│   │   │   └── api.py
│   │   ├── config/
│   │   │   ├── database.py
│   │   │   └── settings.py
│   │   ├── models/
│   │   │   ├── models.py
│   │   │   └── url_types.py
│   │   ├── repositories/
│   │   │   └── channel_repository.py
│   │   ├── scrapers/
│   │   │   ├── base.py
│   │   │   ├── http.py
│   │   │   ├── zeronet.py
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   ├── channel.py
│   │   │   └── scraper.py
│   │   ├── services/
│   │   │   ├── m3u_service.py
│   │   │   └── scraper_service.py
│   │   └── utils/
│   ├── tests/
│   ├── main.py
│   └── requirements.txt
└── frontend/
    ├── public/
    ├── scripts/
    │   └── copy-build.ts
    ├── src/
    │   ├── components/
    │   │   └── NavBar.tsx
    │   ├── pages/
    │   ├── services/
    │   ├── hooks/
    │   ├── utils/
    │   ├── App.tsx
    │   ├── index.tsx
    │   └── theme.ts
    └── package.json
```

## Development Setup

### Backend

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the development server:
```bash
uvicorn main:app --reload
```

### Frontend

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm start
```

3. Build the frontend for production and copy to backend:
```bash
npm run build:backend
```

## Scraper Implementation

The scraper functionality is the core of the application and has been carefully preserved from the v1 implementation. The scrapers work as follows:

1. `BaseScraper`: Contains common functionality for all scrapers, including:
   - Acestream ID extraction from various sources
   - Channel name cleaning
   - M3U file processing

2. `HTTPScraper`: Specialized for scraping HTTP/HTTPS URLs
   - Handles regular websites
   - Processes direct M3U file links

3. `ZeronetScraper`: Specialized for scraping ZeroNet URLs
   - Handles ZeroNet's unique URL format
   - Uses internal ZeroNet service for content retrieval
   - Processes iframe content

The scrapers use asynchronous HTTP requests for better performance and include retry logic for handling transient failures.
