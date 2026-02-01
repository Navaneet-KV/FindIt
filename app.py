from flask import Flask, render_template, request, redirect, session, flash
from database import connect, init_db
from models import LostItem
from functools import wraps
import os
import random
import smtplib

app = Flask(__name__)
app.secret_key = "findit_secret"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

init_db()

# ---------------- LOGIN REQUIRED ----------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated

# ---------------- EMAIL OTP ----------------
def send_otp(email, otp):
    sender = "YOUR_GMAIL@gmail.com"        # CHANGE
    password = "APP_PASSWORD"              # CHANGE

    msg = f"Subject: FindIt OTP\n\nYour OTP is: {otp}"

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, email, msg)

# ---------------- LOGIN ----------------
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
            cur.execute("INSERT INTO users(email,password) VALUES (?,?)", (email, password))
            conn.commit()
            conn.close()
            flash("Registration successful")
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
        image = request.files["image"]
        filename = image.filename
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        item = LostItem(
            request.form["name"],
            request.form["category"],
            request.form["location"],
            request.form["description"],
            filename,
            session["user"]
        )

        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items(name, category, location, description, image, status, holder_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item.name, item.category, item.location,
            item.description, item.image, item.status, item.holder_id
        ))
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

# ---------------- REQUESTS ----------------
@app.route("/requests")
@login_required
def requests_page():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT requests.id, items.name, requests.status
        FROM requests
        JOIN items ON items.id = requests.item_id
    """)
    data = cur.fetchall()
    conn.close()

    return render_template("requests.html", data=data)

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form["email"]
        otp = str(random.randint(100000, 999999))

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        if not cur.fetchone():
            flash("Email not registered")
            conn.close()
            return redirect("/forgot")

        cur.execute("UPDATE users SET otp=? WHERE email=?", (otp, email))
        conn.commit()
        conn.close()

        send_otp(email, otp)
        session["reset_email"] = email
        return redirect("/verify_otp")

    return render_template("forgot.html")

# ---------------- VERIFY OTP ----------------
@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    email = session.get("reset_email")
    if not email:
        return redirect("/forgot")

    if request.method == "POST":
        entered = request.form["otp"]

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT otp FROM users WHERE email=?", (email,))
        real = cur.fetchone()[0]
        conn.close()

        if entered == real:
            return redirect("/reset_password")
        flash("Invalid OTP")

    return render_template("verify_otp.html")

# ---------------- RESET PASSWORD ----------------
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    email = session.get("reset_email")
    if not email:
        return redirect("/forgot")

    if request.method == "POST":
        password = request.form["password"]

        conn = connect()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=?, otp=NULL WHERE email=?", (password, email))
        conn.commit()
        conn.close()

        session.pop("reset_email", None)
        flash("Password reset successful")
        return redirect("/")

    return render_template("reset_password.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
