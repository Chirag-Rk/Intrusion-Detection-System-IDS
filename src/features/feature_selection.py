import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif
import matplotlib.pyplot as plt
import joblib
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import PROCESSED_DATA_DIR, MODELS_DIR

def get_feature_importances():
    print("Loading processed data...")
    try:
        X_train = np.load(PROCESSED_DATA_DIR / 'X_train.npy')
        y_train = np.load(PROCESSED_DATA_DIR / 'y_train.npy')
        encoded_columns = joblib.load(MODELS_DIR / 'preprocessing' / 'encoded_columns.pkl')
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("Calculating Random Forest Feature Importances...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    # Using a subset for faster calculation if the dataset is large
    subset_size = min(50000, len(X_train))
    idx = np.random.choice(len(X_train), subset_size, replace=False)
    
    rf.fit(X_train[idx], y_train[idx])
    importances = rf.feature_importances_
    
    # Sort importances
    indices = np.argsort(importances)[::-1]
    
    print("\nTop 20 Features:")
    top_features = []
    for f in range(min(20, X_train.shape[1])):
        top_features.append((encoded_columns[indices[f]], importances[indices[f]]))
        print(f"{f + 1}. {encoded_columns[indices[f]]} ({importances[indices[f]]})")
        
    # Save top features
    importances_df = pd.DataFrame(top_features, columns=['Feature', 'Importance'])
    importances_df.to_csv(PROCESSED_DATA_DIR / 'feature_importances.csv', index=False)
    
    return top_features

if __name__ == "__main__":
    get_feature_importances()
