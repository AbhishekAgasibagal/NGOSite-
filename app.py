import sqlite3
import webbrowser
from threading import Timer
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'ngo_secret_key'

page_content = {
    "banner_title": "Empowering Lives",
    "mission": "Learn how we change the world.",
    "vision": "Education, Health, and more.",
    "stats": [
        {"value": "15K+", "label": "Lives Impacted"},
        {"value": "120+", "label": "Volunteers"},
        {"value": "45+", "label": "Active Projects"}
    ]
}

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

def init_db():
    with sqlite3.connect('ngo.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

init_db()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('index.html', content=page_content)

@app.route('/about')
def about():
    about_info = {
        "mission": page_content["mission"],
        "vision": page_content["vision"],
        "stats": page_content["stats"]
    }
    return render_template('about.html', data=about_info)

@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        page_content['banner_title'] = request.form.get('banner_title')
        page_content['mission'] = request.form.get('mission')
        page_content['vision'] = request.form.get('vision')
        flash("Website updated successfully!", "success")
        return redirect(url_for('admin_page'))
        
    return render_template('admin_dashboard.html', content=page_content)

@app.route('/login', methods=['POST'])
def login():
    user = request.form.get('user')
    pwd = request.form.get('pass')
    with sqlite3.connect('ngo.db') as conn:
        res = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (user, pwd)).fetchone()
    if res:
        session['user'] = user
        return redirect(url_for('home'))
    flash("Invalid credentials", "danger")
    return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    user = request.form.get('new_user')
    pwd = request.form.get('new_pass')
    try:
        with sqlite3.connect('ngo.db') as conn:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (user, pwd))
        flash("Account created! You can now login.", "success")
    except:
        flash("Username already exists.", "danger")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(debug=True, use_reloader=False)