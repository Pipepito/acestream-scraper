"""
Database table creation script for Acestream Scraper v2
"""
from importlib import import_module

from app.config.database import engine, Base

# Importing the model hub registers every table on Base.metadata.
import_module("app.models.models")

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
