from flask import Flask, render_template, request, redirect, session, flash
from database import connect, init_db
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "findit_secret"

# ================= CONFIG =================
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize DB
init_db()

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT password, role FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["user"] = email
            session["role"] = user[1]
            return redirect("/dashboard")

        flash("Invalid email or password")

    return render_template("login.html")


# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        try:
            conn = connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, password)
            )
            conn.commit()
            conn.close()
            flash("Registration successful")
            return redirect("/")
        except:
            flash("Email already exists")

    return render_template("register.html")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", role=session["role"])


# ================= ADD ITEM =================
@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        img = request.files.get("image")
        filename = None

        if img and img.filename:
            filename = secure_filename(img.filename)
            img.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items
            (name, category, location, description, image, owner_email, owner_mobile)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form["name"],
            request.form["category"],
            request.form["location"],
            request.form["description"],
            filename,
            session["user"],
            request.form["mobile"]
        ))
        conn.commit()
        conn.close()

        return redirect("/items")

    return render_template("add_item.html")


# ================= VIEW + SEARCH ITEMS =================
@app.route("/items")
def items():
    if "user" not in session:
        return redirect("/")

    search = request.args.get("search", "")
    category = request.args.get("category", "")

    conn = connect()
    cur = conn.cursor()

    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")

    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")

    cur.execute(query, params)
    items = cur.fetchall()
    conn.close()

    return render_template("items.html", items=items, user=session["user"])


# ================= INSTANT CLAIM (NO ADMIN) =================
@app.route("/request_claim/<int:item_id>")
def request_claim(item_id):
    if "user" not in session:
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    # Check item
    cur.execute(
        "SELECT owner_email, status FROM items WHERE id=?",
        (item_id,)
    )
    item = cur.fetchone()

    if not item:
        conn.close()
        return redirect("/items")

    owner_email, status = item

    # ❌ Cannot claim own item or already claimed
    if owner_email == session["user"] or status == "Claimed":
        conn.close()
        return redirect("/items")

    # ✅ Mark item as claimed instantly
    cur.execute("""
        UPDATE items
        SET status='Claimed',
            claimed_by=?,
            claimed_at=?
        WHERE id=?
    """, (
        session["user"],
        datetime.now().strftime("%d %b %Y, %I:%M %p"),
        item_id
    ))

    # ✅ Log request history
    cur.execute("""
        INSERT INTO requests (item_id, requester_email, status)
        VALUES (?, ?, 'Claimed')
    """, (item_id, session["user"]))

    conn.commit()
    conn.close()

    return redirect("/items")


# ================= VIEW REQUESTS =================
@app.route("/requests")
def requests_page():
    if "user" not in session:
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    if session["role"] == "admin":
        cur.execute("""
            SELECT requests.id, items.name, requests.requester_email, requests.status
            FROM requests
            JOIN items ON items.id = requests.item_id
            ORDER BY requests.id DESC
        """)
    else:
        cur.execute("""
            SELECT requests.id, items.name, requests.requester_email, requests.status
            FROM requests
            JOIN items ON items.id = requests.item_id
            WHERE items.owner_email=?
            ORDER BY requests.id DESC
        """, (session["user"],))

    data = cur.fetchall()
    conn.close()

    return render_template("requests.html", data=data)


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
