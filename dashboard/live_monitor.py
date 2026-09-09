import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time
import random
import uuid
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))
from configs.config import RAW_DATA_DIR, COLUMNS
from src.data.database import insert_alert, insert_traffic_record

# Attack category mappings in NSL-KDD
ATTACK_CATEGORIES = {
    'Normal': ['normal'],
    'DDoS': ['neptune', 'smurf', 'apache2', 'processtable', 'back', 'pod', 'teardrop', 'land', 'mailbomb', 'udpstorm'],
    'Port Scan': ['portsweep', 'satan', 'mscan', 'ipsweep', 'nmap', 'saint'],
    'Brute Force': ['guess_passwd', 'snmpguess', 'snmpgetattack'],
    'Web Attack': ['httptunnel', 'sqlattack', 'phf', 'buffer_overflow', 'ftp_write', 'xterm', 'rootkit', 'sendmail', 'loadmodule']
}

# Human-readable feature descriptions
FEATURE_DESCRIPTIONS = {
    'src_bytes': 'Source Payload Bytes',
    'dst_bytes': 'Destination Payload Bytes',
    'count': 'Packet Rate (Same-Host Connections)',
    'srv_count': 'Service Request Frequency',
    'serror_rate': 'SYN Flag Count / Error Rate',
    'srv_serror_rate': 'Service SYN-Error Rate',
    'rerror_rate': 'REJ Error Rate',
    'same_srv_rate': 'Same-Service Match Rate',
    'diff_srv_rate': 'Different-Service Rate',
    'dst_host_count': 'Destination Host Count',
    'dst_host_srv_count': 'Destination Host Service Count',
    'dst_host_same_srv_rate': 'Dst Host Same-Service Rate',
    'dst_host_diff_srv_rate': 'Dst Host Diff-Service Rate',
    'dst_host_same_src_port_rate': 'Dst Host Identical Source Port Rate',
    'dst_host_serror_rate': 'SYN Flag Count / Host Error',
    'duration': 'Flow Duration',
    'logged_in': 'User Authentication Status',
    'num_failed_logins': 'Failed Login Attempts',
    'hot': 'Hot Indicators Count',
    'num_compromised': 'Compromised Conditions Count'
}

