from flask import Flask, render_template, request, redirect, session, flash
from database import connect, init_db
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = "findit_secret_key"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize DB
init_db()

# ---------------- LOGIN REQUIRED ----------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/dashboard")
        else:
            flash("Invalid email or password")

    return render_template("login.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, password)
            )
            conn.commit()
            conn.close()
            flash("Registration successful. Please login.")
            return redirect("/")
        except:
            flash("Email already exists")

    return render_template("register.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# ---------------- ADD ITEM ----------------
@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        location = request.form["location"]
        description = request.form["description"]

        image_file = request.files.get("image")
        image_name = None

        if image_file and image_file.filename != "":
            image_name = image_file.filename
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))

        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items (name, category, location, description, image, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category, location, description, image_name, "Available"))
        conn.commit()
        conn.close()

        return redirect("/items")

    return render_template("add_item.html")


# ---------------- VIEW ITEMS ----------------
@app.route("/items")
@login_required
def items():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    conn.close()

    return render_template("items.html", items=items)


# ---------------- REQUESTS (FIXED ✅) ----------------
@app.route("/requests")
@login_required
def requests_page():
    # No logic yet, just show empty page
    data = []
    return render_template("requests.html", data=data)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
