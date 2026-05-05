"""
Database table creation script for Acestream Scraper v2
"""
from app.config.database import engine, Base
from app.models.models import (
    ScrapedURL, 
    AcestreamChannel, 
    EPGSource, 
    TVChannel, 
    EPGChannel, 
    EPGProgram, 
    EPGStringMapping, 
    Setting
)

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