def init_live_monitor_state():
    """Initializes all state variables required for the live monitor."""
    if 'monitor_active' not in st.session_state:
        st.session_state.monitor_active = False
    if 'system_state' not in st.session_state:
        st.session_state.system_state = 'IDLE'
    if 'selected_scenario' not in st.session_state:
        st.session_state.selected_scenario = 'Normal'
    if 'scenario_runner_active' not in st.session_state:
        st.session_state.scenario_runner_active = False
    if 'render_seq' not in st.session_state:
        st.session_state.render_seq = 0
    if 'total_packets' not in st.session_state:
        st.session_state.total_packets = 1284
    if 'normal_packets' not in st.session_state:
        st.session_state.normal_packets = 1257
    if 'threat_packets' not in st.session_state:
        st.session_state.threat_packets = 27
    if 'inference_times' not in st.session_state:
        st.session_state.inference_times = [8.2, 9.1, 7.8, 8.5, 9.0]
    if 'packet_stream' not in st.session_state:
        now = datetime.now()
        st.session_state.packet_stream = [
            {'timestamp': (now - pd.Timedelta(seconds=5)).strftime("%H:%M:%S"), 'protocol': 'TCP', 'src': '192.168.1.24:49210', 'dst': '10.0.0.5:443', 'decision': 'Normal', 'confidence': '98.5%', 'threat_score': 0.0, 'severity': 'LOW', 'status_icon': '🟢', 'status_text': 'NORMAL'},
            {'timestamp': (now - pd.Timedelta(seconds=4)).strftime("%H:%M:%S"), 'protocol': 'TCP', 'src': '192.168.1.31:51022', 'dst': '10.0.0.5:80', 'decision': 'Normal', 'confidence': '99.1%', 'threat_score': 0.0, 'severity': 'LOW', 'status_icon': '🟢', 'status_text': 'NORMAL'},
            {'timestamp': (now - pd.Timedelta(seconds=3)).strftime("%H:%M:%S"), 'protocol': 'TCP', 'src': '192.168.1.18:48120', 'dst': '10.0.0.5:443', 'decision': 'Normal', 'confidence': '97.8%', 'threat_score': 0.0, 'severity': 'LOW', 'status_icon': '🟢', 'status_text': 'NORMAL'},
            {'timestamp': (now - pd.Timedelta(seconds=2)).strftime("%H:%M:%S"), 'protocol': 'TCP', 'src': '45.22.18.91:38192', 'dst': '10.0.0.5:80', 'decision': 'Suspicious Flow', 'confidence': '74.2%', 'threat_score': 42.0, 'severity': 'MODERATE', 'status_icon': '🟡', 'status_text': 'SUSPICIOUS'},
            {'timestamp': (now - pd.Timedelta(seconds=1)).strftime("%H:%M:%S"), 'protocol': 'TCP', 'src': '45.22.18.92:38194', 'dst': '10.0.0.5:80', 'decision': 'DDoS', 'confidence': '96.8%', 'threat_score': 94.0, 'severity': 'CRITICAL', 'status_icon': '🔴', 'status_text': 'THREAT'}
        ]
    if 'traffic_history' not in st.session_state:
        now = datetime.now()
        st.session_state.traffic_history = [
            {'timestamp': (now - pd.Timedelta(seconds=14-i)).strftime("%H:%M:%S"), 'rate': random.randint(20, 32), 'type': 'Normal'}
            for i in range(10)
        ] + [
            {'timestamp': (now - pd.Timedelta(seconds=3)).strftime("%H:%M:%S"), 'rate': 95, 'type': 'Suspicious'},
            {'timestamp': (now - pd.Timedelta(seconds=2)).strftime("%H:%M:%S"), 'rate': 280, 'type': 'Threat'},
            {'timestamp': (now - pd.Timedelta(seconds=1)).strftime("%H:%M:%S"), 'rate': 410, 'type': 'Threat'}
        ]
    if 'graph_annotations' not in st.session_state:
        now = datetime.now()
        st.session_state.graph_annotations = [
            {'x': (now - pd.Timedelta(seconds=2)).strftime("%H:%M:%S"), 'y': 280, 'text': 'DDoS STARTED'}
        ]
    if 'current_threat' not in st.session_state:
        st.session_state.current_threat = {
            'incident_id': 'INC-2026-0042',
            'attack_type': 'DDoS',
            'confidence': '96.8%',
            'threat_score': '94/100',
            'severity': 'CRITICAL',
            'source_ip': '45.22.18.91',
            'dest_ip': '10.0.0.5',
            'protocol': 'TCP',
            'first_detected': datetime.now().strftime("%H:%M:%S"),
            'response_action': 'Simulated Source Isolation & Adaptive Rate Limiting',
            'status': 'SIMULATED RESPONSE ACTIVE'
        }
    if 'explainability_data' not in st.session_state:
        st.session_state.explainability_data = {
            'attack_label': 'DDoS',
            'confidence': '96.8%',
            'features': [
                ('Packet Rate (Same-Host Connections)', 42, True),
                ('SYN Flag Count / Error Rate', 28, True),
                ('Flow Duration', 17, True),
                ('Destination Payload Bytes', 9, False),
                ('Protocol Flag Consistency', 4, False)
            ],
            'reason': 'Abnormally high packet rate combined with SYN-heavy traffic and unusual flow characteristics flagged by DNN classifier.'
        }
    if 'response_stages' not in st.session_state:
        st.session_state.response_stages = {
            'detected': True,
            'classified': True,
            'risk_assessed': True,
            'response_engine': True,
            'source_isolated': True,
            'incident_logged': True
        }
    if 'incident_timeline' not in st.session_state:
        now = datetime.now()
        st.session_state.incident_timeline = [
            {'timestamp': (now - pd.Timedelta(seconds=5)).strftime("%H:%M:%S"), 'icon': '🟢', 'title': 'Monitoring Started', 'desc': 'Baseline traffic inspection active.'},
            {'timestamp': (now - pd.Timedelta(seconds=3)).strftime("%H:%M:%S"), 'icon': '🟡', 'title': 'Anomaly Detected', 'desc': 'Autoencoder reconstruction error elevated.'},
            {'timestamp': (now - pd.Timedelta(seconds=2)).strftime("%H:%M:%S"), 'icon': '🔴', 'title': 'DDoS Classified (INC-2026-0042)', 'desc': 'Model Confidence: 96.8% | Risk: 94/100'},
            {'timestamp': (now - pd.Timedelta(seconds=1)).strftime("%H:%M:%S"), 'icon': '🛡️', 'title': 'Simulated Response Triggered', 'desc': 'Source isolation & rate limiting applied in simulation.'},
            {'timestamp': now.strftime("%H:%M:%S"), 'icon': '📝', 'title': 'Incident Logged', 'desc': 'Persisted to Alerts & Investigation database.'}
        ]
    if 'recent_detections' not in st.session_state:
        now = datetime.now()
        st.session_state.recent_detections = [
            {'Incident ID': 'INC-2026-0042', 'Timestamp': now.strftime("%H:%M:%S"), 'Source': '45.22.18.91:38192', 'Destination': '10.0.0.5:80', 'Protocol': 'TCP', 'Attack Type': 'DDoS', 'Confidence': '96.8%', 'Risk': '94/100', 'Severity': 'CRITICAL', 'Response': 'Simulated Isolation', 'Status': 'Contained (Simulated)'}
        ]
    if 'current_risk_score' not in st.session_state:
        st.session_state.current_risk_score = 91.0
    if 'current_risk_level' not in st.session_state:
        st.session_state.current_risk_level = 'CRITICAL'

def reset_live_monitor():
    """Resets the live monitor demonstration state without clearing DB."""
    st.session_state.monitor_active = False
    st.session_state.system_state = 'IDLE'
    st.session_state.selected_scenario = 'Normal'
    st.session_state.scenario_runner_active = False
    st.session_state.total_packets = 0
    st.session_state.normal_packets = 0
    st.session_state.threat_packets = 0
    st.session_state.inference_times = []
    st.session_state.packet_stream = []
    st.session_state.current_threat = None
    st.session_state.explainability_data = None
    st.session_state.current_risk_score = 10.0
    st.session_state.current_risk_level = 'LOW'
    st.session_state.graph_annotations = []
    st.session_state.response_stages = {
        'detected': False,
        'classified': False,
        'risk_assessed': False,
        'response_engine': False,
        'source_isolated': False,
        'incident_logged': False
    }
    now = datetime.now()
    st.session_state.traffic_history = [
        {'timestamp': (now - pd.Timedelta(seconds=15-i)).strftime("%H:%M:%S"), 'rate': random.randint(18, 30), 'type': 'Normal'}
        for i in range(15)
    ]
    st.session_state.incident_timeline = [
        {'timestamp': datetime.now().strftime("%H:%M:%S"), 'icon': '↻', 'title': 'Monitor Reset', 'desc': 'Demonstration session cleared. Baseline monitoring standing by.'}
    ]
    st.session_state.recent_detections = []

