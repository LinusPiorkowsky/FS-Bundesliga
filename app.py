import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import db
from functools import wraps

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(app.instance_path, 'users.db')
app.config['SECRET_KEY'] = 'supersecretkey'  # Use a secure, random key in production

# Initialize the database with the app
db.init_app(app)

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Route: Home (after login)
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Route: Register
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db_conn = db.get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif db_conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            error = f'User {username} is already registered.'

        if error is None:
            db_conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db_conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))

        flash(error)
    return render_template('register.html')

# Route: Login
@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db_conn = db.get_db()
        error = None
        user = db_conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user is None or not check_password_hash(user['password'], password):
            error = 'Incorrect username or password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            flash('You are now logged in.')
            return redirect(url_for('index'))

        flash(error)
    return render_template('login.html')

# Route: Logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
