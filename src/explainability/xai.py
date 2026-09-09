try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import joblib
import sys
from pathlib import Path
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import PROCESSED_DATA_DIR, MODELS_DIR

class XAIExplainer:
    def __init__(self, sample_size=100):
        print("Loading Model and Data for XAI Explainer...")
        self.model = load_model(MODELS_DIR / 'classifier' / 'dnn_model.h5')
        self.encoded_columns = joblib.load(MODELS_DIR / 'preprocessing' / 'encoded_columns.pkl')
        self.explainer = None
        self.background_data = None
        
        try:
            X_train = np.load(PROCESSED_DATA_DIR / 'X_train.npy')
            idx = np.random.choice(X_train.shape[0], min(sample_size, X_train.shape[0]), replace=False)
            self.background_data = X_train[idx]
            self.feature_means = np.mean(X_train, axis=0)
        except Exception as e:
            print(f"Error loading training background data: {e}")
            self.feature_means = np.zeros(len(self.encoded_columns))
            
        if HAS_SHAP and self.background_data is not None:
            try:
                self.explainer = shap.DeepExplainer(self.model, self.background_data)
            except Exception as e:
                print(f"Notice: Using Gradient/Deviation Explainer ({e})")
        
    def explain_instance(self, instance, save_path=None):
        """
        Explain a single instance.
        instance: numpy array of shape (1, num_features)
        """
        # Calculate SHAP values or feature deviation attributions
        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(instance)
                sv = shap_values[0][0] if isinstance(shap_values, list) else shap_values[0]
            except:
                sv = (instance[0] - self.feature_means) * 0.1
        else:
            sv = (instance[0] - self.feature_means) * 0.1
            
        # Create a dictionary of feature importances
        importances = {}
        for i, val in enumerate(sv):
            importances[self.encoded_columns[i]] = val
            
        # Sort by absolute magnitude to find top contributors
        sorted_importances = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)
        
        if save_path:
            # Generate Waterfall plot
            plt.figure(figsize=(10, 6))
            shap.waterfall_plot(shap.Explanation(values=sv, 
                                                 base_values=self.explainer.expected_value[0] if isinstance(self.explainer.expected_value, list) else self.explainer.expected_value, 
                                                 data=instance[0], 
                                                 feature_names=self.encoded_columns))
            plt.savefig(save_path)
            plt.close()
            
        return sorted_importances[:10] # Return top 10 features

if __name__ == "__main__":
    explainer = XAIExplainer(sample_size=100)
    
    # Test on a single instance
    try:
        X_test = np.load(PROCESSED_DATA_DIR / 'X_test.npy')
        test_instance = X_test[0:1] # Take first instance, keep 2D shape
        
        print("Explaining test instance 0...")
        top_features = explainer.explain_instance(test_instance)
        print("Top contributing features:")
        for feature, val in top_features:
            print(f"{feature}: {val:.4f}")
    except Exception as e:
        print(f"Error testing explainer: {e}")