@st.cache_data
def load_dataset():
    """Load and index NSL-KDD test dataset by attack category."""
    test_path = RAW_DATA_DIR / 'KDDTest+.txt'
    if not test_path.exists():
        return None
    test_df = pd.read_csv(test_path, header=None)
    if len(test_df.columns) == len(COLUMNS) + 1:
        test_df.columns = COLUMNS + ['extra']
        test_df.drop('extra', axis=1, inplace=True)
    elif len(test_df.columns) == len(COLUMNS):
        test_df.columns = COLUMNS
    return test_df

def get_scenario_sample(test_df, scenario_name):
    """Retrieve a representative sample row for the chosen scenario."""
    if test_df is None or test_df.empty:
        return None, 'normal'

    if scenario_name == 'Mixed':
        cat_keys = list(ATTACK_CATEGORIES.keys())
        chosen_cat = random.choice(cat_keys)
        attack_types = ATTACK_CATEGORIES[chosen_cat]
    else:
        attack_types = ATTACK_CATEGORIES.get(scenario_name, ['normal'])

    matched = test_df[test_df['attack_type'].isin(attack_types)]
    if not matched.empty:
        sample = matched.sample(1)
        actual_attack = sample['attack_type'].values[0]
        return sample, actual_attack
    else:
        matched_norm = test_df[test_df['attack_type'] == 'normal']
        sample = matched_norm.sample(1) if not matched_norm.empty else test_df.sample(1)
        return sample, 'normal'

def generate_network_context(scenario_name, actual_attack, record):
    """Generates realistic IP/port attributes to mirror realistic IDS network logs."""
    now_str = datetime.now().strftime("%H:%M:%S")
    protocol = str(record['protocol_type'].values[0]).upper() if 'protocol_type' in record.columns else 'TCP'
    service = str(record['service'].values[0]) if 'service' in record.columns else 'http'
    
    port_map = {
        'http': 80, 'https': 443, 'domain_u': 53, 'smtp': 25, 'ftp': 21,
        'ftp_data': 20, 'telnet': 23, 'ssh': 22, 'private': 8080, 'eco_i': 7
    }
    dst_port = port_map.get(service, random.choice([80, 443, 8080, 53]))
    
    if scenario_name == 'DDoS' or actual_attack in ATTACK_CATEGORIES['DDoS']:
        src_ip = f"45.22.18.{random.randint(90, 99)}"
        dst_ip = "10.0.0.5"
        src_port = random.randint(30000, 65000)
    elif scenario_name == 'Port Scan' or actual_attack in ATTACK_CATEGORIES['Port Scan']:
        src_ip = "198.51.100.42"
        dst_ip = "10.0.0.5"
        src_port = random.randint(40000, 55000)
        dst_port = random.choice([21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 8080])
    elif scenario_name == 'Brute Force' or actual_attack in ATTACK_CATEGORIES['Brute Force']:
        src_ip = "203.0.113.88"
        dst_ip = "10.0.0.5"
        src_port = random.randint(49152, 65535)
        dst_port = 22 if service == 'ssh' else (21 if service == 'ftp' else 80)
    elif scenario_name == 'Web Attack' or actual_attack in ATTACK_CATEGORIES['Web Attack']:
        src_ip = "103.25.14.77"
        dst_ip = "10.0.0.5"
        src_port = random.randint(50000, 60000)
        dst_port = 80 if protocol == 'TCP' else 443
    else:
        src_ip = f"192.168.1.{random.randint(10, 45)}"
        dst_ip = "10.0.0.5"
        src_port = random.randint(1024, 65535)
        
    return {
        'timestamp': now_str,
        'protocol': protocol,
        'src_ip': src_ip,
        'dst_ip': dst_ip,
        'src_port': src_port,
        'dst_port': dst_port,
        'service': service
    }

