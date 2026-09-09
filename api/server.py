import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import sqlite3
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Adjust paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from configs.config import RAW_DATA_DIR, COLUMNS, DATA_DIR
from src.data.database import DB_PATH, get_stats, get_recent_alerts, init_db
from src.inference.inference import InferencePipeline
from src.adaptive_learning.retrainer import AdaptiveRetrainer

app = FastAPI(
    title="AegisIDS API",
    description="Backend API for AegisIDS Adaptive & Explainable Intrusion Detection System",
    version="1.0.0"
)

# Enable CORS for Expo frontend (mobile & web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global lazy-loaded inference pipeline
pipeline: Optional[InferencePipeline] = None
test_dataset_cache: Optional[pd.DataFrame] = None
current_sample_index = 0

def get_pipeline():
    global pipeline
    if pipeline is None:
        init_db()
        pipeline = InferencePipeline()
    return pipeline

def get_test_data():
    global test_dataset_cache
    if test_dataset_cache is None:
        test_path = RAW_DATA_DIR / 'KDDTest+.txt'
        if test_path.exists():
            df = pd.read_csv(test_path, header=None)
            if len(df.columns) == len(COLUMNS) + 1:
                df.columns = COLUMNS + ['extra']
                df.drop('extra', axis=1, inplace=True)
            elif len(df.columns) == len(COLUMNS):
                df.columns = COLUMNS
            test_dataset_cache = df
        else:
            raise FileNotFoundError("Raw test dataset not found.")
    return test_dataset_cache

@app.on_event("startup")
def startup_event():
    init_db()
    print("AegisIDS API started and database verified.")

@app.get("/")
def root():
    return {
        "system": "AegisIDS",
        "status": "operational",
        "version": "1.0.0",
        "endpoints": [
            "/api/stats",
            "/api/alerts",
            "/api/live-sample",
            "/api/analyze",
            "/api/metrics",
            "/api/verified-samples",
            "/api/verify-sample",
            "/api/retrain"
        ]
    }

@app.get("/api/stats")
def get_system_stats():
    """Returns overview statistics on analyzed traffic and alert distributions."""
    stats = get_stats()
    
    # Also get severity counts
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT severity, COUNT(*) FROM alerts GROUP BY severity")
    severity_counts = dict(cursor.fetchall())
    
    cursor.execute("SELECT attack_type, COUNT(*) FROM alerts GROUP BY attack_type")
    attack_counts = dict(cursor.fetchall())
    conn.close()
    
    return {
        "stats": stats,
        "severity_breakdown": {
            "CRITICAL": severity_counts.get("CRITICAL", 0),
            "HIGH": severity_counts.get("HIGH", 0),
            "MODERATE": severity_counts.get("MODERATE", 0),
            "LOW": severity_counts.get("LOW", 0)
        },
        "attack_breakdown": attack_counts
    }

@app.get("/api/alerts")
def fetch_alerts(limit: int = 50):
    """Returns recent intrusion alerts with XAI reasons and recommendations."""
    alerts_df = get_recent_alerts(limit)
    if alerts_df.empty:
        return {"alerts": []}
    return {"alerts": alerts_df.to_dict(orient="records")}

@app.get("/api/live-sample")
def get_live_sample():
    """Simulates real-time network flow by processing the next record in the dataset."""
    global current_sample_index
    try:
        df = get_test_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if current_sample_index >= len(df):
        current_sample_index = 0
        
    record = df.iloc[[current_sample_index]]
    current_sample_index += 1
    
    pipe = get_pipeline()
    pred_info, alert, explanation = pipe.process_record(record)
    
    raw_record = record.to_dict(orient="records")[0]
    
    return {
        "index": current_sample_index,
        "actual_label": raw_record.get("attack_type", "unknown"),
        "prediction": pred_info,
        "alert": alert,
        "explanation": explanation,
        "flow_features": {
            "duration": raw_record.get("duration", 0),
            "protocol_type": raw_record.get("protocol_type", ""),
            "service": raw_record.get("service", ""),
            "flag": raw_record.get("flag", ""),
            "src_bytes": raw_record.get("src_bytes", 0),
            "dst_bytes": raw_record.get("dst_bytes", 0),
            "count": raw_record.get("count", 0),
            "dst_host_srv_count": raw_record.get("dst_host_srv_count", 0)
        }
    }

@app.post("/api/analyze")
def analyze_custom_record(data: Dict[str, Any] = Body(...)):
    """Analyze a single raw or feature dictionary."""
    pipe = get_pipeline()
    df = pd.DataFrame([data])
    pred_info, alert, explanation = pipe.process_record(df)
    return {
        "prediction": pred_info,
        "alert": alert,
        "explanation": explanation
    }

@app.get("/api/metrics")
def get_model_metrics():
    """Returns baseline and AegisIDS model comparison metrics."""
    metrics_path = BASE_DIR / 'results' / 'model_comparison.csv'
    if metrics_path.exists():
        df = pd.read_csv(metrics_path)
        return {"metrics": df.to_dict(orient="records")}
    return {"metrics": []}

@app.get("/api/verified-samples")
def get_verified_samples():
    """Returns candidate samples pending verification."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM verified_samples ORDER BY id DESC LIMIT 50", conn)
    conn.close()
    return {"samples": df.to_dict(orient="records")}

@app.post("/api/verify-sample")
def verify_sample(sample_id: int = Body(..., embed=True), verified_label: str = Body(..., embed=True)):
    """Analyst verifies a candidate anomaly sample."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE verified_samples SET verified_label = ?, status = 'VERIFIED' WHERE sample_id = ?",
        (verified_label, sample_id)
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Sample {sample_id} verified as {verified_label}"}

@app.post("/api/retrain")
def trigger_retraining():
    """Triggers controlled adaptive retraining on verified samples."""
    retrainer = AdaptiveRetrainer()
    success, message = retrainer.retrain_with_verification(min_samples=1)
    return {"success": success, "message": message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
