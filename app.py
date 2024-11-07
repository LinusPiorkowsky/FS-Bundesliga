from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required to use sessions and flash messages

# In-memory storage for simplicity; in a real app, use a database
users = {}

# Route for the login page
@app.route('/')
def login():
    return render_template('login.html')

# Route for handling login
@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = users.get(username)
    
    # Check if user exists and password is correct
    if user and check_password_hash(user['password'], password):
        session['user'] = username
        flash('Logged in successfully!', 'success')
        return redirect(url_for('welcome'))
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))

# Route for the registration page
@app.route('/register')
def register():
    return render_template('register.html')

# Route for handling registration
@app.route('/register', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    # Check if passwords match
    if password != confirm_password:
        flash('Passwords do not match', 'error')
        return redirect(url_for('register'))
    
    # Check if username is already taken
    if username in users:
        flash('Username already exists', 'error')
        return redirect(url_for('register'))
    
    # Register the user
    users[username] = {'password': generate_password_hash(password)}
    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('login'))

# Route for a welcome page after login
@app.route('/welcome')
def welcome():
    if 'user' not in session:
        return redirect(url_for('login'))
    return f'Welcome, {session["user"]}!'

# Route to handle logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

