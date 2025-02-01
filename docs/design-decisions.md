---
title: Design Decisions
nav_order: 3
---

{: .label }
[Linus Piorkowsky & Henry Lückewille]

{: .no_toc }
# Design Decisions

<details open markdown="block">
{: .text-delta }
<summary>Table of contents</summary>
+ ToC
{: toc }
</details>

---

## 01: Displaying Bundesliga Results 

### Meta  

Status  
: **Decided**  

Updated - Decision Date
: 07-Nov-2024  

### Problem Statement  

To provide **historical insights** for fans and data-driven users, we needed a way to **display past Bundesliga results**. The key objectives were:  
- Allowing users to **analyze performance trends** over multiple seasons.  
- Helping fans gain **contextual insights** beyond just predictions.  
- Keeping the dataset manageable while providing meaningful data.  

### Decision  

We created a **results page** that displays Bundesliga results from the **past 8 seasons**. This timeframe ensures:  
- **Relevant historical data** without overwhelming users with excessive information.  
- **Trends and patterns** can be identified for informed decision-making.  
- A balance between **data depth and performance efficiency**.  

### Regarded Options  

1. **Show past 8 seasons of Bundesliga results (Chosen)**  
2. **Include all available historical data (Rejected)**  

| Criterion              | Past 8 Seasons (Chosen) | Full History (Rejected) |
|------------------------|----------------------|------------------------|
| **Relevance**         | Focused on recent trends | Includes outdated data |
| **Performance**       | Faster loading, optimized | Can slow down the app |
| **User Experience**   | Provides useful insights | Overwhelming for casual users |
| **Data Management**   | Manageable dataset | Large, harder to maintain |

---

### **Why We Chose an 8-Year Results Page**  
✅ **Ensures meaningful trends** – Focuses on recent performances.  
✅ **Balances detail & usability** – Enough data without slowing down the app.  
✅ **Useful for fans & analysts** – Helps both casual users and stat-driven bettors.  

By limiting the dataset to the **last 8 seasons**, the Bundesliga Predictor app provides **clear, relevant, and efficient insights** while maintaining high performance.

---

## 02: User Can Choose Favorite Team During Account Creation

### Meta

Status  
: **Decided**  

Updated - Decision Date
: 17-Nov-2024  

### Problem Statement

Users want a personalized experience when using the Bundesliga Predictor app. Allowing them to select a favorite team during account creation ensures they receive customized insights and data relevant to their preferences.  

### Decision  

We implemented a feature that lets users **choose their favorite team** when creating an account. This selection is stored and used to provide tailored team performance insights directly on their dashboard.  

### Regarded Options  

1. **Allow users to select a favorite team at sign-up (Chosen)**  
2. **Let users manually search for team insights each time (Rejected)**  

| Criterion             | Favorite Team Selection at Sign-Up | Manual Team Search |
|-----------------------|----------------------------------|--------------------|
| **User Experience**   | Personalized and engaging       | Less engaging     |
| **Convenience**       | Saves time, automatic insights  | Requires more user effort |
| **Implementation**    | Simple to store and display     | No additional setup required |
| **Flexibility**       | Users can change preferences    | Users pick a team manually each time |

---

## 03: Team Performance Metrics for Additional Insights  

### Meta  

Status  
: **Decided**  

Updated - Decision Date:   
18-Nov-2024  

### Problem Statement  

Beyond match predictions, users want deeper insights into **team performance**, such as goals, wins, efficiency, and trends. This helps both casual fans and data-driven users make more informed decisions.  

### Decision  

We included a **Team Performance Metrics** feature, which provides:  
- **Detailed team statistics** (win/loss record, goal averages, dominance stats, goals conceeded).  
- **Historical performance tracking** to see trends over last games.  

### Regarded Options  

1. **Add Team Performance Metrics (Chosen)**  
2. **Only Provide Match Predictions (Rejected)**
3. **Comparison whith other Teams (Denied)** 

| Criterion             | Team Performance Metrics  | Only Match Predictions |
|-----------------------|-------------------------|------------------------|
| **User Engagement**   | Higher, more insights   | Lower, only predictions |
| **Depth of Data**     | Detailed stats per team | Focused only on matches |
| **Use Cases**        | Useful for fans & analysts | Limited to betting or predictions |
| **Implementation**    | Moderate complexity    | Simpler to maintain |

---

## 04: Name Mapping for Consistent Team Names Across Datasets  

### Meta  

Status  
: **Decided**  

Updated - Decision Date
: 25-Nov-2024  