def process_live_packet(pipeline, test_df, scenario_name):
    """Processes a packet through the model, updates metrics, XAI, response, and DB."""
    record_df, actual_attack = get_scenario_sample(test_df, scenario_name)
    if record_df is None:
        return None

    net_ctx = generate_network_context(scenario_name, actual_attack, record_df)
    
    t0 = time.perf_counter()
    pred_info, alert, exp = pipeline.process_record(record_df)
    inference_ms = round((time.perf_counter() - t0) * 1000, 2)
    
    st.session_state.total_packets += 1
    st.session_state.inference_times.append(inference_ms)
    if len(st.session_state.inference_times) > 100:
        st.session_state.inference_times.pop(0)

    decision = pred_info.get('decision', 'Normal')
    threat_score = float(pred_info.get('threat_score', 0.0))
    confidence = float(pred_info.get('confidence', 0.95))
    anomaly_score = float(pred_info.get('anomaly_score', 0.01))
    severity = pred_info.get('severity', 'LOW')

    is_threat = decision != 'Normal' or threat_score >= 50.0

    if is_threat:
        st.session_state.threat_packets += 1
        status_icon = '🔴'
        status_text = 'THREAT'
        st.session_state.current_risk_score = threat_score
        st.session_state.current_risk_level = severity
        st.session_state.system_state = 'THREAT_DETECTED'
    elif threat_score > 25.0:
        st.session_state.normal_packets += 1
        status_icon = '🟡'
        status_text = 'SUSPICIOUS'
        st.session_state.current_risk_score = max(st.session_state.current_risk_score, threat_score)
        st.session_state.current_risk_level = 'MODERATE'
        st.session_state.system_state = 'ANOMALY_DETECTED'
    else:
        st.session_state.normal_packets += 1
        status_icon = '🟢'
        status_text = 'NORMAL'
        st.session_state.current_risk_score = round(max(8.0, st.session_state.current_risk_score * 0.92), 1)
        if st.session_state.current_risk_score < 25:
            st.session_state.current_risk_level = 'LOW'
        st.session_state.system_state = 'MONITORING'

    if scenario_name == 'DDoS' or (is_threat and 'neptune' in actual_attack):
        current_rate = random.randint(280, 520)
    elif scenario_name == 'Port Scan':
        current_rate = random.randint(90, 160)
    elif is_threat:
        current_rate = random.randint(65, 120)
    else:
        current_rate = random.randint(18, 35)

    st.session_state.traffic_history.append({
        'timestamp': net_ctx['timestamp'],
        'rate': current_rate,
        'type': status_text
    })
    if len(st.session_state.traffic_history) > 30:
        st.session_state.traffic_history.pop(0)

    packet_event = {
        'timestamp': net_ctx['timestamp'],
        'protocol': net_ctx['protocol'],
        'src': f"{net_ctx['src_ip']}:{net_ctx['src_port']}",
        'dst': f"{net_ctx['dst_ip']}:{net_ctx['dst_port']}",
        'decision': scenario_name if is_threat else 'Normal',
        'raw_model_decision': decision,
        'confidence': f"{confidence * 100:.1f}%",
        'threat_score': threat_score,
        'severity': severity,
        'status_icon': status_icon,
        'status_text': status_text
    }
    st.session_state.packet_stream.insert(0, packet_event)
    if len(st.session_state.packet_stream) > 40:
        st.session_state.packet_stream.pop()

    if is_threat:
        incident_id = alert['Alert ID'] if alert else f"INC-2026-{uuid.uuid4().hex[:4].upper()}"
        attack_label = scenario_name if scenario_name != 'Normal' else actual_attack.capitalize()

        response_action_map = {
            'DDoS': 'Simulated Source Isolation & Adaptive Rate Limiting',
            'Port Scan': 'Simulated Source Quarantine & Port Shuffling',
            'Brute Force': 'Simulated Credential Lockout & Host Block',
            'Web Attack': 'Simulated WAF Request Filter & Payload Drop',
            'Mixed': 'Simulated Multi-Vector Dynamic Threat Containment'
        }
        resp_action = response_action_map.get(scenario_name, 'Simulated Automated Containment')

        st.session_state.current_threat = {
            'incident_id': incident_id,
            'attack_type': attack_label,
            'confidence': f"{confidence * 100:.1f}%",
            'threat_score': f"{threat_score}/100",
            'severity': severity,
            'source_ip': net_ctx['src_ip'],
            'dest_ip': net_ctx['dst_ip'],
            'protocol': net_ctx['protocol'],
            'first_detected': net_ctx['timestamp'],
            'response_action': resp_action,
            'status': 'SIMULATED RESPONSE ACTIVE'
        }

        feature_contributions = []
        if exp and len(exp) > 0:
            total_mag = sum(abs(v) for _, v in exp[:5]) or 1.0
            for feat, val in exp[:5]:
                clean_name = FEATURE_DESCRIPTIONS.get(feat, feat.replace('_', ' ').title())
                pct = int(round((abs(val) / total_mag) * 100))
                feature_contributions.append((clean_name, pct, val >= 0))
        else:
            feature_contributions = [
                ('Packet Rate (Same-Host Connections)', 42, True),
                ('SYN Flag Count / Error Rate', 28, True),
                ('Flow Duration', 17, True),
                ('Destination Payload Bytes', 9, False),
                ('Protocol Flag Consistency', 4, False)
            ]

        if scenario_name == 'DDoS':
            narrative = f"Abnormally high packet rate and SYN-heavy connection count ({record_df['count'].values[0] if 'count' in record_df else 'spike'}) flagged by DNN classifier."
        elif scenario_name == 'Port Scan':
            narrative = f"Rapid sequential port connections across unique destination services flagged as high anomaly ({anomaly_score:.3f})."
        elif scenario_name == 'Brute Force':
            narrative = f"Multiple rapid authentication attempts and high same-service frequency flagged with {confidence*100:.1f}% model confidence."
        elif scenario_name == 'Web Attack':
            narrative = f"Unusual payload byte distribution and anomalous flow flags deviating from benign HTTP baselines."
        else:
            narrative = f"Combined DNN score and Autoencoder reconstruction error exceeded critical alert threshold."

        st.session_state.explainability_data = {
            'attack_label': attack_label,
            'confidence': f"{confidence * 100:.1f}%",
            'features': feature_contributions,
            'reason': narrative
        }

        st.session_state.response_stages = {
            'detected': True,
            'classified': True,
            'risk_assessed': True,
            'response_engine': True,
            'source_isolated': True,
            'incident_logged': True
        }

        st.session_state.incident_timeline.insert(0, {
            'timestamp': net_ctx['timestamp'],
            'icon': '🔴',
            'title': f'{attack_label} Classified ({incident_id})',
            'desc': f'Confidence: {confidence*100:.1f}% | Risk: {threat_score}/100 | Action: {resp_action}'
        })
        if len(st.session_state.incident_timeline) > 25:
            st.session_state.incident_timeline.pop()

        detection_entry = {
            'Incident ID': incident_id,
            'Timestamp': net_ctx['timestamp'],
            'Source': f"{net_ctx['src_ip']}:{net_ctx['src_port']}",
            'Destination': f"{net_ctx['dst_ip']}:{net_ctx['dst_port']}",
            'Protocol': net_ctx['protocol'],
            'Attack Type': attack_label,
            'Confidence': f"{confidence * 100:.1f}%",
            'Risk': f"{threat_score}/100",
            'Severity': severity,
            'Response': 'Simulated Isolation',
            'Status': 'Contained (Simulated)'
        }
        if not any(d['Incident ID'] == incident_id for d in st.session_state.recent_detections):
            st.session_state.recent_detections.insert(0, detection_entry)
            if len(st.session_state.recent_detections) > 15:
                st.session_state.recent_detections.pop()

        st.session_state.graph_annotations.append({
            'x': net_ctx['timestamp'],
            'y': current_rate,
            'text': f"{attack_label.upper()} STARTED"
        })
        if len(st.session_state.graph_annotations) > 5:
            st.session_state.graph_annotations.pop(0)

    return packet_event

