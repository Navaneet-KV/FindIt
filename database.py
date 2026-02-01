import sqlite3

DB_NAME = "findit.db"

def connect():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = connect()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        otp TEXT
    )
    """)

    # ITEMS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        location TEXT,
        description TEXT,
        image TEXT,
        status TEXT,
        holder_id TEXT
    )
    """)

    # REQUESTS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        requester_email TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()
