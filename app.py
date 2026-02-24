from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import sqlite3
from datetime import datetime, timedelta
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
#DATABASE = 'food.db'
import os 
if os.environ.get("RENDER"):
    DATABASE = '/data/food.db'
else:
    DATABASE = 'food.db'


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS food (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_name TEXT,
                ingredients TEXT,
                expiry_date TEXT,
                packed_status TEXT,
                allergy_info TEXT,
                is_free INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                email TEXT
            )
        ''')


@app.route('/', methods=["GET", "POST"])
def login():
    if request.method=="POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username=="admin" and password=="123456":
            session["is_admin"] = True
            flash("Welcome Admin", "Success!")
            return redirect(url_for("index"))
        else:
            session["is_admin"] = False
            flash("Login as a public user!", "Info")
            return redirect(url_for("index"))
    return render_template('login.html')

@app.route('/index')
def index():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM food ORDER BY timestamp DESC")
        items = cur.fetchall()
    today = datetime.now().replace(hour = 0, minute = 0, second = 0, microsecond= 0)
    food_with_expiry = []
    if session.get("is_admin"): 
        for item in items:
            expiry_date = datetime.strptime(item[3], "%Y-%m-%d")
            days_left = (expiry_date - today).days
            food_with_expiry.append({
                "item": item,
                "days_left": days_left
            })
    else:
        for item in items:
            expiry_date = datetime.strptime(item[3], "%Y-%m-%d")
            days_left = (expiry_date - today).days
            if expiry_date > today:
                food_with_expiry.append({
                    "item": item,
                    "days_left": days_left
                })
    return render_template('index.html', food_with_expiry = food_with_expiry)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    min_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(min_date)
    if request.method == 'POST':
        expiry_date = request.form['expiry_date']
        today = datetime.today().date()
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        if expiry <= today:
            flash("Expiry Date must be a future date")
            return redirect(url_for("submit"))
        
        data = {
            'food_name': request.form['food_name'],
            'ingredients': request.form['ingredients'],
            'expiry_date': request.form['expiry_date'],
            'packed_status': request.form['packed_status'],
            'allergy_info': request.form['allergy_info'],
            'is_free': 1 if request.form.get('is_free') == 'on' else 0,
            'email': request.form['email']
            }
        print("Inserting a record")
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO food (food_name, ingredients, expiry_date, packed_status,
                                allergy_info, is_free, email)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', tuple(data.values()))
            print("Record Added", request.form['food_name'] )
        return redirect(url_for('education'))
    return render_template('submit.html', min_date = min_date)
@app.route('/education')
def education():
    return render_template('education.html')
@app.route('/logout')
def logout():
    session.clear()
    flash("Admin Logged out Successfully!", "info")
    return redirect(url_for("login"))

@app.route('/delete/<int:food_id>', methods=["POST"])
def delete_food(food_id):
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM food WHERE id=?', (food_id, ))
        conn.commit()
    flash("Item deleted successfully!")
    return redirect(url_for("index"))

@app.route("/download")
def download(): 
    if not session.get("is_admin"):
        return redirect(url_for("login"))
    directory = "/data" if os.environ.get("RENDER") else os.getcwd()
    #exception/error handling
    try:
        return send_from_directory(directory, "food.db", as_attachment = True)
    except FileNotFoundError:
        return "Database File Not Found", 404



if __name__ == '__main__':
    init_db()
    app.run(debug=True)
