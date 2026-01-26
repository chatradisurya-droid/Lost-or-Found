import sqlite3
import os

DB_NAME = "campus_lost_found.db"

def force_create_tables():
    print(f"⏳ Connecting to {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. DELETE OLD TABLES (Clean Slate)
    print("🗑️ Deleting old tables...")
    c.execute("DROP TABLE IF EXISTS items")
    c.execute("DROP TABLE IF EXISTS users")
    
    # 2. CREATE USERS TABLE (Now with 'coins' column!)
    print("🔨 Creating Users table (with Coins)...")
    c.execute('''
        CREATE TABLE users (
            email TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            coins INTEGER DEFAULT 0
        )
    ''')
    
    # 3. CREATE ITEMS TABLE
    print("🔨 Creating Items table...")
    c.execute('''
        CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT,
            item_name TEXT,
            location TEXT,
            description TEXT,
            sensitivity TEXT,
            contact_info TEXT,
            email TEXT,
            image_blob BLOB,
            image_hash TEXT,
            status TEXT DEFAULT 'OPEN',
            is_visible INTEGER DEFAULT 1,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ SUCCESS! Database reset. You can now run 'streamlit run app.py'")

if __name__ == "__main__":
    force_create_tables()