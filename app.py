from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os

app = Flask(__name__)
app.secret_key = "secret123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    return sqlite3.connect(DB_PATH)

def create_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        title TEXT,
        amount REAL,
        category TEXT,
        date TEXT
    )
    """)

    conn.commit()
    conn.close()

@app.route("/", methods=["GET","POST"])
def home():
    if "user" in session:
        conn = get_db()
        cur = conn.cursor()

        month = request.form.get("month")

        if month:
            cur.execute("SELECT * FROM expenses WHERE user=? AND date LIKE ?", (session["user"], f"{month}%"))
        else:
            cur.execute("SELECT * FROM expenses WHERE user=?", (session["user"],))

        rows = cur.fetchall()

        data = []
        for r in rows:
            data.append({
                "id": r[0],
                "title": r[2],
                "amount": r[3],
                "category": r[4],
                "date": r[5]
            })

        total = sum([d["amount"] for d in data])

        return render_template("index.html", data=data, total=total)

    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=?", (user,))
        data = cur.fetchone()

        if data and check_password_hash(data[1], pwd):
            session["user"] = user
            return redirect("/")

    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        hashed = generate_password_hash(pwd)

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users VALUES (?, ?)", (user, hashed))
        conn.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/add", methods=["POST"])
def add():
    title = request.form["title"]
    amount = request.form["amount"]
    category = request.form["category"]
    date = request.form["date"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (user,title,amount,category,date) VALUES (?,?,?,?,?)",
        (session["user"], title, amount, category, date)
    )
    conn.commit()

    return redirect("/")

@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    return redirect("/")

@app.route("/edit/<int:id>")
def edit(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE id=?", (id,))
    r = cur.fetchone()

    data = {
        "id": r[0],
        "title": r[2],
        "amount": r[3],
        "category": r[4],
        "date": r[5]
    }

    return render_template("edit.html", data=data)

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    title = request.form["title"]
    amount = request.form["amount"]
    category = request.form["category"]
    date = request.form["date"]

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE expenses SET title=?,amount=?,category=?,date=? WHERE id=?",
        (title, amount, category, date, id)
    )
    conn.commit()

    return redirect("/")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)