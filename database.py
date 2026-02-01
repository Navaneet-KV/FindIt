import sqlite3

DB_NAME = "findit.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = connect()
    cur = conn.cursor()

    # ---------------- USERS TABLE ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'student'
    )
    """)

    # ---------------- ITEMS TABLE ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        location TEXT,
        description TEXT,
        image TEXT,
        status TEXT DEFAULT 'found',
        holder_id INTEGER
    )
    """)

    # ---------------- REQUESTS TABLE ----------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        requester_id INTEGER,
        status TEXT DEFAULT 'pending'
    )
    """)

    conn.commit()
    conn.close()


# 🚀 Run automatically when app starts
init_db()
