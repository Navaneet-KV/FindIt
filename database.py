import sqlite3

def connect():
    return sqlite3.connect("findit.db")

def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        location TEXT,
        description TEXT,
        image TEXT,
        status TEXT,
        holder_id INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        requester_id INTEGER,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()
