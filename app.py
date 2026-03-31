from flask import Flask, render_template, request, redirect, url_for
import sqlite3

# Machine Learning Imports
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
import pandas as pd
import numpy as np
app = Flask(__name__)

DATABASE = "crime.db"

# -------- Create Table --------
def init_db():
     conn = sqlite3.connect(DATABASE)
     cursor = conn.cursor()
     cursor.execute("""
        CREATE TABLE IF NOT EXISTS crimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crime_type TEXT NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL
        )
     """)
     conn.commit()
     conn.close()

init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "1234":
            return redirect(url_for('dashboard'))
        else:
            return "Invalid Username or Password"

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ---------------- ADD CRIME ----------------
@app.route('/addcrime', methods=['GET', 'POST'])
def add_crime():
    if request.method == 'POST':
        crime_type = request.form['crime_type']
        location = request.form['location']
        date = request.form['date']
        description = request.form['description']

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO crimes (crime_type, location, date, description)
            VALUES (?, ?, ?, ?)
        """, (crime_type, location, date, description))
        conn.commit()
        conn.close()

        return redirect(url_for('view_crime'))

    return render_template("add_crime.html")

# -------- VIEW CRIME --------
@app.route('/viewcrime')
def view_crime():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM crimes")
    crimes = cursor.fetchall()
    conn.close()

    return render_template("view_crime.html", crimes=crimes)

@app.route('/crimeanalysis')
def crime_analysis():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Crime Type, Count, Last Occurred Date
    cursor.execute("""
                   SELECT crime_type,
                          COUNT(*)  as total_cases,
                          MAX(date) as last_occurred
                   FROM crimes
                   GROUP BY crime_type
                   """)

    data = cursor.fetchall()
    conn.close()

    return render_template("crime_analysis.html", data=data)

@app.route('/chart')
def chart():
    import sqlite3
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT crime_type, COUNT(*) 
        FROM crimes 
        GROUP BY crime_type
    """)
    crime_type_data = cursor.fetchall()

    cursor.execute("""
        SELECT substr(date, 1, 7), COUNT(*) 
        FROM crimes 
        GROUP BY substr(date, 1, 7)
    """)
    monthly_data = cursor.fetchall()

    conn.close()

    return render_template(
         "chart.html",
         crime_type_labels=[row[0] for row in crime_type_data],
         crime_type_values=[row[1] for row in crime_type_data],
         monthly_labels=[row[0] for row in monthly_data],
         monthly_values=[row[1] for row in monthly_data]
    )

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    conn = sqlite3.connect(DATABASE)
    df = pd.read_sql_query("SELECT * FROM crimes", conn)
    conn.close()

    result = None
    suggestion = None
    percentage = 0

    if request.method == 'POST':
        input_location = request.form['location']
        input_crime = request.form['crime_type']

        # Encode categorical data
        le_location = LabelEncoder()
        le_crime = LabelEncoder()

        df['location_encoded'] = le_location.fit_transform(df['location'])
        df['crime_encoded'] = le_crime.fit_transform(df['crime_type'])

        # Target: Assume High Risk if crime count > average
        crime_counts = df.groupby(['location', 'crime_type']).size().reset_index(name='count')
        avg_count = crime_counts['count'].mean()
        crime_counts['risk'] = np.where(crime_counts['count'] >= avg_count * 0.7, 1, 0)

        # Encode again for training
        crime_counts['loc_enc'] = le_location.fit_transform(crime_counts['location'])
        crime_counts['crime_enc'] = le_crime.fit_transform(crime_counts['crime_type'])

        X = crime_counts[['loc_enc', 'crime_enc']]
        y = crime_counts['risk']

        model = LogisticRegression()
        model.fit(X, y)

        # Encode input
        try:
            loc_val = le_location.transform([input_location])[0]
            crime_val = le_crime.transform([input_crime])[0]

            prediction = model.predict([[loc_val, crime_val]])[0]

            selected = crime_counts[
                (crime_counts['location'] == input_location) &
                (crime_counts['crime_type'] == input_crime)
                ]

            if not selected.empty:
                count = selected['count'].values[0]
            else:
                count = 0

            # Risk Levels
            if count >= avg_count * 1.2:
                result = "HIGH RISK"
                percentage = 85
                suggestion = "Immediate preventive action required. Increase police patrol and surveillance."

            elif count >= avg_count * 0.7:
                result = "MEDIUM RISK"
                percentage = 60
                suggestion = "Moderate risk. Strengthen monitoring and public awareness."

            else:
                result = "LOW RISK"
                percentage = 30
                suggestion = "Low risk area. Continue regular monitoring."

        except:
            result = "Insufficient Data"
            suggestion = "No previous records found for this combination."

    locations = df['location'].unique()
    crime_types = df['crime_type'].unique()

    return render_template(
        "prediction.html",
        result=result,
        suggestion=suggestion,
        percentage=percentage,
        input_location=input_location if request.method == 'POST' else None,
        input_crime=input_crime if request.method == 'POST' else None,
        locations=locations,
        crime_types=crime_types
    )
@app.route('/logout')
def logout():
    return redirect('/login')
if __name__ == '__main__':
    app.run(debug=True)