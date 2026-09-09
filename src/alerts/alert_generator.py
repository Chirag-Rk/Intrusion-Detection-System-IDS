import uuid
from datetime import datetime

class AlertGenerator:
    def __init__(self):
        pass
        
    def generate_alert(self, prediction_info, explanation):
        """
        prediction_info: dict containing type, confidence, anomaly_score, threat_score, severity
        explanation: list of top features (from XAI)
        """
        # Only generate alerts for non-normal traffic or high anomalies
        if prediction_info['severity'] == 'LOW' and prediction_info['decision'] == 'Normal':
            return None
            
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build explanation string
        reason = "\n".join([f"- {feat}: {val:+.4f}" for feat, val in explanation])
        
        # Determine recommendation
        if prediction_info['severity'] == 'CRITICAL':
            rec = "Immediate investigation required. Isolate source IP and inspect related flows."
        elif prediction_info['severity'] == 'HIGH':
            rec = "High priority investigation. Check host logs and network IDS for correlated events."
        elif prediction_info['severity'] == 'MODERATE':
            rec = "Monitor traffic. May be anomalous benign behavior or early reconnaissance."
        else:
            rec = "Low priority alert. Potential false positive or minor anomaly."
            
        alert_data = {
            'Alert ID': alert_id,
            'Timestamp': timestamp,
            'Attack Type': prediction_info['decision'],
            'Confidence': f"{prediction_info['confidence']*100:.1f}%",
            'Anomaly Score': f"{prediction_info['anomaly_score']:.4f}",
            'Threat Score': f"{prediction_info['threat_score']}/100",
            'Severity': prediction_info['severity'],
            'Reason': reason,
            'Recommendation': rec
        }
        
        return alert_data
        
    def format_alert_text(self, alert_data):
        if not alert_data:
            return ""
            
        alert_text = f"🚨 {alert_data['Severity']} INTRUSION ALERT [{alert_data['Alert ID']}]\n"
        alert_text += f"Timestamp: {alert_data['Timestamp']}\n"
        alert_text += f"Attack Type: {alert_data['Attack Type']}\n"
        alert_text += f"Confidence: {alert_data['Confidence']}\n"
        alert_text += f"Anomaly Score: {alert_data['Anomaly Score']}\n"
        alert_text += f"Threat Score: {alert_data['Threat Score']}\n\n"
        alert_text += f"Top Contributing Features:\n{alert_data['Reason']}\n\n"
        alert_text += f"Recommendation: {alert_data['Recommendation']}\n"
        
        return alert_text

if __name__ == "__main__":
    generator = AlertGenerator()
    pred_info = {
        'decision': 'DoS',
        'confidence': 0.964,
        'anomaly_score': 0.91,
        'threat_score': 92,
        'severity': 'CRITICAL'
    }
    exp = [('src_bytes', 0.42), ('count', 0.31), ('dst_bytes', 0.18)]
    
    alert = generator.generate_alert(pred_info, exp)
    print(generator.format_alert_text(alert))
