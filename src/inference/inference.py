import numpy as np
import pandas as pd
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import MODELS_DIR
from src.preprocessing.preprocessor import DataPreprocessor
from src.scoring.decision_engine import DecisionEngine
from src.scoring.threat_scoring import ThreatScorer
from src.explainability.xai import XAIExplainer
from src.alerts.alert_generator import AlertGenerator
from src.data.database import init_db, insert_traffic_record, insert_alert
from tensorflow.keras.models import load_model
import joblib

class InferencePipeline:
    def __init__(self):
        print("Initializing Inference Pipeline...")
        # Ensure DB is initialized
        init_db()
        
        # Load Preprocessor
        self.preprocessor = DataPreprocessor()
        try:
            self.preprocessor.load_artifacts()
        except:
            print("Warning: Could not load preprocessing artifacts. Have you run the preprocessor?")
            
        # Load Models
        try:
            self.dnn_model = load_model(MODELS_DIR / 'classifier' / 'dnn_model.h5')
            self.autoencoder = load_model(MODELS_DIR / 'anomaly_detector' / 'autoencoder.h5', compile=False)
            self.anomaly_threshold = joblib.load(MODELS_DIR / 'anomaly_detector' / 'threshold.pkl')
        except:
            print("Warning: Could not load models. Have you trained them?")
            self.anomaly_threshold = 0.05
            
        # Initialize Engines
        self.decision_engine = DecisionEngine(self.anomaly_threshold)
        self.threat_scorer = ThreatScorer()
        try:
            self.xai = XAIExplainer(sample_size=50)
        except:
            print("Warning: XAI Explainer could not be initialized.")
            self.xai = None
        self.alert_gen = AlertGenerator()
        
    def process_record(self, record_df):
        """
        Process a single record (pandas DataFrame)
        """
        # Preprocess
        try:
            X, _ = self.preprocessor.transform(record_df)
        except Exception as e:
            print(f"Error in preprocessing: {e}")
            return None
            
        # Predict Known Attack (DNN)
        dnn_prob = self.dnn_model.predict(X, verbose=0)[0][0]
        
        # Detect Anomaly (Autoencoder)
        reconstruction = self.autoencoder.predict(X, verbose=0)
        anomaly_score = np.mean(np.power(X - reconstruction, 2), axis=1)[0]
        
        # Decision Fusion
        decision, severity_multiplier, confidence = self.decision_engine.predict(dnn_prob, anomaly_score)
        
        # Threat Scoring
        threat_score, severity = self.threat_scorer.calculate_score(decision, confidence, anomaly_score, severity_multiplier)
        
        # Explainability
        explanation = []
        if severity in ['MODERATE', 'HIGH', 'CRITICAL'] and self.xai:
            explanation = self.xai.explain_instance(X)
            
        # Result compilation
        prediction_info = {
            'decision': decision,
            'confidence': float(confidence),
            'anomaly_score': float(anomaly_score),
            'threat_score': threat_score,
            'severity': severity,
            'features_json': record_df.to_json(orient='records')
        }
        
        # Logging to DB
        insert_traffic_record(prediction_info)
        
        # Alert Generation
        alert = self.alert_gen.generate_alert(prediction_info, explanation)
        if alert:
            insert_alert(alert)
            
        return prediction_info, alert, explanation

if __name__ == "__main__":
    pipeline = InferencePipeline()
    print("Pipeline ready.")
