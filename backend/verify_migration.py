import sqlite3
import os

db_path = './config/scraper.db'
if os.path.exists(db_path):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f'Found {len(tables)} tables in v2 database:')
        for table in tables:
            table_name = table[0]
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            print(f'  {table_name}: {count} rows')
            
        # Check a few sample records from key tables
        print("\nSample data:")
        
        # Check acestream channels
        cursor.execute("SELECT id, name, 'group' as group_name FROM acestream_channels LIMIT 3")
        channels = cursor.fetchall()
        print(f"\nAcestream channels (first 3):")
        for ch in channels:
            print(f"  ID: {ch[0]}, Name: {ch[1]}, Group: {ch[2]}")
            
        # Check TV channels
        cursor.execute("SELECT id, name, category FROM tv_channels LIMIT 3")
        tv_channels = cursor.fetchall()
        print(f"\nTV channels (first 3):")
        for ch in tv_channels:
            print(f"  ID: {ch[0]}, Name: {ch[1]}, Category: {ch[2]}")
            
        # Check EPG programs
        cursor.execute("SELECT title, start_time, end_time FROM epg_programs LIMIT 3")
        programs = cursor.fetchall()
        print(f"\nEPG programs (first 3):")
        for prog in programs:
            print(f"  Title: {prog[0]}, Start: {prog[1]}, End: {prog[2]}")
            
        # Check settings
        cursor.execute("SELECT key, value FROM settings")
        settings = cursor.fetchall()
        print(f"\nSettings:")
        for setting in settings:
            print(f"  {setting[0]}: {setting[1]}")
            
else:
    print('V2 database not found')
