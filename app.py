from flask import Flask, render_template, request, redirect, session, flash
from database import connect, init_db
import random
import smtplib

app = Flask(__name__)
app.secret_key = "findit_secret"

init_db()

# ---------------- EMAIL OTP FUNCTION ----------------
def send_otp(email, otp):
    sender = "YOUR_GMAIL@gmail.com"        # TODO: replace
    password = "APP_PASSWORD"              # TODO: replace

    message = f"Subject: FindIt OTP\n\nYour OTP for password reset is: {otp}"

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, email, message)

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

# ---------------- REGISTER (FIXED) ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
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
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form["email"]
        otp = str(random.randint(100000, 999999))

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()

        if not user:
            conn.close()
            flash("Email not registered")
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
        entered_otp = request.form["otp"]

        conn = connect()
        cur = conn.cursor()
        cur.execute("SELECT otp FROM users WHERE email=?", (email,))
        row = cur.fetchone()
        conn.close()

        if row and entered_otp == row[0]:
            return redirect("/reset_password")
        else:
            flash("Invalid OTP")

    return render_template("verify_otp.html")

# ---------------- RESET PASSWORD ----------------
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    email = session.get("reset_email")
    if not email:
        return redirect("/forgot")

    if request.method == "POST":
        new_password = request.form["password"]

        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET password=?, otp=NULL WHERE email=?",
            (new_password, email)
        )
        conn.commit()
        conn.close()

        session.pop("reset_email", None)
        flash("Password reset successful. Please login.")
        return redirect("/")

    return render_template("reset_password.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
