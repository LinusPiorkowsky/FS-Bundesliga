import pandas as pd
import os
import socket
from flask import Flask, jsonify, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import db
from functools import wraps
from rapidfuzz import process
import json
import re
import math
from Dataset_Update.dataset_manipulation import (
    verify_directories,
    download_csv,
    check_for_new_data,
    update_dataset,
    harmonize_team_names,
    git_commit_and_push,
)

app = Flask(__name__, static_folder='Static')
app.config['DATABASE'] = os.path.join(app.instance_path, 'users.db')
app.config['SECRET_KEY'] = 'supersecretkey'

# Initialisiere die Datenbank mit der App
db.init_app(app)

# Stelle sicher, dass der Ordner für Instanzdateien existiert
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError as e:
    print(f"Error creating instance folder: {e}")

# Dataset update logic
def update_dataset_on_start():
    try:
        verify_directories()
        print("Starting dataset update...")
        download_csv()

        if check_for_new_data():
            update_dataset()
            harmonize_team_names()
            git_commit_and_push()
        else:
            print("No new data. Continuing with the existing dataset.")
    except Exception as e:
        print(f"Error during dataset update: {e}")

# Run dataset update logic before loading data
update_dataset_on_start()

# Load the updated dataset
df = pd.read_csv("Datasets/Updated_Games.csv", delimiter=';')

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

    # Fetch user information from the database
    user = db_conn.execute('SELECT username, favourite_team FROM users WHERE id = ?', (user_id,)).fetchone()
    all_users = db_conn.execute('SELECT username FROM users').fetchall()

    # Neuste Saison und Gameday
    latest_season = df['Season'].max()
    latest_gameday = df[df['Season'] == latest_season]['Gameday'].max()

    # Auf Default setzen
    season = int(request.args.get('season') or latest_season)
    gameday = int(request.args.get('gameday') or latest_gameday)

    # Rusults filtern
    results = df[(df['Season'] == season) & (df['Gameday'] == gameday)]

    # Tabelle filtern
    standings_data = df[(df['Season'] == season) & (df['Gameday'] <= gameday)]

    # Berechnung für Punkte und Tore
    standings_data['HomePoints'] = standings_data.apply(lambda x: 3 if x['HomeTeamGoals'] > x['AwayTeamGoals'] else 1 if x['HomeTeamGoals'] == x['AwayTeamGoals'] else 0, axis=1)
    standings_data['AwayPoints'] = standings_data.apply(lambda x: 3 if x['AwayTeamGoals'] > x['HomeTeamGoals'] else 1 if x['HomeTeamGoals'] == x['AwayTeamGoals'] else 0, axis=1)

    # Stats
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

    # Stats kombinieren für tabelle
    combined_stats = pd.concat([home_stats, away_stats]).groupby('Team').sum()
    combined_stats['GoalDifference'] = combined_stats['GoalsScored'] - combined_stats['GoalsConceded']
    combined_stats = combined_stats.sort_values(by=['Points', 'GoalDifference', 'GoalsScored'], ascending=False).reset_index()

    # Ranking
    combined_stats['Rank'] = combined_stats.index + 1

    return render_template(
        'welcome.html',
        username=user['username'],
        favourite_team=user['favourite_team'],
        all_users=[{'username': u['username']} for u in all_users],
        latest_results=results.to_dict(orient='records'),
        rankings=combined_stats.to_dict(orient='records'),
        selected_season=season,
        selected_gameday=gameday
    )

