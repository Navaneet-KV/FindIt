from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session, flash
from database import connect, init_db
from models import LostItem
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = "findit_super_secret_key"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize database
init_db()

# ---------------- LOGIN REQUIRED DECORATOR ----------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password, role FROM users WHERE username=?",
            (username,)
        )
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["role"] = user[3]
            return redirect("/dashboard")
        else:
            flash("Invalid username or password")

    return render_template("login.html", title="FindIt")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = connect()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users(username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
        except:
            flash("Username already exists")
            conn.close()
            return redirect("/register")

        conn.close()
        return redirect("/")

    return render_template("register.html", title="FindIt")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT username, role FROM users WHERE id=?",
        (session["user_id"],)
    )
    user = cur.fetchone()
    conn.close()

    return render_template(
        "dashboard.html",
        user_name=user[0],
        role=user[1]
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")


# ---------------- ADD ITEM ----------------
@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        image_file = request.files.get("image")
        image_name = ""

        if image_file and image_file.filename != "":
            image_name = image_file.filename
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_name)
            image_file.save(image_path)

        item = LostItem(
            request.form["item_name"],
            request.form["category"],
            request.form["location"],
            request.form["description"],
            image_name,
            session["user_id"]
        )

        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items(name, category, location, description, image, status, holder_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item.name,
            item.category,
            item.location,
            item.description,
            item.image,
            item.status,
            item.holder_id
        ))
        conn.commit()
        conn.close()

        return redirect("/items")

    return render_template("add_item.html", title="FindIt")


# ---------------- VIEW ITEMS ----------------
@app.route("/items")
@login_required
def items():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    conn.close()

    return render_template("items.html", items=items, title="FindIt")


# ---------------- VIEW REQUESTS ----------------
@app.route("/requests")
@login_required
def view_requests():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            requests.id,
            items.name,
            requests.status
        FROM requests
        JOIN items ON requests.item_id = items.id
    """)

    data = cur.fetchall()
    conn.close()

    return render_template("requests.html", data=data)


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
