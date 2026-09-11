#!/usr/bin/env python3
import sqlite3
import os

def check_database(db_path, db_name):
    if not os.path.exists(db_path):
        print(f"{db_name} database does not exist: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scraped_urls';")
        table_exists = cursor.fetchone()
        print(f"{db_name} scraped_urls table exists: {bool(table_exists)}")
        
        if table_exists:
            # Get row count
            cursor.execute("SELECT COUNT(*) FROM scraped_urls;")
            row_count = cursor.fetchone()[0]
            print(f"{db_name} scraped_urls row count: {row_count}")
            
            # Get table schema
            cursor.execute("PRAGMA table_info(scraped_urls);")
            columns = cursor.fetchall()
            print(f"{db_name} scraped_urls columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Get sample data
            cursor.execute("SELECT * FROM scraped_urls LIMIT 3;")
            rows = cursor.fetchall()
            print(f"{db_name} sample data:")
            for row in rows:
                print(f"  {row}")
        
        conn.close()
    except Exception as e:
        print(f"Error checking {db_name}: {e}")

if __name__ == "__main__":
    print("Checking scraped_urls tables...")
    check_database("config/scraper.db", "V2")
    check_database("config/acestream.db.migrated", "V1")