### Results ROUTE
@app.route('/results', methods=['GET'])
@login_required
def view_results():    

    # Determine the latest season and gameday from `Updated_Games.csv` for default values
    latest_season = df['Season'].max()
    latest_gameday = df[df['Season'] == latest_season]['Gameday'].max()

    # Set default season and gameday to the latest if no input is provided
    season = int(request.args.get('season') or latest_season)
    gameday = int(request.args.get('gameday') or latest_gameday)

    # Filter results for the selected season and gameday
    results = df[(df['Season'] == season) & (df['Gameday'] == gameday)]
    
    # Filter standings data up to the selected gameday for rankings
    standings_data = df[(df['Season'] == season) & (df['Gameday'] <= gameday)]
    
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
    seasons = sorted(df['Season'].unique(), reverse=True)
    
    # Determine the maximum available gameday for the selected season
    max_gameday_for_season = df[df['Season'] == season]['Gameday'].max()
    available_gamedays = sorted(df[(df['Season'] == season) & (df['Gameday'] <= max_gameday_for_season)]['Gameday'].unique())

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
    games_df = pd.read_csv('Datasets/gameplan_24_25.csv', sep=',', encoding='utf-8')
    games_df['Date'] = pd.to_datetime(games_df['Date'], dayfirst=True)
    futuregames = games_df[games_df['Date'] >= pd.to_datetime('today').normalize()]

    if futuregames.empty:
        gamedays = []
    else:
        gamedays = sorted(futuregames['Gameday'].unique())
    
    print("Gamedays:", gamedays)

    # Rückgabe an die Vorlage
    return render_template('prediction.html', gamedays=gamedays)

