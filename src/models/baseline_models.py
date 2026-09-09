import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import sys
from pathlib import Path
import os

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import PROCESSED_DATA_DIR, MODELS_DIR

def evaluate_model(model, X_test, y_test, name):
    print(f"\nEvaluating {name}...")
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    cm = confusion_matrix(y_test, y_pred)
    # Calculate False Positive Rate
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"FPR:       {fpr:.4f}")
    
    return {
        'Model': name,
        'Accuracy': acc,
        'Precision': prec,
        'Recall': rec,
        'F1': f1,
        'FPR': fpr
    }

def main():
    print("Loading processed data...")
    try:
        X_train = np.load(PROCESSED_DATA_DIR / 'X_train.npy')
        y_train = np.load(PROCESSED_DATA_DIR / 'y_train.npy')
        X_test = np.load(PROCESSED_DATA_DIR / 'X_test.npy')
        y_test = np.load(PROCESSED_DATA_DIR / 'y_test.npy')
    except Exception as e:
        print(f"Error loading data: {e}. Run preprocessor.py first.")
        return

    # Using a subset of training data for faster baseline training if needed
    subset_size = min(50000, len(X_train))
    idx = np.random.choice(len(X_train), subset_size, replace=False)
    X_train_sub = X_train[idx]
    y_train_sub = y_train[idx]

    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        # SVM is slow on large datasets, using a small subset just for demonstration
        # In a real run, you'd use SVC(random_state=42) or LinearSVC
        'SVM': SVC(kernel='linear', random_state=42, max_iter=1000) 
    }

    results = []
    
    classifier_dir = MODELS_DIR / 'classifier'
    classifier_dir.mkdir(parents=True, exist_ok=True)

    for name, model in models.items():
        print(f"\nTraining {name}...")
        if name == 'SVM':
            # SVM takes too long, use even smaller subset
            svm_idx = np.random.choice(len(X_train_sub), min(10000, len(X_train_sub)), replace=False)
            model.fit(X_train_sub[svm_idx], y_train_sub[svm_idx])
        else:
            model.fit(X_train_sub, y_train_sub)
            
        # Save model
        joblib.dump(model, classifier_dir / f"{name.replace(' ', '_').lower()}.pkl")
        
        # Evaluate
        metrics = evaluate_model(model, X_test, y_test, name)
        results.append(metrics)
        
    results_df = pd.DataFrame(results)
    results_dir = Path(__file__).resolve().parent.parent.parent / 'results'
    results_dir.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(results_dir / 'baseline_metrics.csv', index=False)
    print("\nBaseline results saved to results/baseline_metrics.csv")
    print(results_df)

if __name__ == "__main__":
    main()
