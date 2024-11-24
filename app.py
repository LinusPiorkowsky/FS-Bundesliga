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

# Datensätze
bundesliga_df = pd.read_csv("Datasets/Bundesliga.csv", delimiter=';')
updated_games_df = pd.read_csv("Datasets/Updated_Games.csv", delimiter=';')

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
# Wenn die User_ID in der bestehenden Flask Sitzung existiert, wird der User automatisch eingeloggt
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Benutzer zu Login-Seite weiterleiten, wenn nicht eingeloggt
        return f(*args, **kwargs) #Wenn eingeloggt wird 
    return decorated_function

# Route für die Home-Seite, die nur zugänglich ist, wenn der Benutzer eingeloggt ist
@app.route('/')
@login_required
def index():
    user_id = session.get('user_id')
    db_conn = db.get_db()
    user = db_conn.execute('SELECT username, favourite_team FROM users WHERE id = ?', (user_id,)).fetchone()
    all_users = db_conn.execute('SELECT username FROM users').fetchall()
    return render_template('welcome.html', username=user['username'], favourite_team=user['favourite_team'], all_users=all_users)
    

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

@app.route('/prediction')
@login_required
def prediction():
    # zukünftige Spieltage laden und in Dropdown Menü laden
    games_df = pd.read_csv('Datasets/gameplan_24_25.csv')
    games_df['Date'] = pd.to_datetime(games_df['Date'], dayfirst=True)
    futuregames = games_df[games_df['Date'] > pd.to_datetime('today')]

    if futuregames.empty:
        gamedays = []
    else:
        gamedays = sorted(futuregames['Gameday'].unique())
    
    print("Gamedays:", gamedays)

    # Rückgabe an die Vorlage
    return render_template('prediction.html', gamedays=gamedays)

    
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

### Berechnungen für Lieblingsteam
combined_df = pd.concat([bundesliga_df, updated_games_df])

combined_df['Date'] = pd.to_datetime(combined_df['Date'], dayfirst=True)
combined_df.sort_values(by='Date', ascending=False, inplace=True)

# Funktion für berechnung
def get_team_insights(team_name):
    # Filter für das Team
    team_matches = combined_df[(combined_df['HomeTeam'] == team_name) | (combined_df['AwayTeam'] == team_name)]
    
    # Perfomace 5 letzte spiele
    last_5_games = team_matches.head(5)
    performance_last_5 = last_5_games.apply(
        lambda row: 'Win' if (row['HomeTeam'] == team_name and row['HomeTeamGoals'] > row['AwayTeamGoals']) or 
                                (row['AwayTeam'] == team_name and row['AwayTeamGoals'] > row['HomeTeamGoals']) else 
                    'Draw' if row['HomeTeamGoals'] == row['AwayTeamGoals'] else 'Loss', axis=1)
    
    # Berechnungen für 10 letzte Spiele
    last_10_games = team_matches.head(10)
    total_shots_on_target = last_10_games.apply(
        lambda row: row['HomeTeamShotsOnTarget'] if row['HomeTeam'] == team_name else row['AwayTeamShotsOnTarget'], axis=1).mean()
    
    avg_goals_scored = last_10_games.apply(
        lambda row: row['HomeTeamGoals'] if row['HomeTeam'] == team_name else row['AwayTeamGoals'], axis=1).mean()
    
    avg_goals_conceded = last_10_games.apply(
        lambda row: row['AwayTeamGoals'] if row['HomeTeam'] == team_name else row['HomeTeamGoals'], axis=1).mean()
    
    efficiency = last_10_games.apply(
        lambda row: (row['HomeTeamGoals'] / row['HomeTeamShotsOnTarget']) if row['HomeTeam'] == team_name else
                    (row['AwayTeamGoals'] / row['AwayTeamShotsOnTarget']), axis=1).mean(skipna=True)
    clean_sheets = last_10_games.apply(
        lambda row: 1 if (row['HomeTeam'] == team_name and row['AwayTeamGoals'] == 0) or 
                          (row['AwayTeam'] == team_name and row['HomeTeamGoals'] == 0) else 0, axis=1).sum()
    
    # Höchster Sieg
    season_2024 = combined_df[combined_df['Season'] == 2024]
    season_2024_team = season_2024[(season_2024['HomeTeam'] == team_name) | (season_2024['AwayTeam'] == team_name)]
    season_2024_team['GoalsScored'] = season_2024_team.apply(
        lambda row: row['HomeTeamGoals'] if row['HomeTeam'] == team_name else row['AwayTeamGoals'], axis=1
    )
    season_2024_team['GoalsConceded'] = season_2024_team.apply(
        lambda row: row['AwayTeamGoals'] if row['HomeTeam'] == team_name else row['HomeTeamGoals'], axis=1
    )
    highest_win_row = season_2024_team.loc[season_2024_team['GoalsScored'].idxmax()]
    highest_win_score = f"{highest_win_row['GoalsScored']}:{highest_win_row['GoalsConceded']}"
    highest_win_opponent = (
        highest_win_row['AwayTeam'] if highest_win_row['HomeTeam'] == team_name else highest_win_row['HomeTeam']
    )
    highest_win_detail = f"{highest_win_score} vs {highest_win_opponent}"
    
    # Overall rating tbd!!!
    rating = (total_shots_on_target * 0.3 + efficiency * 50 + clean_sheets * 5) / 10 * 100
    rating = min(max(int(rating), 1), 100)
    
    return {
        "Performance (Last 5 Games)": performance_last_5.tolist(),
        "Average Shots on Target (Last 10 Games)": total_shots_on_target,
        "Average Goals Scored (Last 10 Games)": avg_goals_scored,
        "Efficiency (Goals per Shot)": efficiency,
        "Average Goals Conceded (Last 10 Games)": avg_goals_conceded,
        "Clean Sheets (Last 10 Games)": clean_sheets,
        "Highest Win of 2024": highest_win_detail,
        "Overall Rating": rating
    }

# Route für favoriten Team
@app.route('/team_insights', methods=['GET'])
@login_required
def team_insights():
    user_id = session.get('user_id')
    db_conn = db.get_db()
    
    # Get the user's favorite team
    user = db_conn.execute('SELECT favourite_team FROM users WHERE id = ?', (user_id,)).fetchone()
    favourite_team = user['favourite_team']
    
    # Calculate insights for the favorite team
    insights = get_team_insights(favourite_team)
    
    return render_template('team_insights.html', favourite_team=favourite_team, insights=insights)


if __name__ == '__main__':
    open_port = find_open_port()  # Einen freien Port finden
    print(f"Flask is running on port {open_port}")
    app.run(debug=True, port=open_port, host='0.0.0.0')  # Flask mit dem gefundenen Port starten