@app.route('/handle_prediction', methods=['POST'])
def handle_prediction():
    # Abrufen der Daten aus der Anfrage
    selected_gameday = request.form.get('gameday')

    # Spiele für den ausgewählten Gameday filtern
    games_df = pd.read_csv('Datasets/gameplan_24_25.csv', sep=',', encoding='utf-8')
    games_df['Date'] = pd.to_datetime(games_df['Date'], dayfirst=True)
    futuregames = games_df[games_df['Date'] >= pd.to_datetime('today').normalize()]

    # Sicherstellen, dass der Spieltag in Integer umgewandelt werden kann
    try:
        selected_gameday = int(selected_gameday)
    except (TypeError, ValueError):
        return jsonify({'error': 'Ungültiger Spieltag ausgewählt. Bitte geben Sie eine gültige Zahl ein.'}), 400

    selected_games = futuregames[futuregames['Gameday'] == selected_gameday]

    # Wenn keine Spiele gefunden wurden
    if selected_games.empty:
        return render_template('selectedprediction.html', gameday=selected_gameday, games_list="No games found for this Gameday.")
    
    else:

        # Daten für die Wahrscheinlichkeitsberechnung vorbereiten
        updated_games = pd.read_csv('Datasets/Updated_Games.csv', delimiter=';')
        updated_games['Date'] = pd.to_datetime(updated_games['Date'], dayfirst=True)

        # Die aktuelle Saison identifizieren
        current_season = updated_games['Season'].max()

        # Aktuelle Saison und ältere Spiele trennen
        current_season_data = updated_games[updated_games['Season'] == current_season]
        past_season_data = updated_games[updated_games['Season'] != current_season]

        # Funktionen zur Statistik- und Wahrscheinlichkeitsberechnung definieren
        def calculate_team_statistics(home_team, away_team, gameday):
            """
            Berechnet die gewichteten Statistiken für beide Teams basierend auf der aktuellen und vorhergehenden Saison.
            Die Gewichtung hängt vom Spieltag ab.
            """
            team_seasons = set(past_season_data[past_season_data['HomeTeam'] == home_team]['Season']).union(
                past_season_data[past_season_data['AwayTeam'] == home_team]['Season']
            )
            opponent_seasons = set(past_season_data[past_season_data['HomeTeam'] == away_team]['Season']).union(
                past_season_data[past_season_data['AwayTeam'] == away_team]['Season']
            )
            common_seasons = team_seasons.intersection(opponent_seasons)

            if len(common_seasons) > 0:  # Prüfen, ob es gemeinsame Saisons gibt
                last_common_season = max(common_seasons)
                last_common_season_data = past_season_data[past_season_data['Season'] == last_common_season].copy()

                home_stats_past = last_common_season_data[last_common_season_data['HomeTeam'] == home_team].copy()
                away_stats_past = last_common_season_data[last_common_season_data['AwayTeam'] == away_team].copy()
            else:
                # Falls keine gemeinsamen Saisons existieren, leere DataFrames initialisieren
                home_stats_past = pd.DataFrame()
                away_stats_past = pd.DataFrame()

            home_stats_current = current_season_data[current_season_data['HomeTeam'] == home_team].copy()
            away_stats_current = current_season_data[current_season_data['AwayTeam'] == away_team].copy()

            # Gewichtung der Statistiken basierend auf dem Spieltag
            if gameday == 1:
                weight_past = 1.0
                weight_current = 0.0
            elif gameday <= 6:
                weight_past = max(0, 1 - (gameday - 1) * 0.2)
                weight_current = 1 - weight_past
            else:
                weight_past = 0.0
                weight_current = 1.0

            def safe_sum(df, column):
                return df[column].sum() if not df.empty and column in df.columns else 0

            # Tore berechnen
            goals_scored_home = (
                weight_current * safe_sum(home_stats_current, 'HomeTeamGoals') +
                (weight_past * safe_sum(home_stats_past, 'HomeTeamGoals') if not home_stats_past.empty else 0)
            )
            goals_scored_away = (
                weight_current * safe_sum(away_stats_current, 'AwayTeamGoals') +
                (weight_past * safe_sum(away_stats_past, 'AwayTeamGoals') if not away_stats_past.empty else 0)
            )
            goals_conceded_home = (
                weight_current * safe_sum(home_stats_current, 'AwayTeamGoals') +
                (weight_past * safe_sum(home_stats_past, 'AwayTeamGoals') if not home_stats_past.empty else 0)
            )
            goals_conceded_away = (
                weight_current * safe_sum(away_stats_current, 'HomeTeamGoals') +
                (weight_past * safe_sum(away_stats_past, 'HomeTeamGoals') if not away_stats_past.empty else 0)
            )

            print(home_team, goals_scored_home)
            print(away_team, goals_scored_away)

            # Siege berechnen
            home_wins = 0
            if not home_stats_current.empty:
                home_wins += weight_current * home_stats_current.loc[
                    home_stats_current['HomeTeamGoals'] > home_stats_current['AwayTeamGoals']
                ].shape[0]
            if not home_stats_past.empty:
                home_wins += weight_past * home_stats_past.loc[
                    home_stats_past['HomeTeamGoals'] > home_stats_past['AwayTeamGoals']
                ].shape[0]

            away_wins = 0
            if not away_stats_current.empty:
                away_wins += weight_current * away_stats_current.loc[
                    away_stats_current['AwayTeamGoals'] > away_stats_current['HomeTeamGoals']
                ].shape[0]
            if not away_stats_past.empty:
                away_wins += weight_past * away_stats_past.loc[
                    away_stats_past['AwayTeamGoals'] > away_stats_past['HomeTeamGoals']
                ].shape[0]

            win_ratio = home_wins / (home_wins + away_wins) if (home_wins + away_wins) > 0 else 0.5

            print(home_team, home_wins)
            print(away_team, away_wins)

            stats = {
                'home_strength': goals_scored_home,
                'away_strength': goals_scored_away,
                'goals_scored': goals_scored_home + goals_scored_away,
                'goals_conceded': goals_conceded_home + goals_conceded_away,
                'home_wins': home_wins,
                'away_wins': away_wins,
                'win_ratio': win_ratio
            }
            return stats



        def calculate_win_probability(home_team, away_team, gameday, updated_games):
            """
            Berechne Wahrscheinlichkeiten für HomeWin, Draw und AwayWin.
            """
            stats = calculate_team_statistics(home_team, away_team, gameday)
            if stats is None:
                return 50, 25, 25  # Standardwerte, falls keine Stats gefunden werden

            home_strength = stats['home_strength']
            away_strength = stats['away_strength']
            home_wins = stats['home_wins']
            away_wins = stats['away_wins']
            win_ratio = stats['win_ratio']

            # Berechne das Verhältnis der Teamstärken und Wahrscheinlichkeiten
            strength_ratio = (0.3 * home_strength + 0.7 * home_wins) / (0.3* away_strength + 0.7 *away_wins) if (away_strength + away_wins) != 0 else 1
            combined_draw_factor = max(0, 1 - abs(1 - strength_ratio)) * (1 - abs(1 - win_ratio))
            draw_adjustment = combined_draw_factor * 20
            draw_probability = min(40, max(10, draw_adjustment + 25))

            remaining_probability = 100 - draw_probability
            total_strength_wins = (0.3 * home_strength + 0.7 * home_wins) + (0.3 * away_strength + 0.7*away_wins)

            if total_strength_wins > 0:
                home_probability = remaining_probability * ((0.3* home_strength + 0.7* home_wins) / total_strength_wins)
                away_probability = remaining_probability * ((0.3* away_strength + 0.7*away_wins) / total_strength_wins)
            else:
                home_probability = away_probability = remaining_probability / 2

            total_probability = home_probability + draw_probability + away_probability
            return round(home_probability / total_probability * 100, 2), \
                round(draw_probability / total_probability * 100, 2), \
                round(away_probability / total_probability * 100, 2)

        def calculate_average_goals(home_team, away_team, updated_games):
            """
            Berechnet die durchschnittlichen Tore pro Heimspiel für das Heimteam
            und die durchschnittlichen Tore pro Auswärtsspiel für das Auswärtsteam.
            """
            # Filter für Heimspiele des Heimteams
            home_games = updated_games[updated_games['HomeTeam'] == home_team]
            # Filter für Auswärtsspiele des Auswärtsteams
            away_games = updated_games[updated_games['AwayTeam'] == away_team]

            # Berechnung der Tore
            home_goals = home_games['HomeTeamGoals'].sum()  # Heimtore des Heimteams
            away_goals = away_games['AwayTeamGoals'].sum()  # Auswärtstore des Auswärtsteams

            # Berechnung der Anzahl der Spiele
            total_home_games = len(home_games)  # Anzahl der Heimspiele des Heimteams
            total_away_games = len(away_games)  # Anzahl der Auswärtsspiele des Auswärtsteams

            # Durchschnittliche Tore berechnen
            home_avg_goals = home_goals / total_home_games if total_home_games > 0 else 0
            away_avg_goals = away_goals / total_away_games if total_away_games > 0 else 0

            # Total durchschnittliche Tore berechnen
            total_avg_goals = home_avg_goals + away_avg_goals

            return home_avg_goals, away_avg_goals, total_avg_goals




        def calculate_over_goals_probability(home_avg_goals, away_avg_goals):
            """
            Berechnet Wahrscheinlichkeiten für über 1,5 und über 2,5 Tore
            mit einer realistischeren Abstufung.
            """
            total_avg_goals = home_avg_goals + away_avg_goals

            # Über-1,5 Tore
            if total_avg_goals <= 1:
                over_1_5_prob = 10  # Minimalwert
            elif total_avg_goals <= 2:
                over_1_5_prob = 20
            elif total_avg_goals <= 3:
                over_1_5_prob = 50
            elif total_avg_goals <= 4:
                over_1_5_prob = 60
            elif total_avg_goals <= 5:
                over_1_5_prob = 70
            else:
                over_1_5_prob = 95  # Obergrenze

            # Über-2,5 Tore (immer 10% weniger als Über-1,5 Tore)
            over_2_5_prob = max(0, over_1_5_prob - 10)

            return round(over_1_5_prob, 2), round(over_2_5_prob, 2)




    probabilities = []
    for _, game in selected_games.iterrows():
        home_prob, draw_prob, away_prob = calculate_win_probability(
            game['HomeTeam'], game['AwayTeam'], selected_gameday, updated_games)

        home_avg_goals, away_avg_goals, total_avg_goals = calculate_average_goals(
            game['HomeTeam'], game['AwayTeam'], updated_games)

        over_1_5_prob, over_2_5_prob = calculate_over_goals_probability(home_avg_goals, away_avg_goals)

        probabilities.append({
            'game': f'{game["HomeTeam"]} vs {game["AwayTeam"]}',
            'home_probability': home_prob,
            'draw_probability': draw_prob,
            'away_probability': away_prob,
            'total_avg_goals': total_avg_goals,
            'over_1_5_prob': over_1_5_prob,
            'over_2_5_prob': over_2_5_prob
        })

    games_list = {
        'dates': selected_games['Date'].dt.strftime('%Y-%m-%d').tolist(),
        'times': selected_games['Time'].tolist(),
        'home_teams': selected_games['HomeTeam'].tolist(),
        'away_teams': selected_games['AwayTeam'].tolist(),
        'home_probabilities': [p['home_probability'] for p in probabilities],
        'draw_probabilities': [p['draw_probability'] for p in probabilities],
        'away_probabilities': [p['away_probability'] for p in probabilities],
        'total_avg_goals': [p['total_avg_goals'] for p in probabilities],
        'over_1_5_prob': [p['over_1_5_prob'] for p in probabilities],
        'over_2_5_prob': [p['over_2_5_prob'] for p in probabilities]
    }

    # Zusatzübersichten erstellen
    most_likely_teams = [
    f"{game['game']} ({game['home_probability']}% Home Win)" if game['home_probability'] > 50 else
    f"{game['game']} ({game['away_probability']}% Away Win)" if game['away_probability'] > 50 else None
    for game in probabilities
]
    most_likely_teams = [team for team in most_likely_teams if team]

    high_goal_games = [
    f"{game['game']} ({game['over_2_5_prob']}% over 2.5 goals)"
    for game in probabilities if game['over_2_5_prob'] > 40
]

    return render_template(
        'selectedprediction.html',
        gameday=selected_gameday,
        games_list=games_list,
        most_likely_teams=most_likely_teams,
        high_goal_games=high_goal_games
    )


