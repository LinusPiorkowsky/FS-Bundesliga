import os
import pandas as pd
from rapidfuzz import process

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
        if team_name == "FC Koln":
            return team_name  # Keep "FC Koln" (we hade a lot of Problems with the name somehow)
        match, score, _ = process.extractOne(team_name, choices)
        return match if score > 60 else team_name  # Setze einen Ähnlichkeitsschwellenwert 
    
    # Harmonisiere Home- und Away-Teamnamen in updated_games
    updated_games['HomeTeam'] = updated_games['HomeTeam'].apply(lambda x: find_best_match(x, official_teams))
    updated_games['AwayTeam'] = updated_games['AwayTeam'].apply(lambda x: find_best_match(x, official_teams))
    
    # Speichere den harmonisierten Datensatz mit Semikolon-Trennzeichen
    updated_games.to_csv(updated_games_path, sep=';', index=False)
    print(f"Harmonisierte Daten gespeichert unter: {updated_games_path}")

harmonize_team_names()
