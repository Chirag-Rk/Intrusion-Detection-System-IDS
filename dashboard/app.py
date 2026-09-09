import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
from pathlib import Path
import time
import json
import sqlite3

# Adjust paths
sys.path.append(str(Path(__file__).resolve().parent.parent))
from configs.config import DATA_DIR, RAW_DATA_DIR, COLUMNS
from src.data.database import DB_PATH, get_stats, get_recent_alerts
from src.inference.inference import InferencePipeline

# Page Config
st.set_page_config(
    page_title="AegisIDS - Security Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme and metrics
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .severity-CRITICAL { color: #FF3B30; font-weight: bold; }
    .severity-HIGH { color: #FF9500; font-weight: bold; }
    .severity-MODERATE { color: #FFCC00; font-weight: bold; }
    .severity-LOW { color: #34C759; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'pipeline' not in st.session_state:
    with st.spinner("Initializing ML Inference Pipeline..."):
        st.session_state.pipeline = InferencePipeline()
        
if 'running' not in st.session_state:
    st.session_state.running = False
    
# Sidebar
st.sidebar.title("🛡️ AegisIDS")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", ["Overview", "Live Traffic Monitor", "Alerts & Investigation", "System Evaluation", "Interactive Threat Simulator"])

def overview_page():
    st.title("Network Security Overview")
    
    # Load Stats from DB
    stats = get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'><h3>Total Analyzed</h3><div class='metric-value'>{stats['total_analyzed']}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><h3>Normal Traffic</h3><div class='metric-value' style='color:#34C759;'>{stats['normal_traffic']}</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><h3>Malicious Detections</h3><div class='metric-value' style='color:#FF3B30;'>{stats['malicious_detected']}</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'><h3>Critical Alerts</h3><div class='metric-value' style='color:#FF3B30;'>{stats['critical_alerts']}</div></div>", unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Recent Alerts summary
    st.subheader("Recent Security Events")
    alerts_df = get_recent_alerts(10)
    if not alerts_df.empty:
        # Style dataframe
        def color_severity(val):
            colors = {'CRITICAL': 'red', 'HIGH': 'orange', 'MODERATE': 'yellow', 'LOW': 'green'}
            return f'color: {colors.get(val, "white")}'
        
        st.dataframe(alerts_df[['timestamp', 'alert_id', 'attack_type', 'threat_score', 'severity']].style.map(color_severity, subset=['severity']), use_container_width=True)
    else:
        st.info("No security alerts recorded.")

from dashboard.live_monitor import (
    init_live_monitor_state,
    load_dataset,
    render_live_monitor_dashboard
)

def live_monitor_page():
    init_live_monitor_state()
    test_df = load_dataset()
    if test_df is None:
        st.error("Test dataset (KDDTest+.txt) not found in data/raw.")
        return
        
    placeholder = st.empty()
    render_live_monitor_dashboard(st.session_state.pipeline, test_df, placeholder)


def alerts_investigation_page():
    st.title("🚨 Alerts & Investigation")
    
    alerts_df = get_recent_alerts(50)
    if alerts_df.empty:
        st.info("No security alerts recorded yet. Use Live Traffic Monitor to generate alerts.")
        return
        
    # Filter controls
    col1, col2 = st.columns([1, 3])
    with col1:
        severity_filter = st.selectbox("Filter by Severity", ['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'])
    
    if severity_filter != 'ALL':
        alerts_df = alerts_df[alerts_df['severity'] == severity_filter]
    
    st.subheader(f"Showing {len(alerts_df)} alert(s)")
    
    for _, row in alerts_df.iterrows():
        sev = row['severity']
        color_map = {'CRITICAL': '#FF3B30', 'HIGH': '#FF9500', 'MODERATE': '#FFCC00', 'LOW': '#34C759'}
        color = color_map.get(sev, '#FFFFFF')
        
        with st.expander(f"🔴 [{sev}] {row['alert_id']} — {row['attack_type']} | Score: {row['threat_score']}"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Severity", sev)
            col2.metric("Confidence", row['confidence'])
            col3.metric("Anomaly Score", row['anomaly_score'])
            
            st.markdown("**🔍 XAI Feature Attribution:**")
            st.code(row.get('reason', 'N/A'), language=None)
            
            st.markdown("**🛡️ Recommendation:**")
            st.info(row.get('recommendation', 'N/A'))
            st.caption(f"Timestamp: {row['timestamp']}")

def evaluation_page():
    st.title("📊 System Evaluation")
    
    # Load full model comparison metrics
    try:
        metrics_df = pd.read_csv(Path(__file__).resolve().parent.parent / 'results' / 'model_comparison.csv')
        st.subheader("Full Model Comparison")
        st.dataframe(metrics_df, use_container_width=True)
        
        # Plotly chart - Accuracy & F1-Score
        fig = px.bar(metrics_df, x='Model', y=['Accuracy', 'F1-Score'], barmode='group', 
                     title="Accuracy & F1-Score Comparison",
                     color_discrete_map={'Accuracy': '#00E599', 'F1-Score': '#00A3FF'})
        fig.update_layout(plot_bgcolor='#1E1E1E', paper_bgcolor='#1E1E1E', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
        
        # FPR comparison
        fig2 = px.bar(metrics_df, x='Model', y='False Positive Rate (FPR)',
                      title="False Positive Rate Comparison", color='False Positive Rate (FPR)',
                      color_continuous_scale='RdYlGn_r')
        fig2.update_layout(plot_bgcolor='#1E1E1E', paper_bgcolor='#1E1E1E', font_color='white')
        st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.warning(f"Full metrics not available: {e}")

    # Show visualization figures
    figures_dir = Path(__file__).resolve().parent.parent / 'results' / 'figures'
    
    col1, col2 = st.columns(2)
    with col1:
        cm_path = figures_dir / 'confusion_matrix.png'
        if cm_path.exists():
            st.subheader("Confusion Matrix")
            st.image(str(cm_path))
    with col2:
        roc_path = figures_dir / 'roc_curve.png'
        if roc_path.exists():
            st.subheader("ROC Curves")
            st.image(str(roc_path))
    
    pr_path = figures_dir / 'precision_recall.png'
    if pr_path.exists():
        st.subheader("Precision-Recall Curves")
        st.image(str(pr_path))
    
    ae_path = figures_dir / 'anomaly_distribution.png'
    if ae_path.exists():
        st.subheader("Autoencoder Anomaly Error Distribution")
        st.image(str(ae_path))

    dnn_hist = figures_dir / 'dnn_training_history.png'
    if dnn_hist.exists():
        st.subheader("DNN Training History")
        st.image(str(dnn_hist))

def threat_simulator_page():
    st.title("🎛️ Interactive Threat Simulator")
    st.markdown("Modify network packet attributes to observe how the AegisIDS AI model evaluates the threat in real-time. This allows for adversarial testing and what-if scenarios.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Packet Parameters")
        st.markdown("Adjust these critical network features:")
        
        # We start with a baseline normal packet
        duration = st.slider("Connection Duration (seconds)", 0, 50000, 0)
        src_bytes = st.slider("Source Bytes", 0, 1000000, 256)
        dst_bytes = st.slider("Destination Bytes", 0, 1000000, 512)
        count = st.slider("Connections to same host (count)", 0, 511, 2)
        srv_count = st.slider("Connections to same service (srv_count)", 0, 511, 2)
        protocol_type = st.selectbox("Protocol Type", ["tcp", "udp", "icmp"])
        flag = st.selectbox("TCP Flag", ["SF", "S0", "REJ", "RSTR", "SH", "RSTO", "S1", "S2", "S3", "OTH"])
        logged_in = st.selectbox("Logged In", [0, 1], index=1)
        
        # Build the mock record matching expected COLUMNS
        # Most other features will be set to 0 for simplicity
        record = {col: 0 for col in COLUMNS}
        record.update({
            'duration': duration,
            'src_bytes': src_bytes,
            'dst_bytes': dst_bytes,
            'count': count,
            'srv_count': srv_count,
            'protocol_type': protocol_type,
            'flag': flag,
            'logged_in': logged_in,
            'attack_type': 'normal', # Baseline
            'difficulty_level': 21
        })
        
        record_df = pd.DataFrame([record])
        
    with col2:
        st.subheader("Real-Time AI Analysis")
        # Process the manually crafted record
        pred_info, alert, exp = st.session_state.pipeline.process_record(record_df)
        
        # Gauge Chart for Threat Score
        threat_score = pred_info['threat_score']
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = threat_score,
            title = {'text': "AI Threat Score"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "white"},
                'bgcolor': "#1E1E1E",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 25], 'color': '#34C759'},
                    {'range': [25, 50], 'color': '#FFCC00'},
                    {'range': [50, 75], 'color': '#FF9500'},
                    {'range': [75, 100], 'color': '#FF3B30'}],
            }
        ))
        
        fig.update_layout(paper_bgcolor="#1E1E1E", font={'color': "white"}, height=350)
        st.plotly_chart(fig, use_container_width=True)
        
        # Status box
        if threat_score < 25:
            st.success(f"✅ Safe: Model classifies this packet as NORMAL. (Confidence: {pred_info['anomaly_score']:.3f})")
        elif threat_score < 75:
            st.warning(f"⚠️ Suspicious: Model detects anomalies. (Severity: {pred_info['severity']})")
        else:
            st.error(f"🚨 CRITICAL THREAT DETECTED (Decision: {pred_info['decision']})")
            
        with st.expander("Raw Packet Data payload"):
            st.json(record)

if page == "Overview":
    overview_page()
elif page == "Live Traffic Monitor":
    live_monitor_page()
elif page == "Alerts & Investigation":
    alerts_investigation_page()
elif page == "System Evaluation":
    evaluation_page()
elif page == "Interactive Threat Simulator":
    threat_simulator_page()
else:
    st.title("Work in Progress")
