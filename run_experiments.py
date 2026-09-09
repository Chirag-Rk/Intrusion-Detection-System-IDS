import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, auc, precision_recall_curve
)
import joblib
import sys
import os
from pathlib import Path
from tensorflow.keras.models import load_model

sys.path.append(str(Path(__file__).resolve().parent))
from configs.config import PROCESSED_DATA_DIR, MODELS_DIR

results_dir = Path(__file__).resolve().parent / 'results'
figures_dir = results_dir / 'figures'
results_dir.mkdir(parents=True, exist_ok=True)
figures_dir.mkdir(parents=True, exist_ok=True)

def run_all_experiments():
    print("============================================================")
    print("RUNNING AEGISIDS COMPREHENSIVE EXPERIMENTAL SUITE")
    print("============================================================")
    
    # 1. Load Processed Datasets
    print("\n[Step 1] Loading Datasets...")
    X_train = np.load(PROCESSED_DATA_DIR / 'X_train.npy')
    y_train = np.load(PROCESSED_DATA_DIR / 'y_train.npy')
    X_test = np.load(PROCESSED_DATA_DIR / 'X_test.npy')
    y_test = np.load(PROCESSED_DATA_DIR / 'y_test.npy')
    encoded_columns = joblib.load(MODELS_DIR / 'preprocessing' / 'encoded_columns.pkl')
    
    # 2. Load Trained Models
    print("\n[Step 2] Loading Models...")
    lr_model = joblib.load(MODELS_DIR / 'classifier' / 'logistic_regression.pkl')
    rf_model = joblib.load(MODELS_DIR / 'classifier' / 'random_forest.pkl')
    svm_model = joblib.load(MODELS_DIR / 'classifier' / 'svm.pkl')
    dnn_model = load_model(MODELS_DIR / 'classifier' / 'dnn_model.h5')
    autoencoder = load_model(MODELS_DIR / 'anomaly_detector' / 'autoencoder.h5', compile=False)
    anomaly_threshold = joblib.load(MODELS_DIR / 'anomaly_detector' / 'threshold.pkl')
    
    # 3. Model Predictions
    print("\n[Step 3] Running Inferences for Comparison...")
    lr_pred = lr_model.predict(X_test)
    rf_pred = rf_model.predict(X_test)
    svm_pred = svm_model.predict(X_test)
    
    dnn_probs = dnn_model.predict(X_test, verbose=0).flatten()
    dnn_pred = (dnn_probs > 0.5).astype(int)
    
    # Autoencoder Anomaly Scoring
    reconstructions = autoencoder.predict(X_test, verbose=0)
    ae_mse = np.mean(np.power(X_test - reconstructions, 2), axis=1)
    ae_pred = (ae_mse > anomaly_threshold).astype(int)
    
    # Decision Fusion Prediction (AegisIDS Proposed)
    fusion_pred = np.where((dnn_pred == 1) | (ae_pred == 1), 1, 0)
    
    models = {
        'Logistic Regression': (lr_pred, lr_model.predict_proba(X_test)[:, 1] if hasattr(lr_model, 'predict_proba') else lr_pred),
        'Random Forest': (rf_pred, rf_model.predict_proba(X_test)[:, 1]),
        'SVM (Linear)': (svm_pred, svm_pred),
        'Proposed DNN': (dnn_pred, dnn_probs),
        'AegisIDS (DNN + Anomaly Fusion)': (fusion_pred, (dnn_probs + np.clip(ae_mse / (anomaly_threshold * 2), 0, 1)) / 2)
    }
    
    # 4. Generate Metric Comparison Table
    print("\n[Step 4] Computing Metrics...")
    records = []
    for name, (pred, probs) in models.items():
        acc = accuracy_score(y_test, pred)
        prec = precision_score(y_test, pred, zero_division=0)
        rec = recall_score(y_test, pred, zero_division=0)
        f1 = f1_score(y_test, pred, zero_division=0)
        cm = confusion_matrix(y_test, pred)
        tn, fp, fn, tp = cm.ravel()
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        records.append({
            'Model': name,
            'Accuracy': round(acc, 4),
            'Precision': round(prec, 4),
            'Recall': round(rec, 4),
            'F1-Score': round(f1, 4),
            'False Positive Rate (FPR)': round(fpr, 4),
            'True Positives': int(tp),
            'False Positives': int(fp),
            'True Negatives': int(tn),
            'False Negatives': int(fn)
        })
        
    metrics_df = pd.DataFrame(records)
    metrics_df.to_csv(results_dir / 'model_comparison.csv', index=False)
    metrics_df.to_csv(results_dir / 'metrics.csv', index=False)
    print("\n" + "="*80)
    print(metrics_df.to_string(index=False))
    print("="*80)
    
    # 5. Visualizations
    print("\n[Step 5] Generating Visualizations...")
    
    # Confusion Matrix for AegisIDS Fusion
    plt.figure(figsize=(6, 5))
    cm_fusion = confusion_matrix(y_test, fusion_pred)
    sns.heatmap(cm_fusion, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Normal', 'Attack'], yticklabels=['Normal', 'Attack'])
    plt.title('AegisIDS Hybrid Decision Confusion Matrix')
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.tight_layout()
    plt.savefig(figures_dir / 'confusion_matrix.png', dpi=300)
    plt.close()
    
    # ROC Curves
    plt.figure(figsize=(8, 6))
    for name, (pred, probs) in models.items():
        fpr, tpr, _ = roc_curve(y_test, probs)
        roc_auc = auc(fpr, tpr)
        plt.plot(fpr, tpr, label=f'{name} (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', label='Chance')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Comparison')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figures_dir / 'roc_curve.png', dpi=300)
    plt.close()
    
    # Precision-Recall Curves
    plt.figure(figsize=(8, 6))
    for name, (pred, probs) in models.items():
        pr_precision, pr_recall, _ = precision_recall_curve(y_test, probs)
        plt.plot(pr_recall, pr_precision, label=f'{name}')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve Comparison')
    plt.legend(loc='lower left')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(figures_dir / 'precision_recall.png', dpi=300)
    plt.close()
    
    # Anomaly Error Distribution
    normal_errors = ae_mse[y_test == 0]
    attack_errors = ae_mse[y_test == 1]
    plt.figure(figsize=(8, 5))
    plt.hist(normal_errors, bins=50, alpha=0.6, label='Normal Traffic MSE', color='green', density=True)
    plt.hist(attack_errors, bins=50, alpha=0.6, label='Malicious Traffic MSE', color='red', density=True)
    plt.axvline(anomaly_threshold, color='black', linestyle='--', label=f'Threshold ({anomaly_threshold:.3f})')
    plt.xlabel('Reconstruction Error (MSE)')
    plt.ylabel('Density')
    plt.title('Autoencoder Reconstruction Error Distribution')
    plt.legend()
    plt.tight_layout()
    plt.savefig(figures_dir / 'anomaly_distribution.png', dpi=300)
    plt.close()

    print("All experimental figures and tables saved in 'results/' successfully!")

if __name__ == "__main__":
    run_all_experiments()
