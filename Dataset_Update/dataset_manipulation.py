import os
import requests
import pandas as pd
from datetime import datetime
from rapidfuzz import process
import subprocess
import schedule
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_UPDATE_DIR = BASE_DIR  
DATASETS_DIR = os.path.join(os.path.dirname(BASE_DIR), 'Datasets')

def verify_directories():
    if not os.path.exists(DATASET_UPDATE_DIR):
        raise FileNotFoundError(f"Directory {DATASET_UPDATE_DIR} does not exist.")
    if not os.path.exists(DATASETS_DIR):
        raise FileNotFoundError(f"Directory {DATASETS_DIR} does not exist.")

# Herunterladen der Bundesliga-Daten
def download_csv():
    url = "https://www.football-data.co.uk/mmz4281/2425/D1.csv"  # Aktuelle Saison
    local_path = os.path.join(DATASET_UPDATE_DIR, 'D1.csv')
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"CSV-Datei erfolgreich heruntergeladen: {local_path}")
    else:
        print(f"Fehler beim Herunterladen der Datei: {response.status_code}")
        raise Exception("Download fehlgeschlagen!")

# Modifizieren und Anhängen der Daten
def update_dataset():
    file_path = os.path.join(DATASET_UPDATE_DIR, 'D1.csv')
    modified_file_path = os.path.join(DATASETS_DIR, 'Updated_Games.csv')

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Datei {file_path} nicht gefunden. Bitte sicherstellen, dass der Download erfolgreich war.")
    
    # Neue CSV laden 
    df_new = pd.read_csv(file_path, sep=',')

    # Umbenennen und zusätzliche Spalten hinzufügen
    df_new_modified = df_new[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HS', 'AS', 'HST', 'AST', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR']].copy()
    df_new_modified.columns = [
        'Date', 'HomeTeam', 'AwayTeam', 'HomeTeamGoals', 'AwayTeamGoals', 'Result',
        'HomeTeamShots', 'AwayTeamShots', 'HomeTeamShotsOnTarget', 'AwayTeamShotsOnTarget',
        'HomeTeamCorners', 'AwayTeamCorners', 'HomeTeamYellow', 'AwayTeamYellow',
        'HomeTeamRed', 'AwayTeamRed'
    ]
    df_new_modified.insert(0, 'Index', range(1, len(df_new_modified) + 1))
    df_new_modified.insert(1, 'Season', '2024')  # Saison dynamisch anpassen
    df_new_modified.insert(2, 'Gameday', (df_new_modified.index // 9) + 1)

    # Bestehende Daten laden
    if os.path.exists(modified_file_path):
        df_existing = pd.read_csv(modified_file_path, delimiter=';')
        
        # Kombinieren 
        combined_df = pd.concat([df_existing, df_new_modified], ignore_index=True)
        
        # Doppelte Einträge entfernen
        combined_df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], inplace=True)
        
        # Index neu setzen
        combined_df.reset_index(drop=True, inplace=True)
        combined_df['Index'] = range(1, len(combined_df) + 1)
    else:
        # Wenn keine bestehenden Daten vorhanden sind, nur die neuen verwenden
        combined_df = df_new_modified

    # Geänderte Datei mit Semikolon speichern
    combined_df.to_csv(modified_file_path, sep=';', index=False)
    print(f"Datei wurde erfolgreich aktualisiert: {modified_file_path}")

# Mapping
def harmonize_team_names():
    updated_games_path = os.path.join(DATASETS_DIR, 'Updated_Games.csv')
    gameplan_path = os.path.join(DATASETS_DIR, 'gameplan_24_25.csv')

    updated_games = pd.read_csv(updated_games_path, sep=';', encoding='utf-8')
    gameplan = pd.read_csv(gameplan_path, sep=',', encoding='utf-8')

    # Extrahiere die Teamnamen aus gameplan_24_25
    official_teams = set(gameplan['HomeTeam']).union(set(gameplan['AwayTeam']))
    
    # Funktion zur Suche nach dem besten Match
    def find_best_match(team_name, choices):
        match, score, _ = process.extractOne(team_name, choices)
        return match if score > 60 else team_name  # Setze einen Ähnlichkeitsschwellenwert
    
    # Harmonisiere Home- und Away-Teamnamen in updated_games
    updated_games['HomeTeam'] = updated_games['HomeTeam'].apply(lambda x: find_best_match(x, official_teams))
    updated_games['AwayTeam'] = updated_games['AwayTeam'].apply(lambda x: find_best_match(x, official_teams))
    
    # Speichere den harmonisierten Datensatz mit Semikolon-Trennzeichen
    updated_games.to_csv(updated_games_path, sep=';', index=False)
    print(f"Harmonisierte Daten gespeichert unter: {updated_games_path}")

def git_commit_and_push():
    try:
        repo_path = "/Users/linus/FS-Bundesliga"
        os.chdir(repo_path)
        
        # Checken ob Git repo
        if not os.path.exists(os.path.join(repo_path, '.git')):
            print("Not a Git repository. Skipping commit.")
            return
        
        # Auto Commit
        subprocess.run(['git', 'add', 'Datasets/Updated_Games.csv'], check=True)
        
        # Commit 
        commit_message = f"Update Bundesliga data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Push to main
        subprocess.run(['git', 'push'], check=True)
        
        print("Successfully committed and pushed to GitHub!")
    except subprocess.CalledProcessError as e:
        print(f"Git operation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Funktion: Workflow für Montag
def monday_update():
    verify_directories()  # Verify directories exist
    print(f"Starte Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    download_csv()
    update_dataset()
    harmonize_team_names()
    git_commit_and_push()  # Git-Synchronisation
    print("Update abgeschlossen.")

if __name__ == "__main__":
    monday_update() # um manuell auszuführen

    schedule.every().monday.at("10:31").do(monday_update)
    print("Scheduler läuft. Warte auf Montag 10:31 Uhr...")
    while True:
        schedule.run_pending()
        time.sleep(1)