from flask import Flask, render_template, request, redirect, session, flash
from database import connect, init_db
from functools import wraps
import os
import random

app = Flask(__name__)
app.secret_key = "findit_secret"

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
        email = request.form["username"]
        password = request.form["password"]

        try:
            conn = connect()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users(email, password) VALUES (?, ?)",
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

        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items (name, category, location, description, image, status, holder_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name, category, location, description, None, "Available", session["user"]
        ))
        conn.commit()
        conn.close()

        flash("Item added successfully")
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


# ---------------- REQUESTS (EMPTY FOR NOW) ----------------
@app.route("/requests")
@login_required
def requests_page():
    data = []  # no logic yet, prevents 500 error
    return render_template("requests.html", data=data)


# ---------------- FORGOT PASSWORD (OTP MOCK) ----------------
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form["email"]

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if not user:
            flash("Email not registered")
            return redirect("/forgot")

        # TEMP OTP (no email to avoid Render crash)
        otp = "123456"
        session["otp"] = otp
        session["reset_email"] = email

        flash("OTP sent (demo OTP: 123456)")
        return redirect("/verify_otp")

    return render_template("forgot.html")


# ---------------- VERIFY OTP ----------------
@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered = request.form["otp"]
        if entered == session.get("otp"):
            return redirect("/reset_password")
        else:
            flash("Invalid OTP")

    return render_template("verify_otp.html")


# ---------------- RESET PASSWORD ----------------
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_password = request.form["password"]
        email = session.get("reset_email")

        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password=? WHERE email=?",
            (new_password, email)
        )
        conn.commit()
        conn.close()

        session.clear()
        flash("Password reset successful")
        return redirect("/")

    return render_template("reset_password.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