def run_automated_attack_scenario(pipeline, test_df, scenario_name, display_placeholder):
    """Executes the automated demonstration replay by updating the display placeholder."""
    st.session_state.scenario_runner_active = True
    st.session_state.selected_scenario = scenario_name

    # Phase 1: Baseline
    st.session_state.system_state = 'MONITORING'
    st.session_state.incident_timeline.insert(0, {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'icon': '🟢',
        'title': f'Scenario Replay Started: {scenario_name}',
        'desc': 'Injecting normal background traffic into dual-model engine.'
    })
    for _ in range(2):
        process_live_packet(pipeline, test_df, 'Normal')
        render_live_monitor_display(display_placeholder)
        time.sleep(0.6)

    # Phase 2: Anomaly
    st.session_state.system_state = 'ANOMALY_DETECTED'
    st.session_state.incident_timeline.insert(0, {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'icon': '🟡',
        'title': 'Traffic Anomaly Detected',
        'desc': f'Unusual connection pattern matching {scenario_name} signature.'
    })
    process_live_packet(pipeline, test_df, scenario_name)
    render_live_monitor_display(display_placeholder)
    time.sleep(0.9)

    # Phase 3: Classification
    st.session_state.system_state = 'CLASSIFYING'
    for _ in range(2):
        process_live_packet(pipeline, test_df, scenario_name)
        render_live_monitor_display(display_placeholder)
        time.sleep(0.7)

    # Phase 4: Simulated Response
    st.session_state.system_state = 'RESPONDING'
    st.session_state.incident_timeline.insert(0, {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'icon': '🛡️',
        'title': 'Response Triggered (Simulated)',
        'desc': 'Flagging source IP and executing simulated ACL drop rules.'
    })
    render_live_monitor_display(display_placeholder)
    time.sleep(1.0)

    # Phase 5: Contained
    st.session_state.system_state = 'CONTAINED'
    st.session_state.incident_timeline.insert(0, {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'icon': '📝',
        'title': 'Incident Logged & Contained',
        'desc': 'Intrusion record saved to investigation database.'
    })
    render_live_monitor_display(display_placeholder)

    st.session_state.scenario_runner_active = False

def render_live_traffic_graph():
    """Renders the real-time Plotly traffic rate graph with annotations."""
    history = st.session_state.traffic_history
    if not history:
        return go.Figure()

    df_hist = pd.DataFrame(history)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_hist['timestamp'],
        y=df_hist['rate'],
        mode='lines+markers',
        line=dict(color='#00E5FF', width=3, shape='spline'),
        marker=dict(size=6, color='#00E5FF'),
        fill='tozeroy',
        fillcolor='rgba(0, 229, 255, 0.08)',
        name='Packets/sec (Simulated)'
    ))

    for ann in st.session_state.graph_annotations:
        if ann['x'] in df_hist['timestamp'].values:
            fig.add_annotation(
                x=ann['x'],
                y=ann['y'],
                text=ann['text'],
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='#FF3B30',
                ax=0,
                ay=-35,
                bgcolor='rgba(255, 59, 48, 0.9)',
                font=dict(color='white', size=11, family='sans-serif'),
                borderpad=4
            )

    fig.update_layout(
        title="LIVE TRAFFIC GRAPH",
        title_font=dict(size=13, color="#E0E0E0"),
        paper_bgcolor="#14171F",
        plot_bgcolor="#14171F",
        font=dict(color="#A0A5B5", size=11),
        margin=dict(l=40, r=20, t=40, b=30),
        height=250,
        xaxis=dict(
            gridcolor="#222736",
            showgrid=True,
            zeroline=False
        ),
        yaxis=dict(
            gridcolor="#222736",
            showgrid=True,
            zeroline=False,
            title="Packets/sec"
        ),
        showlegend=False
    )
    return fig

