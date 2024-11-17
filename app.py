import pandas as pd
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
    os.makedirs(app.instance_path, exist_ok=True)
except OSError as e:
    print(f"Error creating instance folder: {e}")

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

# Boolean Logout und DB laufen nur einmal
first_request_flag = True

@app.before_request
def setup_before_first_request():
    global first_request_flag
    if first_request_flag:
        if 'user_id' in session:
            session.clear()  # Löscht die Sitzung
            flash('You have been logged out automatically.')  # Erfolgsmeldung

        # Initialize the database
        with app.app_context():
            db.init_db()
        
        first_request_flag = False

# Route für die Home-Seite, die nur zugänglich ist, wenn der Benutzer eingeloggt ist
@app.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    db_conn = db.get_db()
    user = db_conn.execute('SELECT username, favourite_team FROM users WHERE id = ?', (user_id,)).fetchone()
    return render_template('welcome.html', username=user['username'], favourite_team=user['favourite_team'])

@app.route('/results', methods=['GET'])
@login_required
def view_results():
    # Load CSV data
    bundesliga = pd.read_csv('Datasets/Bundesliga.csv', delimiter=';')
    updated_games = pd.read_csv('Datasets/Updated_Games.csv', delimiter=';')
    
    # Combine both dataframes for seamless filtering
    games = pd.concat([bundesliga, updated_games])

    # Determine the latest season and gameday from `Updated_Games.csv` for default values
    latest_season = updated_games['Season'].max()
    latest_gameday = updated_games[updated_games['Season'] == latest_season]['Gameday'].max()

    # Set default season and gameday to the latest if no input is provided
    season = int(request.args.get('season') or latest_season)
    gameday = int(request.args.get('gameday') or latest_gameday)

    # Filter results for the selected season and gameday
    results = games[(games['Season'] == season) & (games['Gameday'] == gameday)]
    
    # Filter standings data up to the selected gameday for rankings
    standings_data = games[(games['Season'] == season) & (games['Gameday'] <= gameday)]
    
    # Calculate points, goals scored, and goals conceded for each team
    standings_data['HomePoints'] = standings_data.apply(lambda x: 3 if x['HomeTeamGoals'] > x['AwayTeamGoals'] else 1 if x['HomeTeamGoals'] == x['AwayTeamGoals'] else 0, axis=1)
    standings_data['AwayPoints'] = standings_data.apply(lambda x: 3 if x['AwayTeamGoals'] > x['HomeTeamGoals'] else 1 if x['HomeTeamGoals'] == x['AwayTeamGoals'] else 0, axis=1)
    
    # Aggregate home and away stats
    home_stats = standings_data.groupby('HomeTeam').agg(
        Points=('HomePoints', 'sum'),
        GoalsScored=('HomeTeamGoals', 'sum'),
        GoalsConceded=('AwayTeamGoals', 'sum')
    ).reset_index().rename(columns={'HomeTeam': 'Team'})

    away_stats = standings_data.groupby('AwayTeam').agg(
        Points=('AwayPoints', 'sum'),
        GoalsScored=('AwayTeamGoals', 'sum'),
        GoalsConceded=('HomeTeamGoals', 'sum')
    ).reset_index().rename(columns={'AwayTeam': 'Team'})

    # Combine home and away stats for total standings
    combined_stats = pd.concat([home_stats, away_stats]).groupby('Team').sum()
    combined_stats['GoalDifference'] = combined_stats['GoalsScored'] - combined_stats['GoalsConceded']
    combined_stats = combined_stats.sort_values(by=['Points', 'GoalDifference', 'GoalsScored'], ascending=False).reset_index()

    # Assign ranks
    combined_stats['Rank'] = combined_stats.index + 1

    # Extract distinct seasons and gamedays for dropdowns
    seasons = sorted(games['Season'].unique(), reverse=True)
    
    # Determine the maximum available gameday for the selected season
    max_gameday_for_season = games[games['Season'] == season]['Gameday'].max()
    available_gamedays = sorted(games[(games['Season'] == season) & (games['Gameday'] <= max_gameday_for_season)]['Gameday'].unique())

    return render_template(
        'results.html',
        results=results.to_dict(orient='records'),
        seasons=seasons,
        gamedays=available_gamedays,
        rankings=combined_stats.to_dict(orient='records'),
        selected_season=season,
        selected_gameday=gameday,
        filter_summary=f"Results for Season {season}, Gameday {gameday}"
    )

# Prediction Route
@app.route('/prediction')
@login_required
def prediction():
    # tbd - erstmal filler
    prediction_data = {"message": "This is where predictions will be displayed."}
    return render_template('prediction.html', prediction=prediction_data)

# Funktion für Bundesliga Team (18) für auswahl bei registrierung
def load_bundesliga_teams():
    file_path = 'Datasets/Updated_Games.csv' 
    bundesliga_teams = pd.read_csv(file_path, delimiter=';')
    unique_teams = pd.unique(bundesliga_teams[['HomeTeam', 'AwayTeam']].values.ravel())
    return sorted(unique_teams)

unique_teams = load_bundesliga_teams()

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        favourite_team = request.form.get('favourite_team')
        db_conn = db.get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif not favourite_team:
            error = 'Favourite team is required.'
        elif db_conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            error = f'User {username} is already registered.'

        if error is None:
            db_conn.execute(
                'INSERT INTO users (username, password, favourite_team) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), favourite_team)
            )
            db_conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))

        flash(error)
    return render_template('register.html', teams=unique_teams)


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
@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.clear()  # Löscht alle Sitzungsdaten, einschließlich 'user_id'
    flash('You have been logged out.')  # Optional: Erfolgsmeldung
    return redirect(url_for('login'))  # Weiterleitung zur Login-Seite

# Route für favoriten Team
@app.route('/team_insights', methods=['GET'])
@login_required
def team_insights():
    user_id = session.get('user_id')
    db_conn = db.get_db()
    
    # sql für lieblingsteam von User
    user = db_conn.execute('SELECT favourite_team FROM users WHERE id = ?', (user_id,)).fetchone()
    favourite_team = user['favourite_team']
    return render_template('team_insights.html', favourite_team=favourite_team)

if __name__ == '__main__':
    open_port = find_open_port()  # Einen freien Port finden
    print(f"Flask is running on port {open_port}")
    app.run(debug=True, port=open_port, host='0.0.0.0')  # Flask mit dem gefundenen Port starten
