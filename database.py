import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "lost_found.db"

def init_db():
    """Initializes the database tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY, 
                    name TEXT, 
                    password TEXT,
                    coins INTEGER DEFAULT 100
                )''')
    
    # Create Items Table
    # Added 'image_hash' column for the new AI features
    c.execute('''CREATE TABLE IF NOT EXISTS items (
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
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'OPEN',
                    is_active BOOLEAN DEFAULT 1
                )''')
    
    # Check if 'image_hash' exists (for users upgrading from old version)
    try:
        c.execute("SELECT image_hash FROM items LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE items ADD COLUMN image_hash TEXT")
        
    conn.commit()
    conn.close()

# --- USER FUNCTIONS ---
def add_user(email, name, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (email, name, password) VALUES (?, ?, ?)", 
                  (email, name, password))
        conn.commit()
        conn.close()
        return "SUCCESS"
    except sqlite3.IntegrityError:
        return "EXISTS"

def verify_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, coins FROM users WHERE email = ? AND password = ?", (email, password))
    user = c.fetchone()
    conn.close()
    return user

def get_user_coins(email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE email = ?", (email,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def get_all_users():
    """For Admin Panel to list users"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT email, name, coins FROM users", conn)
    conn.close()
    return df

def delete_user(email):
    """For Admin Panel to delete a user"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE email = ?", (email,))
    # Also delete their posts
    c.execute("DELETE FROM items WHERE email = ?", (email,))
    conn.commit()
    conn.close()

# --- ITEM FUNCTIONS ---
def add_item(report_type, name, location, description, sensitivity, contact, email, img_blob, img_hash):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO items 
                 (report_type, item_name, location, description, sensitivity, contact_info, email, image_blob, image_hash) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (report_type, name, location, description, sensitivity, contact, email, img_blob, img_hash))
    new_id = c.lastrowid
    
    # Reward User 10 Coins for posting
    c.execute("UPDATE users SET coins = coins + 10 WHERE email = ?", (email,))
    
    conn.commit()
    conn.close()
    return new_id

def check_duplicate_post(email, r_type, name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""SELECT id FROM items 
                 WHERE email=? AND report_type=? AND item_name=? AND is_active=1""", 
              (email, r_type, name))
    found = c.fetchone()
    conn.close()
    return found is not None

def get_all_active_items():
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM items WHERE is_active = 1 ORDER BY timestamp DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_user_history(email):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT * FROM items WHERE email = ? ORDER BY timestamp DESC"
    df = pd.read_sql(query, conn, params=(email,))
    conn.close()
    return df

def soft_delete_item(item_id):
    """Marks item as inactive instead of deleting it."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE items SET is_active = 0, status = 'DELETED' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

# --- ADMIN FUNCTIONS ---
def get_admin_all_items():
    """
    Fetches ALL items (including deleted ones) for the Admin Panel.
    This fixes the error by ensuring a fresh connection is used.
    """
    conn = sqlite3.connect(DB_NAME)  # <--- This was the missing fix
    query = "SELECT * FROM items ORDER BY timestamp DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df
