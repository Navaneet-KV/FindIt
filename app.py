from flask import Flask, render_template, request, redirect, session
from database import connect, init_db
from models import LostItem
import os

app = Flask(__name__)
app.secret_key = "findit_secret"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

init_db()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html", title="FindIt")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (request.form["username"], request.form["password"])
        )
        conn.commit()
        conn.close()
        return redirect("/")
    return render_template("register.html", title="FindIt")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", title="FindIt")


@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        image_file = request.files["image"]
        image_name = image_file.filename
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_name)
        image_file.save(image_path)

        item = LostItem(
            request.form["name"],
            request.form["category"],
            request.form["location"],
            request.form["description"],
            image_name,
            session["user_id"]
        )

        conn = connect()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO items(name,category,location,description,image,status,holder_id)
        VALUES (?,?,?,?,?,?,?)
        """, (item.name, item.category, item.location,
              item.description, item.image, item.status, item.holder_id))
        conn.commit()
        conn.close()
        return redirect("/items")

    return render_template("add_item.html", title="FindIt")


@app.route("/items")
def items():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM items")
    items = cur.fetchall()
    conn.close()
    return render_template("items.html", items=items, title="FindIt")

if __name__ == "__main__":
    app.run(debug=True)

import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

