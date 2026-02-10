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
        # User Authentication
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)''')
        
        # Projects Table
        conn.execute('''CREATE TABLE IF NOT EXISTS projects 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, 
                        status TEXT, start_date TEXT, end_date TEXT, location TEXT, image TEXT)''')

        # NEW MEDIA TABLES (Based on your images)
        conn.execute('''CREATE TABLE IF NOT EXISTS press_releases 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, date TEXT, description TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS media_coverage 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, url TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS gallery 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, image TEXT)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS videos 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT)''')

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

@app.route('/projects')
def projects():
    with sqlite3.connect('ngo.db') as conn:
        conn.row_factory = sqlite3.Row
        all_projects = conn.execute('SELECT * FROM projects ORDER BY id DESC').fetchall()
    return render_template('projects.html', projects=all_projects)
    
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
    
    if not user or not pwd:
        flash("Please fill in all fields.", "danger")
        return redirect(url_for('index'))

    try:
        with sqlite3.connect('ngo.db') as conn:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (user, pwd))
        flash("Account created! You can now login.", "success")
    except sqlite3.IntegrityError:
        flash("Username already exists.", "danger")
    except Exception as e:
        flash(f"An error occurred: {e}", "danger")
        
    # This line ensures you stay on the login page
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


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
        db_press = conn.execute('SELECT * FROM press_releases').fetchall()
        db_coverage = conn.execute('SELECT * FROM media_coverage').fetchall()
        db_gallery = conn.execute('SELECT * FROM gallery').fetchall()
        db_videos = conn.execute('SELECT * FROM videos').fetchall()
        
    return render_template('admin_dashboard.html', 
                           content=page_content, 
                           projects=db_projects,
                           press=db_press,
                           coverage=db_coverage,
                           gallery=db_gallery,
                           videos=db_videos)


@app.route('/save_project', methods=['POST'])
def save_project():
    if 'user' not in session: return redirect(url_for('index'))
    title = request.form.get('project_title')
    desc = request.form.get('description')
    status = request.form.get('status')
    start = request.form.get('start_date')
    end = request.form.get('end_date')
    loc = request.form.get('location')
    file = request.files.get('project_image')
    filename = secure_filename(file.filename) if file and file.filename != '' else ""
    if filename: file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    with sqlite3.connect('ngo.db') as conn:
        conn.execute('INSERT INTO projects (title, description, status, start_date, end_date, location, image) VALUES (?,?,?,?,?,?,?)',
                     (title, desc, status, start, end, loc, filename))
    flash("Project added!", "success")
    return redirect(url_for('admin_page'))

@app.route('/delete_project/<int:id>')
def delete_project(id):
    if 'user' not in session: return redirect(url_for('index'))
    with sqlite3.connect('ngo.db') as conn:
        conn.execute('DELETE FROM projects WHERE id = ?', (id,))
    return redirect(url_for('admin_page'))


@app.route('/add_press', methods=['POST'])
def add_press():
    if 'user' not in session: return redirect(url_for('index'))
    title = request.form.get('title')
    date = request.form.get('date')
    desc = request.form.get('description')
    with sqlite3.connect('ngo.db') as conn:
        conn.execute('INSERT INTO press_releases (title, date, description) VALUES (?,?,?)', (title, date, desc))
    flash("Press Release Added!", "success")
    return redirect(url_for('admin_page'))

@app.route('/add_coverage', methods=['POST'])
def add_coverage():
    if 'user' not in session: return redirect(url_for('index'))
    title = request.form.get('title')
    url = request.form.get('url')
    with sqlite3.connect('ngo.db') as conn:
        conn.execute('INSERT INTO media_coverage (title, url) VALUES (?,?)', (title, url))
    flash("Media Coverage Added!", "success")
    return redirect(url_for('admin_page'))

@app.route('/add_gallery', methods=['POST'])
def add_gallery():
    if 'user' not in session: return redirect(url_for('index'))
    file = request.files.get('image')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        with sqlite3.connect('ngo.db') as conn:
            conn.execute('INSERT INTO gallery (image) VALUES (?)', (filename,))
        flash("Gallery image uploaded!", "success")
    return redirect(url_for('admin_page'))

@app.route('/add_video', methods=['POST'])
def add_video():
    if 'user' not in session: return redirect(url_for('index'))
    url = request.form.get('url')
    with sqlite3.connect('ngo.db') as conn:
        conn.execute('INSERT INTO videos (url) VALUES (?)', (url,))
    flash("Video link saved!", "success")
    return redirect(url_for('admin_page'))


@app.route('/delete_press/<int:id>')
def delete_press(id):
    with sqlite3.connect('ngo.db') as conn:
        conn.execute('DELETE FROM press_releases WHERE id = ?', (id,))
    return redirect(url_for('admin_page'))

@app.route('/delete_gallery/<int:id>')
def delete_gallery(id):
    with sqlite3.connect('ngo.db') as conn:
        conn.execute('DELETE FROM gallery WHERE id = ?', (id,))
    return redirect(url_for('admin_page'))


@app.route('/media')
def media_page():
    with sqlite3.connect('ngo.db') as conn:
        conn.row_factory = sqlite3.Row
        # Fetching all data to display on the frontend
        db_press = conn.execute('SELECT * FROM press_releases ORDER BY id DESC').fetchall()
        db_coverage = conn.execute('SELECT * FROM media_coverage ORDER BY id DESC').fetchall()
        db_gallery = conn.execute('SELECT * FROM gallery ORDER BY id DESC').fetchall()
        db_videos = conn.execute('SELECT * FROM videos ORDER BY id DESC').fetchall()
        
    return render_template('media.html', 
                           press=db_press, 
                           coverage=db_coverage, 
                           gallery=db_gallery, 
                           videos=db_videos)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))



