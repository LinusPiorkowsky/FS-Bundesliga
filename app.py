import pandas as pd
import os
import socket
from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import db
from functools import wraps
from rapidfuzz import process
import json
import re

app = Flask(__name__, static_folder='Static')
app.config['DATABASE'] = os.path.join(app.instance_path, 'users.db')
app.config['SECRET_KEY'] = 'supersecretkey'

# Initialisiere die Datenbank mit der App
db.init_app(app)

# Datensatz
df = pd.read_csv("Datasets/Updated_Games.csv", delimiter=';')

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
    futuregames = games_df[games_df['Date'] > pd.to_datetime('today')]

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
    futuregames = games_df[games_df['Date'] > pd.to_datetime('today')]
    selected_games = futuregames[futuregames['Gameday'] == int(selected_gameday)]



    if selected_games.empty:
        games_list = "No games found for this Gameday."
    else:
        # Wahrscheinlichkeiten berechnen
        updated_games = pd.read_csv('Datasets/Updated_Games.csv', delimiter=';')
        updated_games['Date'] = pd.to_datetime(updated_games['Date'], dayfirst=True)
        
        print(updated_games['AwayTeamGoals'])

        # Die aktuelle Saison identifizieren
        current_season = updated_games['Season'].max()

        # Aktuelle Saison und ältere Spiele trennen
        current_season_data = updated_games[updated_games['Season'] == current_season]




        past_season_data = updated_games[updated_games['Season'] != current_season]

        def calculate_team_statistics(home_team, away_team, as_home=True, as_away=True):
            """
            Berechnet die gewichteten Statistiken für beide Teams in einem einzigen Aufruf und gibt die Ergebnisse
            für Heim- und Auswärtsspiele zurück. Diese Funktion wird für die Berechnung der Wahrscheinlichkeiten benötigt.
            """

            # Gemeinsame Saisons ermitteln
            team_seasons = set(past_season_data[past_season_data['HomeTeam'] == home_team]['Season']).union(
                past_season_data[past_season_data['AwayTeam'] == home_team]['Season']
            )
            opponent_seasons = set(past_season_data[past_season_data['HomeTeam'] == away_team]['Season']).union(
                past_season_data[past_season_data['AwayTeam'] == away_team]['Season']
            )
            common_seasons = team_seasons.intersection(opponent_seasons)

            # Filtern der Daten basierend auf gemeinsamen Saisons
            relevant_past_data = past_season_data[past_season_data['Season'].isin(common_seasons)]

            # Statistikberechnung für das Heimteam
            if as_home:
                home_stats = current_season_data[current_season_data['HomeTeam'] == home_team]
                home_stats_past = relevant_past_data[relevant_past_data['HomeTeam'] == home_team]
            else:
                home_stats = home_stats_past = pd.DataFrame()

            # Statistikberechnung für das Auswärtsteam
            if as_away:
                away_stats = current_season_data[current_season_data['AwayTeam'] == away_team]
                away_stats_past = relevant_past_data[relevant_past_data['AwayTeam'] == away_team]
            else:
                away_stats = away_stats_past = pd.DataFrame()

            # Funktion zur sicheren Summenberechnung
            def safe_sum(df, column):
                return df[column].sum() if not df.empty and column in df.columns else 0

            # Gewichtete Tore für das Heimteam und Auswärtsteam ??
            goals_scored_home =  safe_sum(home_stats, 'HomeTeamGoals')
            goals_scored_away = safe_sum(away_stats, 'AwayTeamGoals')
            goals_conceded_home = safe_sum(home_stats, 'AwayTeamGoals') 
            goals_conceded_away = safe_sum(away_stats, 'HomeTeamGoals') 

            # Gesamte Tore und Gegentore
            total_goals_scored = goals_scored_home + goals_scored_away
            total_goals_conceded = goals_conceded_home + goals_conceded_away

            # Berechnung weiterer Statistiken
            shots = safe_sum(home_stats, 'HomeTeamShots')  + \
                    safe_sum(away_stats, 'AwayTeamShots') 
            corners = safe_sum(home_stats, 'HomeTeamCorners') + \
                    safe_sum(away_stats, 'AwayTeamCorners')
            
            # Berechnung der Heimsiege des Heimteams in der aktuellen Saison
            home_wins_current = home_stats[home_stats['HomeTeamGoals'] > home_stats['AwayTeamGoals']].shape[0]
            # Berechnung der Auswärtssiege des Auswärtsteams in der aktuellen Saison
            away_wins_current = away_stats[away_stats['AwayTeamGoals'] > away_stats['HomeTeamGoals']].shape[0]


            # Print-Ausgaben für Debugging
            print(f"Statistiken für {home_team} und {away_team}:")
            print(f"Gemeinsame Saisons, in denen beide Teams in der Bundesliga gespielt haben: {sorted(common_seasons)}")
            print(f"{home_team} Heim Tore diese Saison: {safe_sum(home_stats, 'HomeTeamGoals')}")
            print(f"{home_team} Heim Tore vergangene Saisons: {safe_sum(home_stats_past, 'HomeTeamGoals')}")
            print(f"{away_team} Auswärt Tore diese Saison: {safe_sum(away_stats, 'AwayTeamGoals')}")
            print(f"{away_team} Auswärt Tore vergangene Saisons: {safe_sum(away_stats_past, 'AwayTeamGoals')}")
            
            print(f"Gesamt Tore {home_team}: {goals_scored_home}, Gesamt Tore {away_team}: {goals_scored_away}")
            print(f"Gesamt Gegentore {home_team}: {goals_conceded_home}, Gesamt Gegentore {away_team}: {goals_conceded_away}")
            print(f"Schüsse insgesamt (Heim + Auswärts): {shots}")
            print(f"Ecken insgesamt (Heim + Auswärts): {corners}")

            # Statistikwerte für beide Teams zusammenfassen
            stats = {
                'home_strength': goals_scored_home, 
                'away_strength': goals_scored_away,
                'goals_scored': total_goals_scored,
                'goals_conceded': total_goals_conceded,
                'goals_scored_home': goals_scored_home,
                'goals_scored_away': goals_scored_away,
                'goals_conceded_home': goals_conceded_home,
                'goals_conceded_away': goals_conceded_away,
                'home_wins' : home_wins_current,
                'away_wins' : away_wins_current,
                'win_ratio' :home_wins_current / max(1, away_wins_current), 
                'shots': shots,
                'corners': corners
              
            }

            return stats


        def calculate_win_probability(home_team, away_team, updated_games):
            """
            Berechnet die Wahrscheinlichkeiten für Heimsieg, Unentschieden und Auswärtssieg.
            Die Werte summieren sich zu 100% und berücksichtigen gewichtete Tore.
            """

            # Berechne die Statistiken für beide Teams in einem Aufruf
            stats = calculate_team_statistics(home_team, away_team, as_home=True, as_away=True)

            # Stärken für Heim- und Auswärtsteam
            home_strength = stats['home_strength']
            away_strength = stats['away_strength']


            # Ergebnisse klassifizieren
            updated_games['Result'] = updated_games.apply(
                lambda row: 'HomeWin' if row['HomeTeamGoals'] > row['AwayTeamGoals'] else
                            ('Draw' if row['HomeTeamGoals'] == row['AwayTeamGoals'] else 'AwayWin'),
                axis=1
            )

            # Häufigkeiten berechnen
            result_counts = updated_games['Result'].value_counts(normalize=True)

            # Basiswahrscheinlichkeiten
            base_home = result_counts.get('HomeWin', 0) * 100
            base_draw = result_counts.get('Draw', 0) * 100
            base_away = result_counts.get('AwayWin', 0) * 100

            print(f"Basiswahrscheinlichkeiten: Heimsieg {base_home:.2f}%, Unentschieden {base_draw:.2f}%, Auswärtssieg {base_away:.2f}%")

            # Unentschieden-Wahrscheinlichkeit anpassen
            print("Heimstärke ",home_strength)
            print("Auswärtstärke ", away_strength)

            # Sieg-Statistiken einbinden
            home_wins = stats['home_wins']
            away_wins = stats['away_wins']
            win_ratio = stats['win_ratio']


            # Einfluss von Siegen und Toren kombinieren
            strength_ratio = (home_strength + home_wins) / (away_strength + away_wins) if (away_strength + away_wins) != 0 else float('inf')

            # Kombination von Stärke- und Siegverhältnis
            combined_draw_factor = max(0, 1 - abs(1 - strength_ratio)) * (1 - abs(1 - win_ratio))

            # Unentschieden-Wahrscheinlichkeit berechnen
            draw_adjustment = combined_draw_factor * 20  # Verstärkungsfaktor für Draw
            
            draw_probability = base_draw + draw_adjustment

            # Sicherstellen, dass die Draw-Wahrscheinlichkeit in einem sinnvollen Bereich bleibt
            draw_probability = max(10, min(draw_probability, 40))


            # Verbleibende Wahrscheinlichkeit aufteilen basierend auf Stärken und Siegen
            remaining_probability = 100 - draw_probability
            total_strength_wins = (home_strength + home_wins) + (away_strength + away_wins)
            if total_strength_wins > 0:
                home_probability = base_home + (remaining_probability * ((home_strength + home_wins) / total_strength_wins))
                away_probability = base_away + (remaining_probability * ((away_strength + away_wins) / total_strength_wins))
            else:
                # Gleichverteilung bei fehlenden Stärken und Siegen
                home_probability = away_probability = remaining_probability / 2

            # Normieren, um numerische Fehler zu verhindern
            total_probability = home_probability + draw_probability + away_probability
            home_probability = (home_probability / total_probability) * 100
            draw_probability = (draw_probability / total_probability) * 100
            away_probability = (away_probability / total_probability) * 100

            print(f"Wahrscheinlichkeiten: Heimsieg {home_probability:.2f}%, Unentschieden {draw_probability:.2f}%, Auswärtssieg {away_probability:.2f}%")
            print(f"Heimsiege {home_team} in dieser Saison: {home_wins}")
            print(f"Auswärtssiege {away_team} in dieser Saison: {away_wins}")
            print(f"Sieg-Verhältnis (Heim/Auswärts): {win_ratio:.2f}")
            print(f"Stärke-Sieg-Verhältnis: {strength_ratio:.2f}")
            print(f"Angepasste Unentschieden-Wahrscheinlichkeit: {draw_probability:.2f}%")

            return round(home_probability, 2), round(draw_probability, 2), round(away_probability, 2)




        # Berechnung der Wahrscheinlichkeiten für jedes Spiel
        probabilities = []
        for _, game in selected_games.iterrows():
            home_prob, draw_prob, away_prob = calculate_win_probability(game['HomeTeam'], game['AwayTeam'], updated_games)
            probabilities.append((home_prob, draw_prob, away_prob))

        # Ergebnis-Dictionary
        games_list = {
            'dates': selected_games['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'times': selected_games['Time'].tolist(),
            'home_teams': selected_games['HomeTeam'].tolist(),
            'away_teams': selected_games['AwayTeam'].tolist(),
            'home_probabilities': [p[0] for p in probabilities],
            'draw_probabilities': [p[1] for p in probabilities],
            'away_probabilities': [p[2] for p in probabilities]
        }

        # Die Ergebnisse an die HTML-Vorlage zurückgeben
        return render_template('selectedprediction.html', gameday=selected_gameday, games_list=games_list)

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
    rating = round((total_shots_on_target * 4 + avg_goals_scored * 7 + clean_sheets * 5), 2)
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