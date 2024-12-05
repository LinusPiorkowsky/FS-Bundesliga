import os
import requests
import pandas as pd

# Paths
DATASET_UPDATE_DIR = "Temp"  # Temporary folder for downloads
DATASETS_DIR = "Datasets"  # Final dataset storage
UPDATED_FILE_NAME = "Updated_Games.csv"

# URLs for historical data
SEASON_URLS = {
    "2016": "https://www.football-data.co.uk/mmz4281/1617/D1.csv",
    "2017": "https://www.football-data.co.uk/mmz4281/1718/D1.csv",
    "2018": "https://www.football-data.co.uk/mmz4281/1819/D1.csv",
    "2019": "https://www.football-data.co.uk/mmz4281/1920/D1.csv",
    "2020": "https://www.football-data.co.uk/mmz4281/2021/D1.csv",
    "2021": "https://www.football-data.co.uk/mmz4281/2122/D1.csv",
    "2022": "https://www.football-data.co.uk/mmz4281/2223/D1.csv",
    "2023": "https://www.football-data.co.uk/mmz4281/2324/D1.csv",
    "2024": "https://www.football-data.co.uk/mmz4281/2425/D1.csv",
}

def download_csv(url, season):
    """Download a CSV file for the given season."""
    os.makedirs(DATASET_UPDATE_DIR, exist_ok=True)
    local_path = os.path.join(DATASET_UPDATE_DIR, f'D1_{season}.csv')
    
    response = requests.get(url)
    if response.status_code == 200:
        with open(local_path, 'wb') as f:
            f.write(response.content)
        print(f"CSV file for season {season} downloaded successfully.")
        return local_path
    else:
        print(f"Failed to download data for season {season}. Status code: {response.status_code}")
        raise Exception("Download failed!")

def process_csv(file_path, season):
    """Process a single CSV file and standardize its format."""
    df = pd.read_csv(file_path)
    df_modified = df[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 
                      'HS', 'AS', 'HST', 'AST', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR']].copy()
    df_modified.columns = [
        'Date', 'HomeTeam', 'AwayTeam', 'HomeTeamGoals', 'AwayTeamGoals', 'Result',
        'HomeTeamShots', 'AwayTeamShots', 'HomeTeamShotsOnTarget', 'AwayTeamShotsOnTarget',
        'HomeTeamCorners', 'AwayTeamCorners', 'HomeTeamYellow', 'AwayTeamYellow',
        'HomeTeamRed', 'AwayTeamRed'
    ]
    df_modified.insert(0, 'Index', range(1, len(df_modified) + 1))
    df_modified.insert(1, 'Season', season)
    df_modified.insert(2, 'Gameday', (df_modified.index // 9) + 1)
    return df_modified

def update_dataset():
    """Download, process, and update the master dataset."""
    os.makedirs(DATASETS_DIR, exist_ok=True)
    master_file_path = os.path.join(DATASETS_DIR, UPDATED_FILE_NAME)

    all_data = []

    for season, url in SEASON_URLS.items():
        print(f"Processing season {season}...")
        try:
            csv_path = download_csv(url, season)
            processed_data = process_csv(csv_path, season)
            all_data.append(processed_data)
        except Exception as e:
            print(f"Error processing season {season}: {e}")
            continue

    # Combine all seasons into one DataFrame
    combined_df = pd.concat(all_data, ignore_index=True)

    # If master file exists, merge with it
    if os.path.exists(master_file_path):
        existing_df = pd.read_csv(master_file_path, delimiter=';')
        combined_df = pd.concat([existing_df, combined_df], ignore_index=True)
        combined_df.drop_duplicates(subset=['Date', 'HomeTeam', 'AwayTeam'], inplace=True)
        combined_df.reset_index(drop=True, inplace=True)
        combined_df['Index'] = range(1, len(combined_df) + 1)

    # Save the updated master dataset
    combined_df.to_csv(master_file_path, sep=';', index=False)
    print(f"Dataset updated successfully: {master_file_path}")

if __name__ == "__main__":
    update_dataset()