### Problem Statement  

The Bundesliga Predictor app relies on **two different datasets**:  
- **Updated_Games.csv** (contains historical results)  
- **gameplan_24_25.csv** (contains future match schedules)  

A major challenge was that **team names were not consistent** across these datasets, leading to mismatches and inaccurate analyses. Some teams had different spellings or naming conventions, which made it difficult to merge and compare data effectively.  

### Decision  

We implemented a **name harmonization function** that:  
- Extracts the **official team names** from `gameplan_24_25.csv`.  
- Uses **fuzzy matching** (via RapidFuzz) to map inconsistent names in `Updated_Games.csv` to their correct counterparts.  
- Applies a **threshold-based approach** to ensure high-confidence matches while keeping unmatched names unchanged.  
- **Manually fixes known issues**, such as **"FC Koln"**, which caused repeated problems.  

### Regarded Options  

1. **Harmonize team names using fuzzy matching (Chosen)**  
2. **Manually create a name mapping list (Rejected)**  

| Criterion              | Fuzzy Matching (Chosen) | Manual Mapping (Rejected) |
|------------------------|----------------------|---------------------------|
| **Automation**        | Fully automated      | Requires manual updates   |
| **Scalability**       | Works for future teams | Needs constant maintenance |
| **Accuracy**         | High with threshold   | Depends on human input    |
| **Implementation**    | Moderate complexity  | Simple but time-intensive |

---

### **Why We Chose Automated Name Harmonization**  
✅ **Ensures consistency** – Both datasets use the same official team names.  
✅ **Saves time** – No need for constant manual corrections.  
✅ **Future-proof** – Works dynamically, even if new team names are added.  

By **automatically mapping team names**, the Bundesliga Predictor app can **accurately merge historical and future data**, ensuring better predictions and insights for users.

---

## 05: Prediction Logic Based on Statistics vs. RNN Model  

### Meta  

Status  
: **Decided**  

Updated - Decision Date
: 25-Nov-2024  

### Problem Statement  

To generate match predictions, we needed to decide between **a statistics-based prediction model** or a **Recurrent Neural Network (RNN)-based model**. The goal was to provide users with accurate, interpretable, and reliable predictions while keeping the system efficient and maintainable.  

### Decision  

We chose a **statistical approach** for match predictions instead of an RNN model. The statistical model:  
- Uses **historical match data, team performance metrics, and efficiency calculations**.  
- **Weighs past and current season performance** to adjust accuracy over time.  
- Provides **easily interpretable** probability distributions (home win, draw, away win).  

The decision was made to balance **accuracy, explainability, and computational efficiency**.  

### Regarded Options  

1. **Statistics-Based Prediction Logic (Chosen)**  
2. **RNN-Based Prediction Model (Rejected)**  

| Criterion              | Statistics-Based Model         | RNN-Based Model |
|------------------------|--------------------------------|-----------------|
| **Interpretability**   | High – clear probability logic | Low – complex neural network decisions |
| **Computational Cost** | Low – efficient calculations   | High – requires GPU/ML processing |
| **Data Requirements**  | Moderate – historical match data | High – requires large datasets |
| **Accuracy**           | Consistent for structured data | Potentially better, but requires tuning |
| **Maintenance**        | Easy – simple to update models | Complex – needs ongoing retraining |

---

### **Why We Chose Statistics-Based Predictions**  
✅ **Easy to understand** – Users can see how probabilities are calculated.  
✅ **No deep learning complexity** – Avoids the need for constant retraining and fine-tuning.  
✅ **Computationally efficient** – Works instantly without expensive machine learning processing.  
✅ **Reliable with available data** – Doesn't require large datasets or external training.  

By choosing a statistics-based approach, we ensured that the **Bundesliga Predictor delivers accurate, transparent, and efficient match predictions** without the overhead of an AI model.  

---

## 06: Account Settings 

### Meta  

Status  
: **Decided**  

Updated - Decision Date:
: 28-Nov-2024  

### Problem Statement  

Users need a way to **manage and update their account settings**, including:  
- **Changing their password** for security reasons.  
- **Updating their username** for personalization.  
- **Modifying their favorite team** to adjust their preferences.  

The challenge was to implement **a simple yet secure solution** that ensures user control without compromising data integrity.  

### Decision  

We implemented an **account settings page** where users can:  
- Securely **change their password** with verification.  
- Edit their **username** while ensuring uniqueness.  
- Update their **favorite team**, which affects their personalized insights.  

This decision was made to enhance **user experience and personalization** while maintaining a straightforward and secure implementation.  

