# **Bundesliga Predictor Repository**

**Bundesliga Predictor** is a web application built with Flask and SQLite. Developed as a projekt of the Full-Stack Web Development course at HWR Berlin, this repository contains the full codebase and documentation with GitHub Pages.

## **Repository Contents**  
This repository contains the source code for the Bundesliga Predictor app, including data processing, prediction logic, and a basic web interface.  
Additionally, there is a setup for **GitHub Pages documentation**, which you can view here:  
[Bundesliga Predictor Documentation](https://linuspiorkowsky.github.io/FS-Bundesliga/)  

---

## **Steps to Execute the App**  

### **Step 1: Set up a Python Virtual Environment**  
Run the following command to create and activate a virtual environment:  

```bash
python3 -m venv venv
```
or
```bash
source venv/bin/activate  # For Windows use 'venv\Scripts\activate'
```

### **Step 2: Install Requirements**
```bash
pip install -r requirements.txt
```

### **Step 3: Start the Development Server**

```bash
flask run
```

**Expected output:**

```plaintext
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment.
Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### **Step 4: Access the Application**
Go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to view the login page and start using the Bundesliga Predictor.

---

## Features
The **Bundesliga Predictor** has the following features:
- **Match Predictions:** Calculates probabilities for match outcomes based on historical and current team performance.
- **Team Insights:** Provides statistics on goals, wins, and efficiency metrics for each team.
- **Historic Results:** Provides Bundesliga outcomes from 2016 until today.
- **Live Updates:** Datasets are updated every week.

---

## NextGen Creators

Thank you for exploring our **Bundesliga Predictor** project! We, **Linus Piorkowsky** and **Henry Lückewille**, appreciate your interest and support. 
