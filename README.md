# AegisIDS — Adaptive and Explainable Deep Learning-Based Intrusion Detection System

## 🛡️ Project Overview
AegisIDS is a complete, production-quality academic prototype for a next-generation Intrusion Detection System (IDS). 
Unlike traditional systems that rely solely on known signatures, AegisIDS combines a **Deep Neural Network (DNN)** for classifying known attacks with an **Autoencoder-based Anomaly Detector** to identify zero-day or unseen malicious behaviors.

The system incorporates **Explainable AI (XAI)** using SHAP to interpret model decisions, calculating a normalized **Threat Score** based on confidence and anomaly levels to prioritize critical threats and significantly reduce false positives.

## 🚀 Architecture
The system follows a modular architecture:
1. **Traffic Ingestion & Preprocessing**: Handles missing values, scaling, and categorical encoding using robust Scikit-Learn pipelines.
2. **DNN Classifier**: Predicts known attack categories (Normal vs Malicious).
3. **Autoencoder Anomaly Detector**: Flags unusual traffic patterns based on reconstruction error thresholds.
4. **Decision Engine & Fusion**: Merges predictions and anomaly scores to finalize a high-fidelity threat decision.
5. **XAI Engine (SHAP)**: Explains the top contributing features for malicious predictions.
6. **Alert System**: Generates human-readable security alerts prioritizing investigation steps.
7. **Streamlit Dashboard**: A professional UI providing live monitoring, metrics, and interactive visualizations.

## 💾 Dataset
This project uses the **NSL-KDD** dataset, chosen for its diverse attack categories and established baseline performance in academic IDS research.

## ⚙️ Installation & Usage

### 1. Setup Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Download Dataset
```bash
python src/data/download_dataset.py
```

### 3. Preprocess Data
```bash
python src/preprocessing/preprocessor.py
```

### 4. Train Baseline Models & Perform Feature Selection
```bash
python src/features/feature_selection.py
python src/models/baseline_models.py
```

### 5. Train Core AegisIDS Models
Train the DNN Classifier and Autoencoder:
```bash
python src/models/dnn_classifier.py
python src/anomaly/autoencoder.py
```

### 6. Run the AegisIDS System (Expo Frontend + FastAPI Backend)

#### Step A: Start the FastAPI Backend Server
```bash
python run.py --api
# Or: uvicorn api.server:app --port 8000 --reload
```

#### Step B: Start the Expo Mobile/Web Dashboard
```bash
python run.py --expo
# Or: cd expo-app && npx expo start
```
*Press `w` in the terminal to launch the web dashboard, or scan the QR code with the Expo Go mobile app (iOS / Android).*

---

### Alternative: Legacy Streamlit Console
```bash
python run.py --dashboard
```

## 📊 Experimental Evaluation
AegisIDS clearly demonstrates:
- Enhanced detection of unseen attacks via the Autoencoder thresholding.
- Measurable reduction in false positives through the Decision Fusion engine.
- Deep explainability for analyst review, avoiding "black-box" limitations.
- Comprehensive comparisons against baseline classical ML models (SVM, Random Forest, Logistic Regression).

## 🔮 Future Improvements
- **Real-time Packet Capture (PCAP)** integration.
- Distributed processing using Apache Kafka/Spark.
- Expanding the Adaptive Learning workflow to automate sample verification loops.
- Support for multi-class classification on the CIC-IDS2017 dataset.
