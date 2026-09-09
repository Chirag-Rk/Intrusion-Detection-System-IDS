import numpy as np

class DecisionEngine:
    def __init__(self, anomaly_threshold):
        self.anomaly_threshold = anomaly_threshold
        
    def predict(self, dnn_prob, anomaly_score):
        """
        Combines DNN prediction and anomaly score.
        Returns:
            decision (str): 'Normal', 'Known Attack', 'Anomalous/Unknown Attack', 'High Confidence Attack'
            severity_multiplier (float): A multiplier to use for threat scoring.
        """
        dnn_pred = 1 if dnn_prob > 0.5 else 0
        dnn_confidence = dnn_prob if dnn_pred == 1 else (1 - dnn_prob)
        
        is_anomalous = anomaly_score > self.anomaly_threshold
        
        if dnn_pred == 1 and is_anomalous:
            return 'High Confidence Attack', 1.5, dnn_confidence
        elif dnn_pred == 1 and not is_anomalous:
            return 'Known Attack', 1.0, dnn_confidence
        elif dnn_pred == 0 and is_anomalous:
            return 'Anomalous/Unknown Attack', 1.2, dnn_confidence
        else:
            return 'Normal', 0.0, dnn_confidence

if __name__ == "__main__":
    # Simple test
    engine = DecisionEngine(anomaly_threshold=0.05)
    print(engine.predict(dnn_prob=0.9, anomaly_score=0.02)) # Known Attack
    print(engine.predict(dnn_prob=0.9, anomaly_score=0.10)) # High Confidence Attack
    print(engine.predict(dnn_prob=0.1, anomaly_score=0.08)) # Anomalous
    print(engine.predict(dnn_prob=0.1, anomaly_score=0.02)) # Normal
