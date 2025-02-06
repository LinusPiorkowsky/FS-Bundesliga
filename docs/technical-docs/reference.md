---
title: Reference
parent: Technical Docs
nav_order: 3
---

{: .label }
[Linus Piorkowsky & Henry Lückewille]

{: .no_toc }
# Reference documentation

<details open markdown="block">
{: .text-delta }
<summary>Table of contents</summary>
+ ToC
{: toc }
</details>

## Data Management

### `update_dataset_on_start()`

**Route:** None (Initialization function)

**Methods:** None

**Purpose:** Initializes and updates the dataset on application startup. Verifies directories, downloads new CSV data, and updates the dataset if new data is available.

**Sample output:** Console logs indicating successful dataset update or error messages.

---

### `verify_directories()`

**Route:** None (Helper function)

**Methods:** None

**Purpose:** Verifies existence of required data directories DATASET_UPDATE_DIR and DATASETS_DIR.

**Sample output:** FileNotFoundError if directories don't exist

---

### `download_csv()`

**Route:** None (Helper function)

**Methods:** None

**Purpose:** Downloads current season Bundesliga data from football-data.co.uk.

**Sample output:** CSV file saved to DATASET_UPDATE_DIR or exception on failure

---

### `prepare_dataframe(df)`

**Route:** None (Helper function)

**Methods:** None

**Purpose:** Standardizes DataFrame formatting:
- Converts dates to YYYY-MM-DD
- Strips whitespace from team names

**Sample output:** Cleaned DataFrame

---

### `harmonize_team_names_in_df(df, official_teams)`

**Route:** None (Helper function)

**Methods:** None

**Purpose:** Matches and standardizes team names using fuzzy matching with official team list.

**Sample output:** DataFrame with standardized team names

---

### `harmonize_team_names()`

**Route:** None (Helper function)

**Methods:** None

**Purpose:** Standardizes team names across datasets by comparing against official team list from gameplan and updating the games database.

**Sample output:** Updated CSV file with harmonized team names

---

### `check_for_new_data()`

**Route:** None (Helper function)

**Methods:** None

**Purpose:** Compares downloaded data with existing dataset to identify new entries.

**Sample output:** Boolean indicating if new data exists

---

### `git_commit_and_push()`

**Route:** None (Helper function)

**Methods:** None

**Purpose:** Automates Git operations for dataset updates:
- Adds Updated_Games.csv
- Commits with timestamped message
- Pushes to GitHub repository

**Sample output:** Console confirmation of successful Git operations or error messages

---

## Authentication

### `login_required(f)`

**Route:** None (Decorator)

**Methods:** None

**Purpose:** Decorator function that ensures user authentication before accessing protected routes. Redirects to login page if user is not authenticated.

**Sample output:** None (Redirects to login page if not authenticated)

---

### `register()`

**Route:** `/register`

**Methods:** `GET`, `POST`

**Purpose:** Handles user registration with validation for username, password, and favorite team selection. Validates password complexity and uniqueness of username.

**Sample output:** Registration form or redirect to login page with success message

---

### `login()`

**Route:** `/login`

**Methods:** `GET`, `POST`

**Purpose:** Handles user authentication, verifies credentials, and establishes user session.

**Sample output:** Login form or redirect to index page with success message

---

### `logout()`

**Route:** `/logout`

**Methods:** `GET`

**Purpose:** Terminates user session and redirects to login page.

**Sample output:** Redirect to login page with logout confirmation message

---

## Main Views

### `index()`

**Route:** `/`

**Methods:** `GET`

**Purpose:** Displays the main dashboard with latest season data, gameday information, and user-specific content. Shows current standings and match results.

**Sample output:**
- User information
- Latest match results
- Current season standings
- Team rankings and statistics

---

### `view_results()`

**Route:** `/results`

**Methods:** `GET`

**Purpose:** Shows match results with filtering options for season and gameday. Displays standings and detailed match statistics.

**Sample output:**
- Filtered match results
- Season standings
- Team statistics and rankings
- Gameday selection options

---

## Prediction System

### `prediction()`

**Route:** `/prediction`

**Methods:** `GET`

**Purpose:** Initializes the prediction interface showing future gamedays for match predictions.

**Sample output:** Prediction form with available future gamedays

---

### `handle_prediction()`

**Route:** `/prediction/handle`

**Methods:** `POST`

**Purpose:** Processes match predictions using historical data and statistical analysis. Calculates win probabilities and goal statistics.

**Sample output:**
- Match predictions
- Win/Draw/Loss probabilities
- Goal scoring probabilities
- Team performance insights

---

## Team Analytics

### `get_team_insights(team_name)`

**Route:** None (Helper function)

**Methods:** None

**Purpose:** Calculates detailed team statistics and performance metrics for the last 5-10 games.

**Sample output:**
- Performance history
- Average shots on target
- Goal statistics
- Team efficiency metrics
- Clean sheet records
- Overall team rating

---

### `get_league_averages()`

**Route:** None (Helper function)

**Methods:** None

**Purpose:** Calculates league-wide statistics and averages for comparative analysis.

**Sample output:**
- League average statistics
- Goal metrics
- Team efficiency comparisons
- Season records

---

### `team_insights()`

**Route:** `/team-insights`

**Methods:** `GET`

**Purpose:** Displays comprehensive team analysis and comparison with league averages for the user's favorite team.

**Sample output:**
- Detailed team statistics
- League comparison metrics
- Performance visualizations
- Historical records
