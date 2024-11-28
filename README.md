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

Predcition features per game:
- Probabilty of a win
- probability of a draw
- Probbaility to score more or less then 1,5 goals 
- probabability to score more or less then 2,5 goals


## Bundesliga Match Outcome Prediction Logic
This document explains the step-by-step logic used to calculate probabilities for match outcomes (home win, draw, away win) in Bundesliga matches. The prediction method is only based on current season data at the moment, tailored to the unique characteristics of the Bundesliga. Anyhow, the past_season data is already provided and accessable within the code. We just need to agree to a certain logic to implement the outcome of the last seasons.



   **Step 1: Basic Probabilities**
      The foundation of the prediction model is derived from historical Bundesliga match data (Updated_Games.csv):

      Home Win Probability:
      Percentage of matches where the home team won: 44.95%.

      Away Win Probability:
      Percentage of matches where the away team won: 30.23%.

      Draw Probability:
      Percentage of matches that ended in a draw: 24.81%.

      Key Assumption:
      These probabilities are specific to Bundesliga matches to account for league-specific factors such as home-field advantage and playing styles.

   **Step 2: Gathering Relevant Team Statistics**
      For the example match 1. FC Union Berlin vs. Bayer 04 Leverkusen (Matchday 12), the following data is extracted:

      Current Season Data:

      1. FC Union Berlin (Home Team):

         Goals scored at home: 6.
         Home wins: 3.
         Bayer 04 Leverkusen (Away Team):
         Goals scored away: 11.
         Away wins: 2.
         Historical Data:

      Union Berlin:
         Goals scored at home across all shared seasons: 133.
         Leverkusen:
         Goals scored away across all shared seasons: 194.

   **Step 3: Adjusting Probabilities Using Team-Specific Data**
      A. Goal-Based Strength Adjustment
      The difference in goals is calculated to gauge the relative attacking strength of both teams:

      Home Goals (Union Berlin): 6
      Away Goals (Leverkusen): 11
      Goal Difference: 6 - 11 = -5
      This negative difference indicates that Leverkusen's away attacking performance outweighs Union Berlin's home attacking performance.

      B. Win-Based Adjustment
      We incorporate the win counts for both teams this season:

      Union Berlin (Home Wins): 3
      Leverkusen (Away Wins): 2
      Win Ratio: 3 / 2 = 1.50

      C. Combined Strength-Win Adjustment
      To balance the goal-based adjustment and win-based adjustment, we calculate the strength-win ratio:
      Strength-Win Ratio: (6 + 3) / (11 + 2) = 9 / 13 ≈ 0.69

   **Step 4: Adjusting Probabilities for Draws**
      The draw probability is dynamically adjusted based on the similarity in the strengths and win rates of the teams:

      Closer strength-win ratio to 1: Higher draw probability (evenly matched teams).
      Further from 1: Lower draw probability (clear favorite emerges).
      For this match:
      Strength-Win Ratio: 0.69
      This indicates a moderate edge for Leverkusen, reducing the draw probability slightly.

      Draw Adjustment:
      Draw Adjustment: (1 - abs(1 - 0.69)) * Scaling Factor
      Adjusted Draw Probability: 18.12%

   **Step 5: Final Probability Distribution**
      The remaining probability (after adjusting for draws) is distributed between home and away wins, weighted by the adjusted strengths and wins.

      Steps:
      Calculate Total Strength + Wins:

      Union Berlin Total Strength: 6 + 3 = 9
      Leverkusen Total Strength: 11 + 2 = 13
      Total Strength: 9 + 13 = 22
      
      Calculate Home Win Probability:
      
      Home Probability: 
         Base Home Probability + (9 / 22 * Remaining Probability)

      Calculate Away Win Probability:
         Away Probability: Base Away Probability + (13 / 22 * Remaining Probability)

      Final Output
         For the example match 1. FC Union Berlin vs. Bayer 04 Leverkusen:

         Home Win Probability: 41.60%
         Draw Probability: 18.12%
         Away Win Probability: 40.28%
      
   **Key Assumptions**
      Current Season Data:
      Only current season statistics (goals, wins) are used for strength calculations to ensure predictions reflect recent performance.

      League-Specific Trends:
      Probabilities are based exclusively on Bundesliga data to account for unique characteristics of the league.

      Equal Weighting:
      Goal strength and win ratios are equally weighted to balance attacking and winning performance.


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


