from flask import Flask, render_template, request, redirect, session, flash
from database import connect, init_db
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "findit_secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

init_db()

# ---------------- LOGIN ----------------
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


# ---------------- REGISTER ----------------
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


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", role=session["role"])


# ---------------- ADD ITEM ----------------
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


# ---------------- VIEW + SEARCH ITEMS ----------------
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
        query += " AND category=?"
        params.append(category)

    cur.execute(query, params)
    items = cur.fetchall()
    conn.close()

    return render_template("items.html", items=items, user=session["user"])


# ---------------- REQUEST CLAIM ----------------
@app.route("/request_claim/<int:item_id>")
def request_claim(item_id):
    if "user" not in session:
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    # Check item status & owner
    cur.execute("""
        SELECT owner_email, status FROM items WHERE id=?
    """, (item_id,))
    item = cur.fetchone()

    if not item:
        conn.close()
        return redirect("/items")

    owner_email, status = item

    # ❌ Cannot request own item or already claimed item
    if owner_email == session["user"] or status == "Claimed":
        conn.close()
        return redirect("/items")

    # ❌ Prevent duplicate requests
    cur.execute("""
        SELECT 1 FROM requests
        WHERE item_id=? AND requester_email=?
    """, (item_id, session["user"]))
    exists = cur.fetchone()

    if not exists:
        cur.execute("""
            INSERT INTO requests (item_id, requester_email)
            VALUES (?, ?)
        """, (item_id, session["user"]))
        conn.commit()

    conn.close()
    return redirect("/items")


# ---------------- OWNER APPROVES CLAIM ----------------
@app.route("/approve/<int:req_id>")
def approve(req_id):
    if "user" not in session:
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT items.id, items.owner_email, requests.requester_email
        FROM requests
        JOIN items ON items.id = requests.item_id
        WHERE requests.id=?
    """, (req_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return redirect("/dashboard")

    item_id, owner_email, requester_email = row

    # Only owner can approve
    if owner_email != session["user"]:
        conn.close()
        return redirect("/dashboard")

    # Mark item as claimed
    cur.execute("""
        UPDATE items
        SET status='Claimed',
            claimed_by=?,
            claimed_at=?
        WHERE id=?
    """, (
        requester_email,
        datetime.now().strftime("%d %b %Y, %I:%M %p"),
        item_id
    ))

    # Approve this request
    cur.execute("""
        UPDATE requests SET status='Approved' WHERE id=?
    """, (req_id,))

    # Reject all other requests for this item
    cur.execute("""
        UPDATE requests
        SET status='Rejected'
        WHERE item_id=? AND id!=?
    """, (item_id, req_id))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# ---------------- VIEW REQUESTS (OWNER + ADMIN) ----------------
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
        """)
    else:
        cur.execute("""
            SELECT requests.id, items.name, requests.requester_email, requests.status
            FROM requests
            JOIN items ON items.id = requests.item_id
            WHERE items.owner_email=?
        """, (session["user"],))

    data = cur.fetchall()
    conn.close()

    return render_template("requests.html", data=data)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
