import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def load_and_clean_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.dropna()
    return df

def create_sliding_windows(df, window_size=100, step_size=50):
    X = []
    y = []
    
    feature_columns = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']
    features = df[feature_columns].values
    labels = df['label'].values

    for i in range(0, len(features) - window_size + 1, step_size):
        window = features[i : i + window_size]
        window_label = 1 if np.any(labels[i : i + window_size] == 1) else 0
        X.append(window)
        y.append(window_label)
        
    return np.array(X), np.array(y).reshape(-1, 1)

def preprocess_pipeline(file_path, window_size=100, step_size=50):
    df = load_and_clean_csv(file_path)
    
    feature_columns = ['accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']
    scaler = StandardScaler()
    df[feature_columns] = scaler.fit_transform(df[feature_columns])
    
    X, y = create_sliding_windows(df, window_size, step_size)
    print(f"Successfully generated X shape: {X.shape} and y shape: {y.shape}")
    return X, y

if __name__ == "__main__":
    import os
    os.makedirs('data/raw', exist_ok=True)
    print("Generating mock data to verify pipeline...")
    mock_data = {
        'accel_x': np.sin(np.linspace(0, 50, 500)),
        'accel_y': np.cos(np.linspace(0, 50, 500)),
        'accel_z': np.random.normal(0, 1, 500),
        'gyro_x': np.random.normal(0, 0.1, 500),
        'gyro_y': np.random.normal(0, 0.1, 500),
        'gyro_z': np.random.normal(0, 0.1, 500),
        'label': np.zeros(500)
    }
    mock_data['label'][220:240] = 1 
    
    df_mock = pd.DataFrame(mock_data)
    df_mock.to_csv('data/raw/mock_sensor_data.csv', index=False)
    X, y = preprocess_pipeline('data/raw/mock_sensor_data.csv')