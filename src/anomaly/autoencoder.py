import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import joblib
import sys
from pathlib import Path
import os
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import PROCESSED_DATA_DIR, MODELS_DIR, DNN_BATCH_SIZE, DNN_EPOCHS, LEARNING_RATE

def create_autoencoder(input_dim):
    # Encoder
    input_layer = Input(shape=(input_dim,))
    encoder = Dense(64, activation="relu")(input_layer)
    encoder = Dropout(0.2)(encoder)
    encoder = Dense(32, activation="relu")(encoder)
    
    # Bottleneck
    bottleneck = Dense(16, activation="relu")(encoder)
    
    # Decoder
    decoder = Dense(32, activation="relu")(bottleneck)
    decoder = Dropout(0.2)(decoder)
    decoder = Dense(64, activation="relu")(decoder)
    
    # Output
    output_layer = Dense(input_dim, activation="linear")(decoder)
    
    autoencoder = Model(inputs=input_layer, outputs=output_layer)
    optimizer = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE)
    autoencoder.compile(optimizer=optimizer, loss='mse')
    
    return autoencoder

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

    # To train the autoencoder to recognize "normal" traffic,
    # we filter the training dataset to include ONLY normal traffic (label = 0)
    normal_indices = (y_train == 0)
    X_train_normal = X_train[normal_indices]
    
    print(f"Total training samples: {X_train.shape[0]}")
    print(f"Normal training samples (for AE): {X_train_normal.shape[0]}")
    
    anomaly_dir = MODELS_DIR / 'anomaly_detector'
    anomaly_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = anomaly_dir / 'autoencoder.h5'
    
    autoencoder = create_autoencoder(X_train_normal.shape[1])
    
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        ModelCheckpoint(filepath=str(model_path), monitor='val_loss', save_best_only=True)
    ]
    
    print("Training Autoencoder...")
    history = autoencoder.fit(
        X_train_normal, X_train_normal,
        validation_split=0.2,
        epochs=DNN_EPOCHS,
        batch_size=DNN_BATCH_SIZE,
        callbacks=callbacks,
        verbose=1
    )
    
    # Determine anomaly threshold using the validation set (or normal training data)
    best_ae = autoencoder
    reconstructions = best_ae.predict(X_train_normal)
    mse = np.mean(np.power(X_train_normal - reconstructions, 2), axis=1)
    
    # Set threshold as 95th percentile of normal reconstruction errors
    threshold = np.percentile(mse, 95)
    print(f"Determined Anomaly Threshold: {threshold:.4f}")
    
    # Save threshold
    joblib.dump(threshold, anomaly_dir / 'threshold.pkl')
    
    # Quick Test on full test set
    test_reconstructions = best_ae.predict(X_test)
    test_mse = np.mean(np.power(X_test - test_reconstructions, 2), axis=1)
    
    y_pred_anomaly = (test_mse > threshold).astype(int)
    
    from sklearn.metrics import confusion_matrix, classification_report
    print("\nAnomaly Detection Results on Test Set (0=Normal, 1=Anomaly/Attack):")
    print(classification_report(y_test, y_pred_anomaly))

if __name__ == "__main__":
    main()
