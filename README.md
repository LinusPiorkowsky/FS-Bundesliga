# FS-Bundesliga

This app will allow users to explore past Bundesliga results and get basic predictions for future games based on historical trends. It will focus on simplicity, using straightforward statistics to show likely outcomes.

Key Features:
- Historical Data Overview: Users can view team results over the past 8 seasons, including win/loss records and points earned each season.
- Basic Prediction Feature: Using simple stats (like win rates and home vs. away performance), the app will predict if a team is likely to win, lose, or draw their next game.
- Team Comparison: Users can pick two teams to compare their past matchups, showing results from the last few seasons.
- Simple Match Insights: For each upcoming game, the app will show basic insights, such as each team’s recent performance and a percentage-based likelihood of winning.

Value Proposition:
The app provides Bundesliga fans with an easy way to understand team trends and get basic predictions for upcoming games without advanced features. It’s ideal for fans who want a quick look at likely outcomes based on past performance.

Goals:
Simple and Functional: Develop a straightforward app with easy-to-understand features, focusing on team comparisons and simple predictions.
User-Friendly Interface: Make a clean, basic interface that anyone can use without technical knowledge.

## How to Update the Dataset

Follow these steps to update the `Updatet_games.csv` file with the latest data:

1. **Download the Latest Data**
   - Open the link: [Bundesliga Data](https://www.football-data.co.uk/germanym.php)
   - Download the CSV file for the **2024/2025 Season - Bundesliga 1**.

2. **Place the CSV in the Project Folder**
   - Move the downloaded CSV file into the `Dataset_Update` folder in this project.

3. **Set the File Path in the Script**
   - Copy the relative path of the downloaded CSV file (e.g., `Dataset_Update/your_downloaded_file.csv`).
   - Open `dataset_manipulation.py` and update the `file_path` variable on **line 4** with the new path.

4. **Run the Script**
   - Run `dataset_manipulation.py` to process the new data and update `Updatet_games.csv`.

5. **Cleanup**
   - After running the script, delete the downloaded CSV file from the `Dataset_Update` folder to keep the project directory organized.

6. **Confirmation**
   - The `Updatet_games.csv` file has now been updated with the latest game data.
