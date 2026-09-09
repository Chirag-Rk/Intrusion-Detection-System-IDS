import unittest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.scoring.decision_engine import DecisionEngine
from src.scoring.threat_scoring import ThreatScorer
from src.alerts.alert_generator import AlertGenerator
from src.preprocessing.preprocessor import DataPreprocessor

class TestAegisPipeline(unittest.TestCase):

    def test_decision_engine(self):
        engine = DecisionEngine(anomaly_threshold=0.1)
        
        # Test High Confidence Attack
        dec, mult, conf = engine.predict(dnn_prob=0.95, anomaly_score=0.25)
        self.assertEqual(dec, 'High Confidence Attack')
        self.assertGreater(mult, 1.0)
        
        # Test Normal
        dec, mult, conf = engine.predict(dnn_prob=0.05, anomaly_score=0.02)
        self.assertEqual(dec, 'Normal')
        self.assertEqual(mult, 0.0)
        
        # Test Anomaly / Zero-day
        dec, mult, conf = engine.predict(dnn_prob=0.2, anomaly_score=0.35)
        self.assertEqual(dec, 'Anomalous/Unknown Attack')
        
    def test_threat_scorer(self):
        scorer = ThreatScorer()
        
        # Critical Threat
        score, sev = scorer.calculate_score('High Confidence Attack', 0.99, 0.5, 1.5)
        self.assertGreaterEqual(score, 75)
        self.assertEqual(sev, 'CRITICAL')
        
        # Low Threat (Normal)
        score, sev = scorer.calculate_score('Normal', 0.95, 0.01, 0.0)
        self.assertLessEqual(score, 25)
        self.assertEqual(sev, 'LOW')

    def test_alert_generator(self):
        gen = AlertGenerator()
        pred_info = {
            'decision': 'High Confidence Attack',
            'confidence': 0.98,
            'anomaly_score': 0.45,
            'threat_score': 95.0,
            'severity': 'CRITICAL'
        }
        explanation = [('src_bytes', 0.55), ('dst_bytes', 0.32)]
        alert = gen.generate_alert(pred_info, explanation)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert['Severity'], 'CRITICAL')
        self.assertIn('ALT-', alert['Alert ID'])
        self.assertIn('src_bytes', alert['Reason'])

    def test_preprocessor_instantiation(self):
        preprocessor = DataPreprocessor()
        self.assertIsNotNone(preprocessor)

if __name__ == '__main__':
    unittest.main()
