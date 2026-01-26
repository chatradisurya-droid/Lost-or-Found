import sqlite3
import pandas as pd

DB_NAME = "campus_lost_found.db"

# --------------------------------------------------
# DATABASE INIT
# --------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Users Table (Stores login info & coins)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            coins INTEGER DEFAULT 0
        )
    """)
    
    # 2. Items Table (Stores Lost & Found reports)
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
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
    """)
    conn.commit()
    conn.close()

# --------------------------------------------------
# USER MANAGEMENT
# --------------------------------------------------
def add_user(email, username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # Check if user already exists
        c.execute("SELECT email FROM users WHERE email=?", (email,))
        if c.fetchone(): return "EXISTS"
        
        # Create new user with 0 coins
        c.execute("INSERT INTO users (email, username, password, coins) VALUES (?, ?, ?, 0)", (email, username, password))
        conn.commit()
        return "SUCCESS"
    except Exception as e: return str(e)
    finally: conn.close()

def verify_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Fetch username AND coins for session state
    c.execute("SELECT username, coins FROM users WHERE email=? AND password=?", (email, password))
    row = c.fetchone()
    conn.close()
    return row if row else None # Returns (username, coins)

def get_user_coins(email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE email=?", (email,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def reward_user(email, amount=2):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET coins = coins + ? WHERE email=?", (amount, email))
    conn.commit()
    conn.close()

# --------------------------------------------------
# ITEM MANAGEMENT
# --------------------------------------------------
def add_item(report_type, item_name, location, description, sensitivity, contact, email, image_blob, image_hash):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO items (report_type, item_name, location, description, sensitivity, contact_info, email, image_blob, image_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (report_type, item_name, location, description, sensitivity, contact, email, image_blob, image_hash))
    item_id = c.lastrowid
    conn.commit()
    conn.close()
    return item_id

def get_all_active_items():
    """Fetch items that are OPEN and Visible (for Home Feed)"""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM items WHERE status='OPEN' AND is_visible=1 ORDER BY timestamp DESC", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

def get_user_history(user_email):
    """Fetch history for a specific logged-in user"""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM items WHERE email=? ORDER BY timestamp DESC", conn, params=(user_email,))
    except: df = pd.DataFrame()
    conn.close()
    return df

def soft_delete_item(item_id):
    """User deletes their own item (Hidden from feed)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # ENSURE THIS IS ON ONE LINE
    c.execute("UPDATE items SET is_visible=0, status='DELETED_BY_USER' WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def resolve_item(item_id):
    """Mark item as CLAIMED (Successful Match)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # ENSURE THIS IS ON ONE LINE
    c.execute("UPDATE items SET status='CLAIMED', is_visible=0 WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def check_duplicate_post(email, report_type, item_name):
    """Simple spam prevention"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT item_name FROM items WHERE email=? AND report_type=? AND status='OPEN' AND is_visible=1", (email, report_type))
    rows = c.fetchall()
    conn.close()
    
    new_clean = item_name.lower().strip()
    for (old_name,) in rows:
        if new_clean in old_name.lower().strip(): return True
    return False

# --------------------------------------------------
# ADMIN PANEL FUNCTIONS
# --------------------------------------------------
def get_all_users():
    """Fetch all registered users for Admin View"""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT email, username, coins FROM users", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

def get_admin_all_items():
    """Fetch ABSOLUTELY EVERY item (Active, Claimed, Deleted) for Admin"""
    conn = sqlite3.connect(DB_NAME)
    try:
        df = pd.read_sql_query("SELECT * FROM items ORDER BY timestamp DESC", conn)
    except: df = pd.DataFrame()
    conn.close()
    return df

def delete_user(email):
    """Admin capability to ban/delete a user and their data"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM users WHERE email=?", (email,))
        c.execute("DELETE FROM items WHERE email=?", (email,)) # Delete their posts too
        conn.commit()
    except: pass
    finally: conn.close()