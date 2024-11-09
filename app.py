import os
import socket
from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import db
from functools import wraps

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(app.instance_path, 'users.db')
app.config['SECRET_KEY'] = 'supersecretkey'

# Initialisiere die Datenbank mit der App
db.init_app(app)

# Stelle sicher, dass der Ordner für Instanzdateien existiert
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Funktion, um einen freien Port zu finden
def find_open_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))  # Auf einen verfügbaren Port binden
        return s.getsockname()[1]  # Den Port zurückgeben

# Login erforderlich Dekorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Benutzer zu Login-Seite weiterleiten, wenn nicht eingeloggt
        return f(*args, **kwargs)
    return decorated_function

# Logout automatisch beim Start der Anwendung ausführen
@app.before_first_request
def logout_automatically():
    # Wenn der Benutzer bereits eingeloggt ist, logge ihn aus
    if 'user_id' in session:
        session.clear()  # Löscht die Sitzung
        flash('You have been logged out automatically.')  # Optional: Erfolgsmeldung

@app.before_first_request
def initialize_db():
    """Stelle sicher, dass die DB bei der ersten Anfrage initialisiert wird."""
    with app.app_context():
        db.init_db()

# Route für die Home-Seite, die nur zugänglich ist, wenn der Benutzer eingeloggt ist
@app.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    db_conn = db.get_db()
    user = db_conn.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
    return render_template('welcome.html', username=user['username'])

# Registrierung-Route
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        db_conn = db.get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif db_conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            error = f'User {username} is already registered.'

        if error is None:
            db_conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db_conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))  # Nach der Registrierung zur Login-Seite weiterleiten

        flash(error)
    return render_template('register.html')

# Login-Route
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
            session.clear()  # Lösche vorherige Sitzungsdaten
            session['user_id'] = user['id']  # Setze die 'user_id' in der Session
            flash('You are now logged in.')
            return redirect(url_for('index'))  # Weiterleitung zur Welcome-Seite

        flash(error)
    return render_template('login.html')

# Logout-Route
@app.route('/logout')
@login_required
def logout():
    session.clear()  # Löscht alle Sitzungsdaten, einschließlich 'user_id'
    flash('You have been logged out.')  # Optional: Erfolgsmeldung
    return redirect(url_for('login'))  # Weiterleitung zur Login-Seite

if __name__ == '__main__':
    open_port = find_open_port()  # Einen freien Port finden
    print(f"Flask is running on port {open_port}")
    app.run(debug=True, port=open_port, host='0.0.0.0')  # Flask mit dem gefundenen Port starten
