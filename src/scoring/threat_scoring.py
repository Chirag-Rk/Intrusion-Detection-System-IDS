import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import THREAT_THRESHOLDS

class ThreatScorer:
    def __init__(self, thresholds=THREAT_THRESHOLDS):
        self.thresholds = thresholds
        
    def calculate_score(self, decision, confidence, anomaly_score, severity_multiplier):
        """
        Calculate threat score 0-100 based on decision and features.
        """
        base_score = 0
        
        if decision == 'Normal':
            base_score = 10 * anomaly_score # small score based on anomaly
        elif decision == 'Anomalous/Unknown Attack':
            base_score = 40 + (20 * anomaly_score)
        elif decision == 'Known Attack':
            base_score = 60 + (15 * confidence)
        elif decision == 'High Confidence Attack':
            base_score = 75 + (20 * confidence) + (5 * anomaly_score)
            
        final_score = base_score * severity_multiplier
        
        # Cap at 100
        final_score = min(100.0, max(0.0, final_score))
        
        severity = self._get_severity(final_score)
        
        return round(final_score, 1), severity
        
    def _get_severity(self, score):
        if score <= self.thresholds['LOW']:
            return 'LOW'
        elif score <= self.thresholds['MODERATE']:
            return 'MODERATE'
        elif score <= self.thresholds['HIGH']:
            return 'HIGH'
        else:
            return 'CRITICAL'

if __name__ == "__main__":
    scorer = ThreatScorer()
    print(scorer.calculate_score('Normal', 0.9, 0.01, 0.0))
    print(scorer.calculate_score('Known Attack', 0.85, 0.03, 1.0))
    print(scorer.calculate_score('Anomalous/Unknown Attack', 0.5, 0.15, 1.2))
    print(scorer.calculate_score('High Confidence Attack', 0.99, 0.20, 1.5))
