import sqlite3

def connect():
    return sqlite3.connect("findit.db")

def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        otp TEXT
    )
    """)

    conn.commit()
    conn.close()
