import os
import requests
import pandas as pd
from datetime import datetime
from rapidfuzz import process


def harmonize_team_names():

    """
    Harmonisiert Teamnamen in basierend auf den offiziellen Namen aus gameplan_24_25.

    """
    updated_games = pd.read_csv('Dataset_Update/D1.csv', sep=',', encoding='utf-8')
    gameplan = pd.read_csv('Datasets/gameplan_24_25.csv', sep=',', encoding='utf-8')

    
    # Extrahiere die Teamnamen aus gameplan_24_25
    official_teams = set(gameplan['HomeTeam']).union(set(gameplan['AwayTeam']))
    
    # Funktion zur Suche nach dem besten Match
    def find_best_match(team_name, choices):
        match, score, _ = process.extractOne(team_name, choices)
        return match if score > 80 else team_name  # Setze einen Ähnlichkeitsschwellenwert (hier: 80)
    

    # Harmonisiere Home- und Away-Teamnamen in updated_games
    updated_games['HomeTeam'] = updated_games['HomeTeam'].apply(lambda x: find_best_match(x, official_teams))
    updated_games['AwayTeam'] = updated_games['AwayTeam'].apply(lambda x: find_best_match(x, official_teams))
    
    # Speichere den harmonisierten Datensatz
    updated_games.to_csv('Dataset_Update/D1.csv', index=False)
    print(f"Harmonisierte Daten gespeichert unter: {'Dataset_Update/D1.csv'}")

harmonize_team_names() 