@app.route('/register', methods=('GET', 'POST'))
def register():
    # Load Bundesliga teams from JSON file
    json_path = "Static/Data/teams.json"
    try:
        with open(json_path, 'r') as file:
            unique_teams = json.load(file)
    except FileNotFoundError:
        unique_teams = {"BundesligaTeams": []}

    # Extract team names from JSON
    team_names = [team['name'] for team in unique_teams.get('BundesligaTeams', [])]

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        favourite_team = request.form.get('favourite_team')
        db_conn = db.get_db()
        error = None

        # Validate form inputs
        if not username:
            error = 'Username is required.'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters long.'
        elif not password:
            error = 'Password is required.'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters long.'
        elif not re.search(r'[A-Z]', password):
            error = 'Password must contain at least one uppercase letter.'
        elif not re.search(r'[a-z]', password):
            error = 'Password must contain at least one lowercase letter.'
        elif not re.search(r'\d', password):
            error = 'Password must contain at least one digit.'
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            error = 'Password must contain at least one special character.'
        elif password != confirm_password:
            error = 'Passwords do not match.'
        elif not favourite_team:
            error = 'Favourite team is required.'
        elif db_conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone() is not None:
            error = f'User {username} is already registered.'

        # Register user if no errors
        if error is None:
            db_conn.execute(
                'INSERT INTO users (username, password, favourite_team) VALUES (?, ?, ?)',
                (username, generate_password_hash(password), favourite_team)
            )
            db_conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login')) 

        flash(error)
    return render_template('register.html', teams=team_names)



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
# Function to calculate insights for a specific team
def get_team_insights(team_name):
    # Filter matches for the team
    team_matches = df[(df['HomeTeam'] == team_name) | (df['AwayTeam'] == team_name)]
    
    # Performance for the last 5 games
    last_5_games = team_matches.head(5)
    performance_last_5 = last_5_games.apply(
        lambda row: 'W' if (row['HomeTeam'] == team_name and row['HomeTeamGoals'] > row['AwayTeamGoals']) or 
                                (row['AwayTeam'] == team_name and row['AwayTeamGoals'] > row['HomeTeamGoals']) else 
                    'D' if row['HomeTeamGoals'] == row['AwayTeamGoals'] else 'L', axis=1)
    
    # Calculations for the last 10 games
    last_10_games = team_matches.head(10)
    total_shots_on_target = round(last_10_games.apply(
        lambda row: row['HomeTeamShotsOnTarget'] if row['HomeTeam'] == team_name else row['AwayTeamShotsOnTarget'], axis=1).mean(), 2)
    
    avg_goals_scored = round(last_10_games.apply(
        lambda row: row['HomeTeamGoals'] if row['HomeTeam'] == team_name else row['AwayTeamGoals'], axis=1).mean(), 2)
    
    avg_goals_conceded = round(last_10_games.apply(
        lambda row: row['AwayTeamGoals'] if row['HomeTeam'] == team_name else row['HomeTeamGoals'], axis=1).mean(), 2)
    
    efficiency = round(last_10_games.apply(
        lambda row: (row['HomeTeamGoals'] / row['HomeTeamShotsOnTarget']) if row['HomeTeam'] == team_name and row['HomeTeamShotsOnTarget'] > 0 else
                    (row['AwayTeamGoals'] / row['AwayTeamShotsOnTarget']) if row['AwayTeam'] == team_name and row['AwayTeamShotsOnTarget'] > 0 else 0,
        axis=1).mean(), 2)
    
    clean_sheets = last_10_games.apply(
        lambda row: 1 if (row['HomeTeam'] == team_name and row['AwayTeamGoals'] == 0) or 
                          (row['AwayTeam'] == team_name and row['HomeTeamGoals'] == 0) else 0, axis=1).sum()
    
    # Highest win in the 2024 season
    season_2024 = df[df['Season'] == 2024]
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
    
    # Overall rating
    rating = round((avg_goals_scored * 10 - avg_goals_conceded * 5 + clean_sheets * 10), 2)
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

