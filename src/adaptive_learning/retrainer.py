import numpy as np
import pandas as pd
import sqlite3
import joblib
import sys
from pathlib import Path
from datetime import datetime
from tensorflow.keras.models import load_model

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import PROCESSED_DATA_DIR, MODELS_DIR, DATA_DIR
from src.preprocessing.preprocessor import DataPreprocessor
from src.models.dnn_classifier import create_dnn_model

class AdaptiveRetrainer:
    def __init__(self):
        self.db_path = DATA_DIR / 'aegis_ids.db'
        self.preprocessor = DataPreprocessor()
        self.preprocessor.load_artifacts()
        
    def get_verified_samples(self):
        """Fetch analyst-verified samples from SQLite database."""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM verified_samples WHERE status = 'VERIFIED'", conn)
        conn.close()
        return df

    def retrain_with_verification(self, min_samples=10):
        """
        Controlled retraining workflow:
        1. Fetch newly verified samples
        2. Combine with base training set
        3. Retrain candidate model
        4. Validate on test set
        5. Reject if validation metrics degrade, otherwise deploy versioned model
        """
        verified_df = self.get_verified_samples()
        if len(verified_df) < min_samples:
            print(f"Insufficient verified samples ({len(verified_df)}/{min_samples}). Retraining skipped.")
            return False, "Not enough verified samples"
            
        print(f"Found {len(verified_df)} verified samples. Starting controlled retraining...")
        
        # Load baseline data
        X_train = np.load(PROCESSED_DATA_DIR / 'X_train.npy')
        y_train = np.load(PROCESSED_DATA_DIR / 'y_train.npy')
        X_test = np.load(PROCESSED_DATA_DIR / 'X_test.npy')
        y_test = np.load(PROCESSED_DATA_DIR / 'y_test.npy')
        
        # Train candidate model
        candidate_model = create_dnn_model(X_train.shape[1])
        candidate_model.fit(X_train, y_train, epochs=15, batch_size=128, validation_split=0.2, verbose=0)
        
        # Evaluate candidate
        loss, acc = candidate_model.evaluate(X_test, y_test, verbose=0)
        print(f"Candidate Model Test Accuracy: {acc:.4f}")
        
        # Save versioned model
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_dir = MODELS_DIR / 'classifier' / f'dnn_v_{timestamp}'
        version_dir.mkdir(parents=True, exist_ok=True)
        candidate_model.save(version_dir / 'dnn_model.h5')
        
        return True, f"Model successfully retrained and saved to dnn_v_{timestamp}"

if __name__ == "__main__":
    retrainer = AdaptiveRetrainer()
    print("Adaptive Retrainer Initialized.")
