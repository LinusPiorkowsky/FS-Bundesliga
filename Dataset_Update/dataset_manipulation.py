import pandas as pd

# Load the CSV file
file_path = 'Dataset_Update/D1.csv'   # Einmal Pro Woche den neusten Datensatz laden, dann Pfad einfügen
df = pd.read_csv(file_path)

# Select and rename columns as per the desired structure
df_modified = df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HS', 'AS', 'HST', 'AST', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR']].copy()

# Rename columns to match the target structure
df_modified.columns = [
    'Date', 'HomeTeam', 'AwayTeam', 'HomeTeamGoals', 'AwayTeamGoals', 'Result',
    'HomeTeamShots', 'AwayTeamShots', 'HomeTeamShotsOnTarget', 'AwayTeamShotsOnTarget',
    'HomeTeamCorners', 'AwayTeamCorners', 'HomeTeamYellow', 'AwayTeamYellow',
    'HomeTeamRed', 'AwayTeamRed'
]

# Add placeholder columns for 'Index' and 'Season'
df_modified.insert(0, 'Index', range(1, len(df_modified) + 1))
df_modified.insert(1, 'Season', '2024')  # Use appropriate season as needed

# Calculate 'Gameday' based on groups of 9 games
df_modified.insert(2, 'Gameday', (df_modified.index // 9) + 1)

# Save the modified DataFrame, overwriting Updatet_games.csv
modified_file_path = 'Datasets/Updated_Games.csv'
df_modified.to_csv(modified_file_path, sep=';', index=False)

print(f'Modified file saved and overwrites the file at {modified_file_path}')