### Regarded Options  

1. **Allow users to modify account settings via a dedicated page (Chosen)**  
2. **Restrict account settings changes (Rejected)**  

| Criterion              | Account Settings Feature (Chosen) | No Account Changes (Rejected) |
|------------------------|---------------------------------|------------------------------|
| **User Experience**    | High – users have control      | Low – fixed data, no flexibility |
| **Security**           | Secure updates with verification | Secure but restrictive |
| **Personalization**    | Users can customize preferences | No personalization |
| **Implementation**     | Moderate complexity           | Simple, but limits functionality |

---

### **Why We Chose Account Settings Management**  
✅ **Enhances user experience** – Users can personalize their accounts freely.  
✅ **Improves security** – Password updates reduce risks of unauthorized access.  
✅ **Flexibility** – Users can change their preferences at any time.  

By allowing users to modify their **password, username, and favorite team**, the Bundesliga Predictor app ensures **greater personalization, security, and control** over their account.  

These design decisions were made to optimize user experience, provide meaningful insights, and ensure reliable data updates while maintaining simplicity in implementation.

---

## 07: Implementing a Betting Integration (Denied)  

### Meta  

Status  
: **Denied**  

Updated - Decision Date:
: 03-Dec-2024  

### Problem Statement  

An idea was proposed to integrate **direct betting options** within the Bundesliga Predictor app. This would allow users to place bets directly through the platform using third-party betting providers.  

While this feature could add **monetization opportunities** and enhance user engagement, it introduced several **legal, ethical, and technical challenges**.  

### Decision  

We decided **not to implement direct betting integration**, because:  
- **Legal complexities** – Different countries have strict regulations on online betting, making implementation risky and complicated.  
- **Ethical concerns** – Encouraging betting directly within the app could create **responsible gambling issues**.  
- **Focus on insights** – Our goal is to provide **data-driven predictions**, not facilitate gambling transactions.  

### Regarded Options  

1. **Provide betting insights but no integration (Chosen)**  
2. **Allow users to place bets through third-party providers (Rejected)**  

| Criterion              | Insights-Only (Chosen) | Betting Integration (Rejected) |
|------------------------|----------------------|-------------------------------|
| **Legal Compliance**  | No legal risks       | High regulatory complexity |
| **User Experience**   | Focus on statistics  | Might shift focus to gambling |
| **Ethical Concerns**  | No direct influence  | Could promote unhealthy betting |
| **Implementation**    | Simple & data-based  | Requires partnerships & APIs |

---

### **Why We Rejected Betting Integration**  
❌ **Avoids legal and compliance risks** – No need for gambling licenses.  
❌ **Keeps the app focused on insights** – Maintains credibility as a data-driven tool.  
❌ **Prevents ethical concerns** – Does not promote excessive gambling behavior.  

By **excluding direct betting**, the Bundesliga Predictor app remains a **neutral, data-driven prediction tool** rather than a gambling platform.  

---

## 08: Dataset Update at Application Start  

### Meta  

Status  
: **Decided**  

Updated - Decision Date:
: 05-Dec-2024  

### Problem Statement  

The app needs to work with the most up-to-date match data. Without regular updates, predictions could become inaccurate. We had to decide whether to update the dataset every time the application starts or to maintain a live server for dataset updates.  

### Decision  

We chose to **update the dataset every time the app starts**. The process:  
1. **Download the latest dataset** at launch.  
2. **Compare it to the existing dataset** (check for new rows).  
3. **Update only if new data is available**, otherwise keep the old dataset.  

### Regarded Options  

1. **Update dataset at application start (Chosen)**  
2. **Use a continuously running server to update data (Rejected)**  

| Criterion             | Update on App Start  | Live Server for Updates |
|-----------------------|---------------------|-------------------------|
| **Data Freshness**    | Always latest at launch | Updates continuously |
| **Server Costs**      | None, local update  | Requires active hosting |
| **Complexity**        | Simple local check  | Needs backend infrastructure |
| **Reliability**       | Works offline with latest data | Dependent on server uptime |

### **Why We Chose to Update at App Start**  
✅ **Ensures data accuracy** – The app always runs on the latest available dataset.  
✅ **No additional infrastructure required** – Avoids the need for a dedicated update server.  
✅ **Reliable even without internet** – Works with the most recent data available at launch.  

By **updating at startup**, the Bundesliga Predictor app stays **lightweight, efficient, and always up-to-date**, providing users with **accurate predictions without unnecessary complexity**.  
