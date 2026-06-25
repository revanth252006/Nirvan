import os
import numpy as np
from sklearn.model_selection import train_test_split

# Absolute imports targeting the src package
from src.model import build_motion_model
from src.preprocess import preprocess_pipeline

def train_pipeline(data_csv_path, save_model_path, epochs=15, batch_size=32):
    os.makedirs(os.path.dirname(save_model_path), exist_ok=True)

    print("--- Phase 1: Preprocessing Sensor Data ---")
    X, y = preprocess_pipeline(data_csv_path)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"Training set size: {X_train.shape[0]} samples")
    print(f"Validation set size: {X_val.shape[0]} samples")

    print("\n--- Phase 2: Initializing Neural Network ---")
    window_size = X.shape[1]
    num_features = X.shape[2]
    
    model = build_motion_model(window_size=window_size, num_features=num_features)

    print("\n--- Phase 3: Commencing Model Training ---")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        verbose=1
    )

    print("\n--- Phase 4: Saving Trained Weights ---")
    model.save(save_model_path)
    print(f"Successfully saved trained model weights to: {save_model_path}")
    
    return history

if __name__ == "__main__":
    dataset_path = "data/raw/mock_sensor_data.csv"
    output_path = "models/motion_model.h5"
    
    # Auto-generate mock data if missing before starting the training
    if not os.path.exists(dataset_path):
        print(f"Template data missing at {dataset_path}. Auto-generating it via preprocessor...")
        os.system("python -m src.preprocess")

    train_pipeline(dataset_path, output_path, epochs=5, batch_size=16)