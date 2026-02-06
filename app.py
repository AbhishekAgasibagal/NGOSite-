import sqlite3
import webbrowser
import os
from threading import Timer
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'ngo_secret_key'

UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
        conn.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT,
                start_date TEXT,
                end_date TEXT,
                location TEXT,
                image TEXT
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
    
    with sqlite3.connect('ngo.db') as conn:
        conn.row_factory = sqlite3.Row
        db_projects = conn.execute('SELECT * FROM projects').fetchall()
        
    return render_template('admin_dashboard.html', content=page_content, projects=db_projects)

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

@app.route('/save_project', methods=['POST'])
def save_project():
    if 'user' not in session:
        return redirect(url_for('index'))

    title = request.form.get('project_title')
    desc = request.form.get('description')
    status = request.form.get('status')
    start = request.form.get('start_date')
    end = request.form.get('end_date')
    loc = request.form.get('location')
    
    file = request.files.get('project_image')
    filename = ""
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    try:
        with sqlite3.connect('ngo.db') as conn:
            conn.execute('''
                INSERT INTO projects (title, description, status, start_date, end_date, location, image) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, desc, status, start, end, loc, filename))
        flash("Project saved successfully!", "success")
    except Exception as e:
        flash(f"Error: {e}", "danger")

    return redirect(url_for('admin_page'))

@app.route('/projects')
def projects():
    with sqlite3.connect('ngo.db') as conn:
        conn.row_factory = sqlite3.Row
        all_projects = conn.execute('SELECT * FROM projects').fetchall()
    return render_template('projects.html', projects=all_projects)

@app.route('/delete_project/<int:id>')
def delete_project(id):
    if 'user' not in session: return redirect(url_for('index'))
    with sqlite3.connect('ngo.db') as conn:
        conn.execute('DELETE FROM projects WHERE id = ?', (id,))
    flash("Project deleted successfully!", "success")
    return redirect(url_for('admin_page'))

@app.route('/edit_project/<int:id>', methods=['POST'])
def edit_project(id):
    if 'user' not in session: return redirect(url_for('index'))
    title = request.form.get('project_title')
    desc = request.form.get('description')
    status = request.form.get('status')
    loc = request.form.get('location')

    with sqlite3.connect('ngo.db') as conn:
        conn.execute('''
            UPDATE projects 
            SET title = ?, description = ?, status = ?, location = ? 
            WHERE id = ?
        ''', (title, desc, status, loc, id))
    flash("Project updated successfully!", "success")
    return redirect(url_for('admin_page'))

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(debug=True, use_reloader=False)
