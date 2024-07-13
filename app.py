from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to establish a database connection
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Route to handle login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'Logged in successfully as {username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')
    return render_template('login.html')

# Route to handle logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

# Route to display home page with tasks
@app.route('/')
def home():
    if 'user_id' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()
    conn.close()

    return render_template('home.html', tasks=tasks, username=session['username'], role=session['role'])

# Route to add a new task (only accessible by admin)
@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))

    task = request.form['task']

    # Handle file upload
    file_path = None
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != '':
            # Save file to the uploads folder
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

    # Insert task into the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task, status, file_path) VALUES (?, ?, ?)', (task, 'not started', file_path))
    conn.commit()
    conn.close()

    flash('Task added successfully!', 'success')
    return redirect(url_for('home'))

# Route to update a task (accessible by both admin and normal users)
@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    if 'user_id' not in session:
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))

    new_status = request.form['status']

    # Update task status in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
    conn.commit()
    conn.close()

    flash('Task updated successfully!', 'success')
    return redirect(url_for('home'))

# Route to serve uploaded files
@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Admin page route (accessible only to admins)
@app.route('/admin')
def admin():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()

    conn.close()

    return render_template('admin.html', users=users, tasks=tasks)

# Route to add a new user (accessible only by admin)
@app.route('/add_user', methods=['POST'])
def add_user():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('admin'))

    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    # Insert user into the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
    conn.commit()
    conn.close()

    flash('User added successfully!', 'success')
    return redirect(url_for('admin'))

# Helper function to check user credentials (replace with your own implementation)
def check_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

