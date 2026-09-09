import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
import joblib
import os
import sys
from pathlib import Path

# Add project root to path so we can import configs
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, COLUMNS, MODELS_DIR

class DataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.categorical_cols = ['protocol_type', 'service', 'flag']
        self.label_encoders = {}
        self.attack_encoder = LabelEncoder()
        
    def load_data(self, filepath):
        """Loads data from raw text file and applies columns."""
        df = pd.read_csv(filepath, header=None)
        
        # NSL-KDD sometimes has an extra column at the end
        if len(df.columns) == len(COLUMNS) + 1:
            df.columns = COLUMNS + ['extra_col']
            df.drop('extra_col', axis=1, inplace=True)
        elif len(df.columns) == len(COLUMNS):
            df.columns = COLUMNS
            
        return df
        
    def map_attacks(self, df):
        """Map specific attacks to normal/attack or specific categories."""
        # Work on an explicit copy to avoid SettingWithCopyWarning
        df = df.copy()
        # For simplicity in this baseline, we will map 'normal' to 0 and everything else to 1
        df['label'] = df['attack_type'].apply(lambda x: 0 if x == 'normal' else 1)
        # Drop difficulty level and original attack_type
        df = df.drop(['attack_type', 'difficulty_level'], axis=1, errors='ignore')
        return df

    def fit_transform(self, df):
        """Fit transformers and transform the data."""
        df = self.map_attacks(df)
        
        y = df['label'].values
        X = df.drop('label', axis=1)
        
        # One-hot encode categorical features
        X_encoded = pd.get_dummies(X, columns=self.categorical_cols)
        self.encoded_columns = X_encoded.columns
        
        # Scale all features
        X_scaled = self.scaler.fit_transform(X_encoded)
        
        return X_scaled, y, X_encoded.columns

    def transform(self, df):
        """Transform new data using fitted transformers."""
        df = self.map_attacks(df)
        
        if 'label' in df.columns:
            y = df['label'].values
            X = df.drop('label', axis=1)
        else:
            y = None
            X = df
            
        X_encoded = pd.get_dummies(X, columns=self.categorical_cols)
        
        # Handle missing columns after one-hot encoding (if any category was missing in test set)
        missing_cols = set(self.encoded_columns) - set(X_encoded.columns)
        for c in missing_cols:
            X_encoded[c] = 0
            
        X_encoded = X_encoded[self.encoded_columns] # Reorder to match training
        
        X_scaled = self.scaler.transform(X_encoded)
        return X_scaled, y
        
    def save_artifacts(self, save_dir=MODELS_DIR / 'preprocessing'):
        """Save the fitted scaler and column names."""
        save_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.scaler, save_dir / 'scaler.pkl')
        joblib.dump(self.encoded_columns, save_dir / 'encoded_columns.pkl')
        
    def load_artifacts(self, load_dir=MODELS_DIR / 'preprocessing'):
        """Load the fitted scaler and column names."""
        self.scaler = joblib.load(load_dir / 'scaler.pkl')
        self.encoded_columns = joblib.load(load_dir / 'encoded_columns.pkl')

if __name__ == "__main__":
    print("Initializing DataPreprocessor...")
    preprocessor = DataPreprocessor()
    
    train_path = RAW_DATA_DIR / 'KDDTrain+.txt'
    test_path = RAW_DATA_DIR / 'KDDTest+.txt'
    
    if train_path.exists() and test_path.exists():
        print("Loading training data...")
        df_train = preprocessor.load_data(train_path)
        
        print("Fitting and transforming training data...")
        X_train, y_train, cols = preprocessor.fit_transform(df_train)
        
        print("Saving preprocessing artifacts...")
        preprocessor.save_artifacts()
        
        print("Loading testing data...")
        df_test = preprocessor.load_data(test_path)
        
        print("Transforming testing data...")
        X_test, y_test = preprocessor.transform(df_test)
        
        print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
        print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
        
        # Save processed data
        print("Saving processed datasets...")
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        np.save(PROCESSED_DATA_DIR / 'X_train.npy', X_train)
        np.save(PROCESSED_DATA_DIR / 'y_train.npy', y_train)
        np.save(PROCESSED_DATA_DIR / 'X_test.npy', X_test)
        np.save(PROCESSED_DATA_DIR / 'y_test.npy', y_test)
        print("Preprocessing complete!")
    else:
        print("Raw datasets not found. Please run download_dataset.py first.")
