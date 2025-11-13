# import_csv.py
import sqlite3
import pandas as pd
from datetime import datetime
import os

DB = os.getenv("DB_FILE", "potholes_demo.db")

def create_tables(conn):
    conn.execute('''
    CREATE TABLE IF NOT EXISTS potholes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT,
      description TEXT,
      lat REAL,
      lon REAL,
      photo_filename TEXT,
      reported_by TEXT,
      reported_at TEXT,
      city TEXT,
      severity INTEGER,
      status TEXT DEFAULT 'pending',
      assigned_official TEXT
    );
    ''')
    conn.commit()

def import_csv(csv_file):
    df = pd.read_csv(csv_file)
    conn = sqlite3.connect(DB)
    create_tables(conn)
    cur = conn.cursor()
    inserted = 0
    for _, row in df.iterrows():
        try:
            cur.execute('''
            INSERT INTO potholes (title,description,lat,lon,photo_filename,reported_by,reported_at,city,severity)
            VALUES (?,?,?,?,?,?,?,?,?)
            ''', (row.get('title'), row.get('description'), float(row.get('lat')), float(row.get('lon')),
                  None, row.get('reported_by'), str(row.get('reported_at')), row.get('city'), int(row.get('severity'))))
            inserted += 1
        except Exception as e:
            print("Skipping row due to", e)
    conn.commit()
    conn.close()
    print("Imported", inserted, "rows into", DB)

if __name__ == "__main__":
    import_csv("demo_potholes.csv")
