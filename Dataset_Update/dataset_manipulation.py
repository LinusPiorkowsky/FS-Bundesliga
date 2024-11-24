import os
import requests
import pandas as pd
from datetime import datetime

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
    
    # Neue CSV laden
    df_new = pd.read_csv(file_path)

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

    # Geänderte Datei speichern
    combined_df.to_csv(modified_file_path, sep=';', index=False)
    print(f"Datei wurde erfolgreich aktualisiert: {modified_file_path}")

# Funktion: Workflow für Montag
def monday_update():
    print(f"Starte Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    download_csv()
    update_dataset()
    print("Update abgeschlossen.")

# Zeitgesteuertes Ausführen mit `schedule`
if __name__ == "__main__":
    import schedule
    import time

    # Montags um 06:00 Uhr ausführen
    schedule.every().sunday.at("15:27").do(monday_update)
    
    print("Scheduler läuft. Warte auf Montag 06:00 Uhr...")
    while True:
        schedule.run_pending()
        time.sleep(1)