# Function to calculate league averages
def get_league_averages():
    # Filter for the last 10 games for all teams
    last_10_games = df.tail(10 * len(df['HomeTeam'].unique()))

    # Calculations
    avg_shots_on_target = round(last_10_games[['HomeTeamShotsOnTarget', 'AwayTeamShotsOnTarget']].mean().mean(), 2)
    avg_goals_scored = round(last_10_games[['HomeTeamGoals', 'AwayTeamGoals']].mean().mean(), 2)
    avg_goals_conceded = avg_goals_scored  # Goals scored by one team are goals conceded by another
    efficiency = round(
        last_10_games.apply(
            lambda row: (row['HomeTeamGoals'] / row['HomeTeamShotsOnTarget']) if row['HomeTeamShotsOnTarget'] > 0 else 0, axis=1
        ).mean() + 
        last_10_games.apply(
            lambda row: (row['AwayTeamGoals'] / row['AwayTeamShotsOnTarget']) if row['AwayTeamShotsOnTarget'] > 0 else 0, axis=1
        ).mean(), 2
    )
    clean_sheets = last_10_games.apply(
        lambda row: (1 if row['AwayTeamGoals'] == 0 else 0) + (1 if row['HomeTeamGoals'] == 0 else 0), axis=1).sum()

    total_matches = len(last_10_games)
    avg_clean_sheets_per_game = round(clean_sheets / total_matches, 2)

    # Highest win league-wide in the 2024 season
    season_2024 = df[df['Season'] == 2024]
    season_2024['GoalDifference'] = abs(season_2024['HomeTeamGoals'] - season_2024['AwayTeamGoals'])
    highest_win_row = season_2024.loc[season_2024['GoalDifference'].idxmax()]
    highest_win_score = f"{max(highest_win_row['HomeTeamGoals'], highest_win_row['AwayTeamGoals'])}:{min(highest_win_row['HomeTeamGoals'], highest_win_row['AwayTeamGoals'])}"
    highest_win_teams = f"{highest_win_row['HomeTeam']} vs {highest_win_row['AwayTeam']}"

    return {
        "League Average Shots on Target": avg_shots_on_target,
        "League Average Goals Scored": avg_goals_scored,
        "League Efficiency (Goals per Shot)": round(efficiency / 2, 2),  # Divide by 2 since we summed home and away efficiency
        "League Average Goals Conceded": avg_goals_conceded,
        "Average Clean Sheets Per Game": avg_clean_sheets_per_game,
        "Highest Win of 2024": f"{highest_win_score} ({highest_win_teams})"
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
    
    # Load team data from JSON
    json_path = "Static/Data/teams.json"
    try:
        with open(json_path, 'r') as file:
            teams_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        teams_data = {"BundesligaTeams": []}
        print(f"Error loading JSON: {e}")

    # Find data for the favorite team
    team_data = next((team for team in teams_data.get('BundesligaTeams', []) if team['name'] == favourite_team), None)

    # Calculate insights for the favorite team
    insights = get_team_insights(favourite_team)
    league_averages = get_league_averages()
    
    return render_template(
        'team_insights.html',
        favourite_team=favourite_team,
        insights=insights,
        team_data=team_data,
        league_averages=league_averages
    )


@app.route('/account-settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        user_id = session.get('user_id')
        db_conn = db.get_db()

        # Fetch the user's hashed password from the database
        user = db_conn.execute('SELECT password FROM users WHERE id = ?', (user_id,)).fetchone()

        if not check_password_hash(user['password'], current_password):
            flash('Incorrect password. Please try again.', 'error')
            return render_template('verify_password.html')

        # Password correct, redirect to account actions
        session['verified'] = True
        return redirect(url_for('account_actions'))

    return render_template('verify_password.html')

@app.route('/account-actions')
@login_required
def account_actions():
    if not session.get('verified'):
        return redirect(url_for('account_settings'))

    return render_template('account_actions.html')

@app.route('/change-username', methods=['GET', 'POST'])
@login_required
def change_username():
    if not session.get('verified'):
        return redirect(url_for('account_settings'))

    if request.method == 'POST':
        new_username = request.form.get('new_username')
        user_id = session.get('user_id')
        db_conn = db.get_db()

        # Validate the new username
        if not new_username:
            flash('Username is required.', 'username_error')
        elif len(new_username) < 3:
            flash('Username must be at least 3 characters long.', 'username_error')
        elif db_conn.execute('SELECT id FROM users WHERE username = ?', (new_username,)).fetchone() is not None:
            flash(f'User {new_username} is already registered.', 'username_error')
        else:
            # Update username in the database
            db_conn.execute('UPDATE users SET username = ? WHERE id = ?', (new_username, user_id))
            db_conn.commit()
            flash('Username updated successfully!', 'username_success')
            return redirect(url_for('account_actions'))

    return render_template('change_username.html')

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not session.get('verified'):
        return redirect(url_for('account_settings'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        user_id = session.get('user_id')
        db_conn = db.get_db()

        # Validate the new password
        if not new_password:
            flash('Password is required.', 'password_error')
        elif len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'password_error')
        elif not re.search(r'[A-Z]', new_password):
            flash('Password must contain at least one uppercase letter.', 'password_error')
        elif not re.search(r'[a-z]', new_password):
            flash('Password must contain at least one lowercase letter.', 'password_error')
        elif not re.search(r'\d', new_password):
            flash('Password must contain at least one digit.', 'password_error')
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            flash('Password must contain at least one special character.', 'password_error')
        elif new_password != confirm_password:
            flash('Passwords do not match.', 'password_error')
        else:
            # Update the password in the database
            hashed_password = generate_password_hash(new_password)
            db_conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
            db_conn.commit()
            flash('Password updated successfully!', 'password_success')
            return redirect(url_for('account_actions'))

    return render_template('change_password.html')


@app.route('/change-favourite-team', methods=['GET', 'POST'])
@login_required
def change_favourite_team():
    # Load Bundesliga teams from JSON file
    json_path = "Static/Data/teams.json"
    try:
        with open(json_path, 'r') as file:
            unique_teams = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Handle missing or invalid JSON file
        unique_teams = {"BundesligaTeams": []}
        print(f"Error loading JSON: {e}")

    # Extract team names from JSON
    team_names = [team['name'] for team in unique_teams.get('BundesligaTeams', []) if isinstance(team, dict) and 'name' in team]

    if request.method == 'POST':
        favourite_team = request.form.get('favourite_team')
        user_id = session.get('user_id')
        db_conn = db.get_db()
        error = None

        # Validate input
        if not favourite_team:
            error = 'Favourite team is required.'
        elif favourite_team not in team_names:
            error = 'Invalid team selection.'

        # Update favourite team if no errors
        if error is None:
            db_conn.execute(
                'UPDATE users SET favourite_team = ? WHERE id = ?',
                (favourite_team, user_id)
            )
            db_conn.commit()
            flash('Favourite team updated successfully!', 'success')
            return redirect(url_for('account_actions'))

        flash(error, 'error')

    return render_template('change_favourite_team.html', teams=team_names)



if __name__ == '__main__':
    open_port = find_open_port()  # Einen freien Port finden
    print(f"Flask is running on port {open_port}")
    app.run(debug=True, port=open_port, host='0.0.0.0')  # Flask mit dem gefundenen Port starten