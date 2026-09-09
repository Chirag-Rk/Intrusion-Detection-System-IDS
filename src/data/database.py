import sqlite3
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
import os

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import DATA_DIR

DB_PATH = DATA_DIR / 'aegis_ids.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Traffic Records Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS traffic_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        prediction TEXT,
        confidence REAL,
        anomaly_score REAL,
        threat_score REAL,
        severity TEXT,
        features_json TEXT
    )
    ''')
    
    # Alerts Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id TEXT PRIMARY KEY,
        timestamp TEXT,
        attack_type TEXT,
        confidence TEXT,
        anomaly_score TEXT,
        threat_score TEXT,
        severity TEXT,
        reason TEXT,
        recommendation TEXT,
        status TEXT DEFAULT 'NEW'
    )
    ''')
    
    # Verified Samples for Adaptive Learning
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS verified_samples (
        sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        features_json TEXT,
        predicted_label TEXT,
        verified_label TEXT,
        status TEXT DEFAULT 'PENDING'
    )
    ''')
    
    conn.commit()
    conn.close()
    
def insert_traffic_record(record):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO traffic_records (timestamp, prediction, confidence, anomaly_score, threat_score, severity, features_json)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        record['decision'],
        record['confidence'],
        record['anomaly_score'],
        record['threat_score'],
        record['severity'],
        record.get('features_json', '{}')
    ))
    conn.commit()
    conn.close()

def insert_alert(alert):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR IGNORE INTO alerts (alert_id, timestamp, attack_type, confidence, anomaly_score, threat_score, severity, reason, recommendation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        alert['Alert ID'], alert['Timestamp'], alert['Attack Type'], 
        alert['Confidence'], alert['Anomaly Score'], alert['Threat Score'], 
        alert['Severity'], alert['Reason'], alert['Recommendation']
    ))
    conn.commit()
    conn.close()
    
def get_recent_alerts(limit=50):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM alerts ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    return df

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM traffic_records")
    total_traffic = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM traffic_records WHERE prediction != 'Normal'")
    malicious = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE severity = 'CRITICAL'")
    critical_alerts = cursor.fetchone()[0]
    
    conn.close()
    return {
        'total_analyzed': total_traffic,
        'malicious_detected': malicious,
        'normal_traffic': total_traffic - malicious,
        'critical_alerts': critical_alerts
    }

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
