---
title: Architecture
parent: Technical Docs
nav_order: 1
---

{: .label }
[Linus Piorkowsky]

{: .no_toc }
# Architecture

<details open markdown="block">
{: .text-delta }
<summary>Table of contents</summary>
+ ToC
{: toc }
</details>

## Overview

The **Bundesliga Predictor App** is a Flask-based web application designed to provide users with match predictions, team insights, and historical Bundesliga results. It uses historical match data, statistical modeling, and a user-friendly interface to deliver meaningful insights.  

## Codemap

The applications codemap is build in the following structure:

```
FS-Webapp/
├── app.py
├── db.py
├── Dataset_Update/
│   ├── D1.csv
│   ├── dataset_manipulation.py
│   └── namemapping.py
├── Datasets/
│   ├── gamaeplan_24_25.csv
│   └── Updated_Games.csv
├── models.py
├── static/
│   ├── CSS/
│   │   └── styles.css
│   ├── Data/
│   │   └── teams.json
│   └── images/
│       └── bundesliga-logo.png
├── templates/
│   ├── account_actions.html
│   ├── change_favourite_team.html
│   ├── change_password.html
│   ├── change_username.html
│   ├── login.html
│   ├── prediction.html
│   ├── register.html
│   ├── results.html
│   ├── selectedpredictions.html
│   ├── team_insights.html
│   ├── verify_password.html
│   └── welcome.html
└── docs/
    ├── assets/
    ├── team-eval/
    ├── tecincal-focs/
    └── technical-docs/
```

## Cross-Cutting Concerns  

### Authentication & Authorization  

- **Flask-Login** manages user authentication and session control.  
- Users **must be logged in** to access prediction features.  
- Passwords are **hashed** before storage for security.  

### Data Flow  

The Bundesliga Predictor app **ingests historical match data** and **processes team performance statistics** to generate predictions.  

1. **Data Collection**  
   - `Updated_Games.csv` → Historical Bundesliga match results.  
   - `gameplan_24_25.csv` → Upcoming Bundesliga match schedule.  
   - `D1.csv` → Automatically updated at every app startup with the latest match data.  

2. **Data Processing**  
   - `dataset_manipulation.py` downloads, compares, and inserts new data from `D1.csv` into `Updated_Games.csv`.  
   - `namemapping.py` ensures **team name consistency** across datasets, preventing mismatches.  

### Prediction Logic  

The app generates **match outcome predictions** based on **historical team performance, weighted statistics, and efficiency metrics**.  

1. **User Input:**  
   - The user selects a **matchday** for which they want predictions.  

2. **Data Retrieval & Filtering:**  
   - The app loads **upcoming fixtures** from `gameplan_24_25.csv` and filters matches for the **selected matchday**.  
   - It also loads **historical match data** from `Updated_Games.csv` to analyze past performance trends.  

3. **Team Performance Analysis:**  
   - For each match, the app calculates **key performance indicators**, including:  
     - **Goals scored & conceded** (home vs. away performance).  
     - **Win ratio & team efficiency** based on past match results.  
     - **Weighted season impact:** Early-season predictions rely more on the previous season, while later predictions emphasize the current season.  

4. **Probability Calculation:**  
   - The model uses weighted team statistics to estimate probabilities for:  
     - **Home win**  
     - **Draw**  
     - **Away win**  
     - **Over 1.5 and over 2.5 goals**  

5. **Results Display:**  
   - The **calculated probabilities** are displayed in an intuitive, easy-to-read format.  
   - Users can explore insights such as **matches likely to have high goal counts** or **teams with the highest winning probability**.  

**This approach ensures predictions are based on real statistical data, making them interpretable, reliable, and computationally efficient.**  

### File Handling  

- All match datasets are stored in **CSV format** under `Datasets/`.  
- Dataset updates occur **automatically at application startup**:  
  - The system **compares existing data with newly fetched data**.  
  - If updates are found, **new records are appended** to `Updated_Games.csv`.  
  - This ensures **up-to-date predictions** without manual intervention.  

### Security  

- **User authentication** is managed via **Flask-Login** with secure session handling.  
- **Password hashing** ensures that user credentials are stored securely.
  
