import sqlite3
import random

crime_types = [
    "Phishing",
    "Online Fraud",
    "Identity Theft",
    "Cyber Bullying",
    "Hacking",
    "Credit Card Scam",
    "Fake Job Scam",
    "OTP Fraud",
    "Social Media Hacking",
    "UPI Fraud"
]

locations = [
    "Hyderabad",
    "Mumbai",
    "Delhi",
    "Bangalore",
    "Chennai",
    "Kolkata",
    "Pune",
    "Ahmedabad"
]
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "crime.db")

conn = sqlite3.connect(db_path)


conn = sqlite3.connect
conn.close()

print("1000 records inserted successfully!")
