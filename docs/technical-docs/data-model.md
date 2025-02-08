---
title: Data Model
parent: Technical Docs
nav_order: 2
---

{: .label }
[Linus Piorkowsky & Henry Lückewille]

{: .no_toc }
# Data Model

## Table of Contents
- [Overview](#overview)
- [Key Entities](#key-entities)
- [Entity Details](#entity-details)
  - [User](#1-user)
  - [Team](#2-team)
  - [Match](#3-match)
  - [Season](#4-season)
  - [Gameday](#5-gameday)
  - [Prediction](#6-prediction)
  - [Dataset Update](#7-dataset-update)


## Overview
This document provides a structured visualization and description of the data model used in the application. The following entities and their relationships reflect the actual implementation.

---

## Key Entities

- **User**
- **Team**
- **Match**
- **Season**
- **Gameday**
- **Prediction**
- **Dataset Update**

---

## Entity Details

### 1. User
**Attributes:**
- `id` (Primary Key)
- `username` (Unique)
- `password` (Hashed)
- `favourite_team` (Foreign Key to Team)

**Relationships:**
- A user has one favourite team.
- A user can make multiple predictions.

---

### 2. Team
**Attributes:**
- `id` (Primary Key)
- `name` (Unique)
- `league` (e.g., Bundesliga)
- `stadium`
- `coach`

**Relationships:**
- A team can be the favourite of multiple users.
- A team can participate in multiple matches.

---

### 3. Match
**Attributes:**
- `id` (Primary Key)
- `season_id` (Foreign Key to Season)
- `gameday_id` (Foreign Key to Gameday)
- `home_team_id` (Foreign Key to Team)
- `away_team_id` (Foreign Key to Team)
- `home_team_goals`
- `away_team_goals`
- `date`
- `time`

**Relationships:**
- A match belongs to one season and one gameday.
- A match involves two teams (home and away).

---

### 4. Season
**Attributes:**
- `id` (Primary Key)
- `year` (e.g., 2024)

**Relationships:**
- A season can have multiple matches.
- A season can have multiple gamedays.

---

### 5. Gameday
**Attributes:**
- `id` (Primary Key)
- `season_id` (Foreign Key to Season)
- `gameday_number` (e.g., 1, 2, 3, ...)

**Relationships:**
- A gameday belongs to one season.
- A gameday can have multiple matches.

---

### 6. Prediction
**Attributes:**
- `id` (Primary Key)
- `user_id` (Foreign Key to User)
- `match_id` (Foreign Key to Match)
- `home_team_win_probability`
- `draw_probability`
- `away_team_win_probability`
- `over_1_5_goals_probability`
- `over_2_5_goals_probability`

**Relationships:**
- A prediction is made by one user for one match.

---

### 7. Dataset Update
**Attributes:**
- `id` (Primary Key)
- `update_date`
- `status` (e.g., Success, Failed)
- `details` (e.g., Error messages, commit hash)

**Relationships:**
- A dataset update is related to the dataset used in the application.

