import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import sys
from pathlib import Path
import os
import matplotlib.pyplot as plt

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from configs.config import PROCESSED_DATA_DIR, MODELS_DIR, DNN_BATCH_SIZE, DNN_EPOCHS, LEARNING_RATE

def create_dnn_model(input_dim):
    model = Sequential([
        Dense(128, input_dim=input_dim, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        
        Dense(64, activation='relu'),
        BatchNormalization(),
        Dropout(0.2),
        
        Dense(32, activation='relu'),
        Dropout(0.1),
        
        Dense(1, activation='sigmoid')
    ])
    
    optimizer = tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE)
    model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])
    
    return model

def plot_history(history, save_dir):
    plt.figure(figsize=(12, 4))
    
    # Plot Loss
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Val Loss')
    plt.title('Model Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    
    # Plot Accuracy
    plt.subplot(1, 2, 2)
    plt.plot(history.history['accuracy'], label='Train Accuracy')
    plt.plot(history.history['val_accuracy'], label='Val Accuracy')
    plt.title('Model Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    
    save_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_dir / 'dnn_training_history.png')
    plt.close()

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
        
    print(f"X_train shape: {X_train.shape}")
    
    classifier_dir = MODELS_DIR / 'classifier'
    classifier_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = classifier_dir / 'dnn_model.h5'
    
    model = create_dnn_model(X_train.shape[1])
    
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
        ModelCheckpoint(filepath=str(model_path), monitor='val_loss', save_best_only=True)
    ]
    
    print("Training DNN...")
    history = model.fit(
        X_train, y_train,
        validation_split=0.2,
        epochs=DNN_EPOCHS,
        batch_size=DNN_BATCH_SIZE,
        callbacks=callbacks,
        verbose=1
    )
    
    print("\nTraining Complete. Evaluating on test set...")
    # Load best model
    best_model = load_model(model_path)
    
    y_pred_probs = best_model.predict(X_test)
    y_pred = (y_pred_probs > 0.5).astype(int)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    
    # Save plots
    results_dir = Path(__file__).resolve().parent.parent.parent / 'results' / 'figures'
    plot_history(history, results_dir)
    print(f"Training history plot saved to {results_dir}")

if __name__ == "__main__":
    main()
