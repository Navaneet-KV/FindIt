from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "findit_secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------- DATABASE ----------
def connect():
    return sqlite3.connect("findit.db")


def init_db():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        location TEXT,
        description TEXT,
        image TEXT,
        status TEXT DEFAULT 'Available'
    )
    """)

    conn.commit()
    conn.close()


init_db()

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/dashboard")
        else:
            flash("Invalid email or password")

    return render_template("login.html")


# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = connect()
            cur = conn.cursor()
            cur.execute("INSERT INTO users(email,password) VALUES (?,?)", (email, password))
            conn.commit()
            conn.close()
            flash("Registration successful. Please login.")
            return redirect("/")
        except:
            flash("Email already exists")

    return render_template("register.html")


# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")


# ---------- ADD ITEM ----------
@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        name = request.form.get("name")
        category = request.form.get("category")
        location = request.form.get("location")
        description = request.form.get("description")

        image_file = request.files.get("image")
        image_name = None

        if image_file and image_file.filename:
            image_name = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))

        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items (name, category, location, description, image)
            VALUES (?, ?, ?, ?, ?)
        """, (name, category, location, description, image_name))
        conn.commit()
        conn.close()

        flash("Item added successfully")
        return redirect("/items")

    return render_template("add_item.html")


# ---------- VIEW ITEMS ----------
@app.route("/items")
def items():
    if "user" not in session:
        return redirect("/")

    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    conn.close()

    return render_template("items.html", items=items)


# ---------- REQUESTS (DUMMY FOR NOW) ----------
@app.route("/requests")
def requests_page():
    if "user" not in session:
        return redirect("/")

    data = []  # placeholder
    return render_template("requests.html", data=data)


# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
