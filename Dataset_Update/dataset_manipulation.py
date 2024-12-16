import os
import requests
import pandas as pd
from datetime import datetime
from rapidfuzz import process
import subprocess

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
# datensatz vorbereiten auf check
def prepare_dataframe(df):
    # Convert date to a uniform format
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True).dt.strftime('%Y-%m-%d')
    # Strip whitespace from team names if present
    if 'HomeTeam' in df.columns and df['HomeTeam'].dtype == 'object':
        df['HomeTeam'] = df['HomeTeam'].str.strip()
    if 'AwayTeam' in df.columns and df['AwayTeam'].dtype == 'object':
        df['AwayTeam'] = df['AwayTeam'].str.strip()
    return df

def harmonize_team_names_in_df(df, official_teams):
    def find_best_match(team_name, choices):
        match, score, _ = process.extractOne(team_name, choices)
        return match if score > 60 else team_name

    df['HomeTeam'] = df['HomeTeam'].apply(lambda x: find_best_match(x, official_teams))
    df['AwayTeam'] = df['AwayTeam'].apply(lambda x: find_best_match(x, official_teams))
    return df

# Überprüfen, ob neue Daten vorhanden sind
def check_for_new_data():
    file_path = os.path.join(DATASET_UPDATE_DIR, 'D1.csv')
    modified_file_path = os.path.join(DATASETS_DIR, 'Updated_Games.csv')

    df_new = pd.read_csv(file_path, sep=',')
    df_new = prepare_dataframe(df_new)

    # If existing file doesn't exist, we consider everything as new
    if not os.path.exists(modified_file_path):
        print("Update erforderlich.")
        return True

    df_existing = pd.read_csv(modified_file_path, delimiter=';')
    df_existing = prepare_dataframe(df_existing)

    # Identify keys
    if not all(col in df_new.columns for col in ['Date', 'HomeTeam', 'AwayTeam']):
        raise ValueError("Spalten Date, HomeTeam oder AwayTeam fehlen in der neuen CSV.")
    if not all(col in df_existing.columns for col in ['Date', 'HomeTeam', 'AwayTeam']):
        raise ValueError("Spalten Date, HomeTeam oder AwayTeam fehlen in der bestehenden CSV.")

    # Create sets of keys
    existing_keys = set(zip(df_existing['Date'], df_existing['HomeTeam'], df_existing['AwayTeam']))
    new_keys = set(zip(df_new['Date'], df_new['HomeTeam'], df_new['AwayTeam']))

    diff = new_keys - existing_keys
    if len(diff) > 0:
        print(f"Neue Daten erkannt.")
        return True
    else:
        print("Keine neuen Daten gefunden.")
        return False

def update_dataset():
    file_path = os.path.join(DATASET_UPDATE_DIR, 'D1.csv')
    modified_file_path = os.path.join(DATASETS_DIR, 'Updated_Games.csv')

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Datei {file_path} nicht gefunden. Bitte sicherstellen, dass der Download erfolgreich war.")
    # Neue CSV laden
    df_new = pd.read_csv(file_path, sep=',')
    df_new = prepare_dataframe(df_new)

     #Umbenennen und zusätzliche Spalten hinzufügen
    df_new_modified = df_new[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HS', 'AS', 'HST', 'AST', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR']].copy()
    df_new_modified.columns = [
        'Date', 'HomeTeam', 'AwayTeam', 'HomeTeamGoals', 'AwayTeamGoals', 'Result',
        'HomeTeamShots', 'AwayTeamShots', 'HomeTeamShotsOnTarget', 'AwayTeamShotsOnTarget',
        'HomeTeamCorners', 'AwayTeamCorners', 'HomeTeamYellow', 'AwayTeamYellow',
        'HomeTeamRed', 'AwayTeamRed'
    ]

    df_new_modified.insert(0, 'Index', range(1, len(df_new_modified)+1))
    df_new_modified.insert(1, 'Season', '2024')
    df_new_modified.insert(2, 'Gameday', (df_new_modified.index // 9) + 1)

    if os.path.exists(modified_file_path):
        df_existing = pd.read_csv(modified_file_path, delimiter=';')
        df_existing = prepare_dataframe(df_existing)

        # If you harmonize team names in Updated_Games.csv, do it here for df_new_modified as well:
        # Load official team names from your gameplan (adjust path and code as needed)
        gameplan_path = os.path.join(DATASETS_DIR, 'gameplan_24_25.csv')
        gameplan = pd.read_csv(gameplan_path, sep=',', encoding='utf-8')
        official_teams = set(gameplan['HomeTeam']).union(set(gameplan['AwayTeam']))

        df_new_modified = harmonize_team_names_in_df(df_new_modified, official_teams)
        df_existing = harmonize_team_names_in_df(df_existing, official_teams)

        # Filter only truly new rows by anti-join
        merged = pd.merge(df_new_modified, df_existing[['Date', 'HomeTeam', 'AwayTeam']], 
                          on=['Date','HomeTeam','AwayTeam'], how='left', indicator=True)
        new_rows = merged[merged['_merge'] == 'left_only'].drop(columns='_merge')

        if len(new_rows) > 0:
            combined_df = pd.concat([df_existing, new_rows], ignore_index=True)
            combined_df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], inplace=True)
            combined_df.reset_index(drop=True, inplace=True)
            combined_df['Index'] = range(1, len(combined_df) + 1)
            combined_df.to_csv(modified_file_path, sep=';', index=False)
            print(f"{len(new_rows)} neue Zeilen wurden hinzugefügt. Datei aktualisiert: {modified_file_path}")
        else:
            print("Keine neuen Zeilen zum Hinzufügen gefunden.")
    else:
        # No existing data, just save the new file
        df_new_modified.to_csv(modified_file_path, sep=';', index=False)
        print(f"Keine bisherigen Daten vorhanden. Neue Datei erstellt: {modified_file_path}")

def harmonize_team_names():
    updated_games_path = os.path.join(DATASETS_DIR, 'Updated_Games.csv')
    gameplan_path = os.path.join(DATASETS_DIR, 'gameplan_24_25.csv')

    updated_games = pd.read_csv(updated_games_path, sep=';', encoding='utf-8')
    gameplan = pd.read_csv(gameplan_path, sep=',', encoding='utf-8')

    official_teams = set(gameplan['HomeTeam']).union(set(gameplan['AwayTeam']))
    updated_games = harmonize_team_names_in_df(updated_games, official_teams)

    updated_games.to_csv(updated_games_path, sep=';', index=False)
    print(f"Harmonisierte Daten gespeichert unter: {updated_games_path}")

def git_commit_and_push():
    try:
        repo_path = "/Users/linus/FS-Bundesliga"
        os.chdir(repo_path)
        
        if not os.path.exists(os.path.join(repo_path, '.git')):
            print("Not a Git repository. Skipping commit.")
            return
        
        subprocess.run(['git', 'add', 'Datasets/Updated_Games.csv'], check=True)
        
        commit_message = f"Update Bundesliga data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        subprocess.run(['git', 'push'], check=True)
        
        print("Successfully committed and pushed to GitHub!")
    except subprocess.CalledProcessError as e:
        print(f"Git operation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    verify_directories()
    print("Starte Initialisierung...")
    download_csv()

    if check_for_new_data():
        update_dataset()
        # harmonize_team_names() #testen ob jedes mal notwendig
        git_commit_and_push()
    else:
        print("Keine neuen Daten. Beende das Skript.")
