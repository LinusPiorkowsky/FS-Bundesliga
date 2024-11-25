import os
import requests
import pandas as pd
from datetime import datetime
from rapidfuzz import process

# Funktion: Herunterladen der Bundesliga-Daten
def download_csv():
    url = "https://www.football-data.co.uk/mmz4281/2425/D1.csv"  # Aktuelle Saison
    local_path = "Dataset_Update/D1.csv"  # Speicherort für die CSV
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"CSV-Datei erfolgreich heruntergeladen: {local_path}")
    else:
        print(f"Fehler beim Herunterladen der Datei: {response.status_code}")
        raise Exception("Download fehlgeschlagen!")

# Funktion: Modifizieren und Anhängen der Daten
def update_dataset():
    file_path = "Dataset_Update/D1.csv"
    modified_file_path = "Datasets/Updated_Games.csv"

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Datei {file_path} nicht gefunden. Bitte sicherstellen, dass der Download erfolgreich war.")
    
    # Neue CSV laden (Semikolon als Trennzeichen sicherstellen)
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

    # Bestehende Daten laden, wenn verfügbar
    if os.path.exists(modified_file_path):
        df_existing = pd.read_csv(modified_file_path, delimiter=';')
        
        # Kombinieren der Daten
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

"Mapping der Teamnamen aus der D1.csv und der führenden gameplan_24_25.csv"
def harmonize_team_names():

    """
    Harmonisiert Teamnamen in updated_games basierend auf den offiziellen Namen aus gameplan_24_25.

    """
    updated_games_path = 'Datasets/Updated_Games.csv'
    gameplan_path = 'Datasets/gameplan_24_25.csv'

    updated_games = pd.read_csv(updated_games_path, sep=';', encoding='utf-8')
    gameplan = pd.read_csv(gameplan_path, sep=',', encoding='utf-8')

    # Extrahiere die Teamnamen aus gameplan_24_25
    official_teams = set(gameplan['HomeTeam']).union(set(gameplan['AwayTeam']))
    
    # Funktion zur Suche nach dem besten Match
    def find_best_match(team_name, choices):
        match, score, _ = process.extractOne(team_name, choices)
        return match if score > 80 else team_name  # Setze einen Ähnlichkeitsschwellenwert (hier: 80)
    
    # Harmonisiere Home- und Away-Teamnamen in updated_games
    updated_games['HomeTeam'] = updated_games['HomeTeam'].apply(lambda x: find_best_match(x, official_teams))
    updated_games['AwayTeam'] = updated_games['AwayTeam'].apply(lambda x: find_best_match(x, official_teams))
    
    # Speichere den harmonisierten Datensatz mit Semikolon-Trennzeichen
    updated_games.to_csv(updated_games_path, sep=';', index=False)
    print(f"Harmonisierte Daten gespeichert unter: {updated_games_path}")

# Funktion: Workflow für Montag
def monday_update():
    print(f"Starte Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    download_csv()
    update_dataset()
    harmonize_team_names()
    print("Update abgeschlossen.")

# Zeitgesteuertes Ausführen mit `schedule`
if __name__ == "__main__":
    import schedule
    import time

    # Montags um 06:00 Uhr ausführen
    schedule.every().monday.at("10:31").do(monday_update)
    
    print("Scheduler läuft. Warte auf Montag 06:00 Uhr...")
    while True:
        schedule.run_pending()
        time.sleep(1)