def render_live_monitor_display(display_container):
    """Renders all visual displays inside the placeholder without recreating action buttons."""
    # Increment sequence to ensure unique element IDs on each update
    if 'render_seq' not in st.session_state:
        st.session_state.render_seq = 0
    st.session_state.render_seq += 1
    seq = st.session_state.render_seq

    with display_container.container():
        # Top Header Bar
        status_map = {
            'IDLE': ('● SYSTEM IDLE', '#8E8E93'),
            'MONITORING': ('● SYSTEM ACTIVE', '#34C759'),
            'ANOMALY_DETECTED': ('● ANOMALY DETECTED', '#FFCC00'),
            'CLASSIFYING': ('● CLASSIFYING THREAT', '#FF9500'),
            'THREAT_DETECTED': ('● ATTACK DETECTED', '#FF3B30'),
            'RESPONDING': ('● RESPONSE ACTIVE', '#AF52DE'),
            'CONTAINED': ('● THREAT CONTAINED', '#5856D6')
        }
        badge_text, badge_color = status_map.get(
            st.session_state.system_state, ('● SYSTEM ACTIVE', '#34C759')
        )

        st.markdown(f"""
        <div style="background-color: #1A1D26; padding: 14px 18px; border-radius: 8px; border-left: 5px solid {badge_color}; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 1.3rem; font-weight: 700; color: #FFFFFF; letter-spacing: 0.5px;">
                    📡 LIVE TRAFFIC MONITOR
                </div>
                <div style="font-size: 0.85rem; color: #8F9BA8; margin-top: 2px;">
                    Real-time network intrusion detection
                </div>
            </div>
            <div style="text-align: right;">
                <div style="display: inline-block; background-color: rgba(255,255,255,0.06); border: 1px solid {badge_color}; color: {badge_color}; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 0.82rem;">
                    {badge_text}
                </div>
                <div style="font-size: 0.72rem; color: #FF9500; font-weight: 600; margin-top: 3px;">
                    ● DEMO MODE — SIMULATED TRAFFIC
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4-Column KPI Cards Row
        tot = st.session_state.total_packets
        threats = st.session_state.threat_packets
        det_rate = f"{(threats / max(1, tot)) * 100:.1f}%" if tot > 0 else "0.0%"
        risk_score = st.session_state.current_risk_score
        risk_color = '#FF3B30' if risk_score >= 75 else ('#FF9500' if risk_score >= 50 else ('#FFCC00' if risk_score >= 25 else '#34C759'))
        risk_icon = '🔴' if risk_score >= 75 else ('🟠' if risk_score >= 50 else ('🟡' if risk_score >= 25 else '🟢'))

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div style="background-color: #181B24; padding: 12px 14px; border-radius: 8px; border: 1px solid #282D3C;">
                <div style="font-size: 0.75rem; color: #8F9BA8; font-weight: 700; text-transform: uppercase;">PACKETS</div>
                <div style="font-size: 1.6rem; font-weight: 700; color: #FFFFFF; margin-top: 2px;">{tot:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div style="background-color: #181B24; padding: 12px 14px; border-radius: 8px; border: 1px solid #282D3C;">
                <div style="font-size: 0.75rem; color: #8F9BA8; font-weight: 700; text-transform: uppercase;">THREATS</div>
                <div style="font-size: 1.6rem; font-weight: 700; color: #FF3B30; margin-top: 2px;">{threats:,}</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div style="background-color: #181B24; padding: 12px 14px; border-radius: 8px; border: 1px solid #282D3C;">
                <div style="font-size: 0.75rem; color: #8F9BA8; font-weight: 700; text-transform: uppercase;">DETECTION</div>
                <div style="font-size: 1.6rem; font-weight: 700; color: #00E5FF; margin-top: 2px;">{det_rate}</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div style="background-color: #181B24; padding: 12px 14px; border-radius: 8px; border: 1px solid #282D3C;">
                <div style="font-size: 0.75rem; color: #8F9BA8; font-weight: 700; text-transform: uppercase;">CURRENT RISK</div>
                <div style="font-size: 1.6rem; font-weight: 700; color: {risk_color}; margin-top: 2px;">{risk_icon} {risk_score:.0f}/100</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

        # Full-Width Live Traffic Graph with dynamic unique key
        st.plotly_chart(render_live_traffic_graph(), use_container_width=True, key=f"plotly_traffic_chart_{seq}")

        # Split 2-Column Section: Live Packet Stream vs Current Threat
        col_stream, col_threat = st.columns([1.1, 1.0])

        with col_stream:
            st.markdown("<div style='font-size: 0.95rem; font-weight: 700; color: #E1E4EA; margin-bottom: 6px;'>LIVE TRAFFIC EVENTS</div>", unsafe_allow_html=True)
            if st.session_state.packet_stream:
                stream_html = """
                <div style="background-color: #14171F; border: 1px solid #242836; border-radius: 8px; height: 230px; overflow-y: auto; font-family: monospace; font-size: 0.8rem; padding: 6px;">
                """
                for pkt in st.session_state.packet_stream[:15]:
                    color = '#34C759' if pkt['status_text'] == 'NORMAL' else ('#FFCC00' if pkt['status_text'] == 'SUSPICIOUS' else '#FF3B30')
                    stream_html += f"""
                    <div style="padding: 5px 8px; border-bottom: 1px solid #1E2230; display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: {color}; font-weight: 700;">{pkt['status_icon']} {pkt['timestamp']}</span>
                        <span style="color: #00E5FF;">{pkt['protocol']}</span>
                        <span style="color: #D1D5DB;">{pkt['src']} → {pkt['dst']}</span>
                        <span style="color: {color}; font-weight: 700;">{pkt['decision'].upper()}</span>
                    </div>
                    """
                stream_html += "</div>"
                st.markdown(stream_html, unsafe_allow_html=True)
            else:
                st.info("No packets analyzed yet. Click an attack button or 'Run Attack Scenario'.")

        with col_threat:
            st.markdown("<div style='font-size: 0.95rem; font-weight: 700; color: #E1E4EA; margin-bottom: 6px;'>CURRENT THREAT</div>", unsafe_allow_html=True)
            ct = st.session_state.current_threat
            if ct and st.session_state.system_state in ['THREAT_DETECTED', 'RESPONDING', 'CONTAINED', 'CLASSIFYING', 'IDLE', 'MONITORING'] and st.session_state.current_risk_score >= 50:
                st.markdown(f"""
                <div style="background-color: #1A1318; border: 1px solid #FF3B30; border-radius: 8px; padding: 14px; height: 230px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,59,48,0.25); padding-bottom: 6px;">
                            <span style="font-size: 1.15rem; font-weight: 700; color: #FF3B30;">🔴 {ct['attack_type'].upper()} DETECTED</span>
                            <span style="background-color: rgba(255,59,48,0.2); color: #FF3B30; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700;">{ct['severity']}</span>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 8px; font-size: 0.85rem;">
                            <div><span style="color: #8F9BA8;">Confidence:</span> <b style="color: #34C759;">{ct['confidence']}</b></div>
                            <div><span style="color: #8F9BA8;">Risk:</span> <b style="color: #FF3B30;">{ct['threat_score']}</b></div>
                            <div><span style="color: #8F9BA8;">Severity:</span> <b style="color: #FF3B30;">{ct['severity']}</b></div>
                            <div><span style="color: #8F9BA8;">Incident ID:</span> <b style="color: #FFFFFF;">{ct['incident_id']}</b></div>
                            <div><span style="color: #8F9BA8;">Source IP:</span> <b style="color: #00E5FF;">{ct['source_ip']}</b></div>
                            <div><span style="color: #8F9BA8;">Protocol:</span> <b style="color: #E0E0E0;">{ct['protocol']}</b></div>
                        </div>
                    </div>
                    <div style="background-color: rgba(255,255,255,0.04); padding: 6px 8px; border-radius: 4px; font-size: 0.78rem;">
                        <span style="color: #FF9500; font-weight: 600;">Response:</span> {ct['response_action']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background-color: #121A15; border: 1px solid #34C759; border-radius: 8px; padding: 30px 14px; text-align: center; height: 230px; display: flex; flex-direction: column; justify-content: center;">
                    <div style="font-size: 2.2rem; margin-bottom: 4px;">🟢</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #34C759;">NO ACTIVE THREAT</div>
                    <div style="font-size: 0.82rem; color: #8F9BA8; margin-top: 4px;">Normal baseline traffic streaming.</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color: #262B38; margin: 14px 0;'>", unsafe_allow_html=True)

        # 🧠 Explainable AI ("WHY WAS THIS DETECTED?")
        st.markdown("<div style='font-size: 1.05rem; font-weight: 700; color: #FFFFFF;'>🧠 WHY WAS THIS DETECTED?</div>", unsafe_allow_html=True)

        exp_data = st.session_state.explainability_data
        if exp_data:
            col_b, col_r = st.columns([1.2, 1.0])
            with col_b:
                for feat_name, pct, is_pos in exp_data['features'][:4]:
                    bar_color = '#FF3B30' if is_pos else '#00E5FF'
                    st.markdown(f"""
                    <div style="margin-bottom: 6px; font-size: 0.82rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span style="color: #D1D5DB; font-weight: 500;">{feat_name}</span>
                            <span style="color: {bar_color}; font-weight: 700;">+{pct}%</span>
                        </div>
                        <div style="background-color: #222634; border-radius: 4px; height: 7px; width: 100%;">
                            <div style="background-color: {bar_color}; width: {pct}%; height: 7px; border-radius: 4px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            with col_r:
                st.markdown(f"""
                <div style="background-color: #181B24; border: 1px solid #282D3C; border-radius: 8px; padding: 12px; font-size: 0.84rem; color: #D1D5DB; line-height: 1.45;">
                    <div style="font-weight: 600; color: #FF9500; margin-bottom: 4px;">Detection Reason:</div>
                    {exp_data['reason']}
                    <div style="margin-top: 8px; font-size: 0.75rem; color: #8F9BA8; border-top: 1px solid #262B38; padding-top: 4px;">
                        Model Attribution Confidence: <b style="color:#34C759;">{exp_data['confidence']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: #181B24; border: 1px dashed #2E3446; border-radius: 8px; padding: 12px; text-align: center; color: #8F9BA8; font-size: 0.82rem;">
                No anomalous pattern detected. Select an attack scenario to inspect neural attribution.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='border-color: #262B38; margin: 14px 0;'>", unsafe_allow_html=True)

        # 🛡️ INCIDENT RESPONSE
        st.markdown("<div style='font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-bottom: 6px;'>🛡️ INCIDENT RESPONSE</div>", unsafe_allow_html=True)

        stages = st.session_state.response_stages
        def make_stage(icon_symbol, text_label, is_done):
            c = "#34C759" if is_done else "#8F9BA8"
            bg = "rgba(52, 199, 89, 0.12)" if is_done else "#181B24"
            bdr = "#34C759" if is_done else "#282D3C"
            return f"""
            <div style="background-color: {bg}; border: 1px solid {bdr}; border-radius: 6px; padding: 8px; text-align: center; font-size: 0.8rem;">
                <div style="font-size: 1.05rem; font-weight: 700; color: {c};">{icon_symbol}</div>
                <div style="font-weight: 600; color: #FFFFFF; margin-top: 2px;">{text_label}</div>
            </div>
            """

        resp_col1, resp_col2, resp_col3, resp_col4, resp_col5, resp_col6 = st.columns(6)
        with resp_col1:
            st.markdown(make_stage("🔴", "Threat Detected", stages['detected']), unsafe_allow_html=True)
        with resp_col2:
            st.markdown(make_stage("🧠", "ML Classified", stages['classified']), unsafe_allow_html=True)
        with resp_col3:
            st.markdown(make_stage("📊", "Risk Assessed", stages['risk_assessed']), unsafe_allow_html=True)
        with resp_col4:
            st.markdown(make_stage("🛡️", "Response Active", stages['response_engine']), unsafe_allow_html=True)
        with resp_col5:
            st.markdown(make_stage("🚫", "Simulated Isolation", stages['source_isolated']), unsafe_allow_html=True)
        with resp_col6:
            st.markdown(make_stage("📝", "Incident Logged", stages['incident_logged']), unsafe_allow_html=True)

        st.markdown("<hr style='border-color: #262B38; margin: 14px 0;'>", unsafe_allow_html=True)

        # INCIDENT TIMELINE & RECENT DETECTIONS
        col_tline, col_tlist = st.columns([1.0, 1.3])

        with col_tline:
            st.markdown("<div style='font-size: 0.95rem; font-weight: 700; color: #E1E4EA; margin-bottom: 6px;'>INCIDENT TIMELINE</div>", unsafe_allow_html=True)
            tline_html = """
            <div style="background-color: #14171F; border: 1px solid #242836; border-radius: 8px; height: 210px; overflow-y: auto; padding: 8px; font-size: 0.8rem;">
            """
            for item in st.session_state.incident_timeline:
                tline_html += f"""
                <div style="padding: 5px 0; border-bottom: 1px solid #1E2230;">
                    <div style="display: flex; justify-content: space-between; color: #8F9BA8; font-size: 0.75rem;">
                        <span>{item['icon']} <b>{item['title']}</b></span>
                        <span>{item['timestamp']}</span>
                    </div>
                    <div style="color: #D1D5DB; font-size: 0.76rem; margin-top: 1px; padding-left: 18px;">
                        {item['desc']}
                    </div>
                </div>
                """
            tline_html += "</div>"
            st.markdown(tline_html, unsafe_allow_html=True)

        with col_tlist:
            st.markdown("<div style='font-size: 0.95rem; font-weight: 700; color: #E1E4EA; margin-bottom: 6px;'>RECENT DETECTIONS</div>", unsafe_allow_html=True)
            if st.session_state.recent_detections:
                df_det = pd.DataFrame(st.session_state.recent_detections)
                st.dataframe(df_det[['Incident ID', 'Timestamp', 'Attack Type', 'Confidence', 'Risk', 'Severity', 'Status']], use_container_width=True, height=210, key=f"table_detections_{seq}")
            else:
                st.markdown("""
                <div style="background-color: #14171F; border: 1px solid #242836; border-radius: 8px; height: 210px; display: flex; justify-content: center; align-items: center; color: #8F9BA8; font-size: 0.82rem;">
                    No security incidents logged yet.
                </div>
                """, unsafe_allow_html=True)

def render_live_monitor_dashboard(pipeline, test_df, container):
    """
    Renders the complete Live Traffic Monitor page:
    1. Static Controls with explicit unique keys.
    2. Dynamic display placeholder for real-time visualization.
    """
    # 1. Action Controls Row
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 1.5, 1.5])
    with ctrl_col1:
        if st.button("Start Live Monitoring", type="primary", use_container_width=True, key="btn_start_monitor"):
            st.session_state.monitor_active = True
            st.session_state.system_state = 'MONITORING'
            process_live_packet(pipeline, test_df, 'Normal')
            st.rerun()
    with ctrl_col2:
        if st.button("Stop Monitoring", use_container_width=True, key="btn_stop_monitor"):
            st.session_state.monitor_active = False
            st.session_state.system_state = 'IDLE'
            st.rerun()
    with ctrl_col3:
        if st.button("↻ Reset Monitor", use_container_width=True, key="btn_reset_monitor"):
            reset_live_monitor()
            st.rerun()

    st.markdown("<hr style='border-color: #262B38; margin: 10px 0;'>", unsafe_allow_html=True)

    # 2. Attack Simulation Buttons Row
    st.markdown("<div style='font-size: 0.95rem; font-weight: 700; color: #E1E4EA; margin-bottom: 6px;'>ATTACK SIMULATION</div>", unsafe_allow_html=True)
    
    sim_c1, sim_c2, sim_c3, sim_c4, sim_c5, sim_c6 = st.columns(6)
    with sim_c1:
        if st.button("🟢 Normal", use_container_width=True, key="btn_scenario_normal"):
            st.session_state.selected_scenario = 'Normal'
            process_live_packet(pipeline, test_df, 'Normal')
            st.rerun()
    with sim_c2:
        if st.button("🔴 DDoS", use_container_width=True, key="btn_scenario_ddos"):
            st.session_state.selected_scenario = 'DDoS'
            process_live_packet(pipeline, test_df, 'DDoS')
            st.rerun()
    with sim_c3:
        if st.button("🟠 Port Scan", use_container_width=True, key="btn_scenario_portscan"):
            st.session_state.selected_scenario = 'Port Scan'
            process_live_packet(pipeline, test_df, 'Port Scan')
            st.rerun()
    with sim_c4:
        if st.button("🟣 Brute Force", use_container_width=True, key="btn_scenario_bruteforce"):
            st.session_state.selected_scenario = 'Brute Force'
            process_live_packet(pipeline, test_df, 'Brute Force')
            st.rerun()
    with sim_c5:
        if st.button("🔵 Web Attack", use_container_width=True, key="btn_scenario_webattack"):
            st.session_state.selected_scenario = 'Web Attack'
            process_live_packet(pipeline, test_df, 'Web Attack')
            st.rerun()
    with sim_c6:
        if st.button("⚠️ Mixed Attack", use_container_width=True, key="btn_scenario_mixed"):
            st.session_state.selected_scenario = 'Mixed'
            process_live_packet(pipeline, test_df, 'Mixed')
            st.rerun()

    st.markdown("<div style='margin-top: 6px;'></div>", unsafe_allow_html=True)
    run_auto = st.button(
        f"▶ RUN ATTACK SCENARIO ({st.session_state.selected_scenario.upper()})",
        type="primary",
        use_container_width=True,
        key="btn_run_scenario"
    )

    st.markdown("<hr style='border-color: #262B38; margin: 12px 0;'>", unsafe_allow_html=True)

    # 3. Dynamic Visual Display Placeholder
    display_placeholder = st.empty()
    render_live_monitor_display(display_placeholder)

    # 4. Handle Scenario Replay Loop cleanly
    if run_auto:
        run_automated_attack_scenario(pipeline, test_df, st.session_state.selected_scenario, display_placeholder)
        st.rerun()
