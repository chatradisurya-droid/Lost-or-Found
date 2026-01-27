import sqlite3
import pandas as pd

DB_NAME = "campus_lost_found.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Users Table with Coins
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY, 
                    name TEXT, 
                    password TEXT,
                    coins INTEGER DEFAULT 100
                )''')
    # Items Table
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
    # Ensure Coins column exists (migration check)
    try:
        c.execute("SELECT coins FROM users LIMIT 1")
    except:
        c.execute("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 100")
        
    conn.commit()
    conn.close()

def add_user(email, name, password):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (email, name, password, coins) VALUES (?, ?, ?, 100)", 
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
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def add_item(report_type, name, location, description, sensitivity, contact, email, img_blob, img_hash):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Insert Item
    c.execute("""INSERT INTO items 
                 (report_type, item_name, location, description, sensitivity, contact_info, email, image_blob, image_hash) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (report_type, name, location, description, sensitivity, contact, email, img_blob, img_hash))
    new_id = c.lastrowid
    
    # REWARD COINS (+10)
    c.execute("UPDATE users SET coins = coins + 10 WHERE email = ?", (email,))
    
    conn.commit()
    conn.close()
    return new_id

def check_duplicate_post(email, r_type, name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM items WHERE email=? AND report_type=? AND item_name=? AND is_active=1", 
              (email, r_type, name))
    found = c.fetchone()
    conn.close()
    return found is not None

def get_all_active_items():
    conn = sqlite3.connect(DB_NAME)
    # Fetch all items to check history
    df = pd.read_sql("SELECT * FROM items WHERE is_active = 1 ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def get_user_history(email):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM items WHERE email = ? ORDER BY timestamp DESC", conn, params=(email,))
    conn.close()
    return df

def soft_delete_item(item_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE items SET is_active = 0, status = 'DELETED' WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
# Admin Functions
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT email, name, coins FROM users", conn)
    conn.close()
    return df

def get_admin_all_items():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM items ORDER BY timestamp DESC", conn)
    conn.close()
    return df

def delete_user(email):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE email = ?", (email,))
    c.execute("DELETE FROM items WHERE email = ?", (email,))
    conn.commit()
    conn.close()
