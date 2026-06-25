import os
import numpy as np
import librosa
import tensorflow as tf
from sklearn.model_selection import train_test_split

# Dynamic Configuration Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)      # Points to nirvan-motion-agent
PARENT_DIR = os.path.dirname(REPO_ROOT)     # Points to D:\Nirvan

# Check where the dataset folder lives and set the correct absolute path
if os.path.exists(os.path.join(PARENT_DIR, "audio_training_lab")):
    DATASET_PATH = os.path.join(PARENT_DIR, "audio_training_lab", "kaggle_dataset")
else:
    DATASET_PATH = os.path.join(REPO_ROOT, "audio_training_lab", "kaggle_dataset")

MODEL_OUTPUT_PATH = os.path.join(REPO_ROOT, "models", "audio_anomaly.tflite")
SAMPLE_RATE = 16000
DURATION = 5  # 5-second clips to match blueprint

def load_and_preprocess_data():
    X = []
    y = []
    
    # Expected subfolder structure
    categories = {"0_normal": 0, "1_anomaly": 1}
    
    print(f"📂 Scanning dataset directory: {DATASET_PATH}")
    print("🎙️ Extracting acoustic features...")
    
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Error: Dataset path '{DATASET_PATH}' not found!")
        print("Please verify your folder location and try again.")
        return None, None

    for category, label in categories.items():
        dir_path = os.path.join(DATASET_PATH, category)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"📁 Created empty folder: {dir_path}")
            continue
            
        file_list = [f for f in os.listdir(dir_path) if f.endswith(".wav")]
        print(f"🔍 Found {len(file_list)} files in folder: {category}")
            
        for file_name in file_list:
            file_path = os.path.join(dir_path, file_name)
            try:
                # Load audio file, forcing mono and setting a unified sample rate
                audio, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
                
                # Ensure exact sample pad/truncate for consistency (160000 samples)
                required_samples = SAMPLE_RATE * DURATION
                if len(audio) < required_samples:
                    audio = np.pad(audio, (0, required_samples - len(audio)), 'constant')
                else:
                    audio = audio[:required_samples]
                
                # Extract MFCCs (Mel-Frequency Cepstral Coefficients)
                mfccs = librosa.feature.mfcc(y=audio, sr=SAMPLE_RATE, n_mfcc=40)
                mfccs_processed = np.mean(mfccs.T, axis=0)
                
                X.append(mfccs_processed)
                y.append(label)
            except Exception as e:
                print(f"⚠️ Skipping corrupted file {file_name}: {e}")

    return np.array(X), np.array(y)

def train_and_export():
    X, y = load_and_preprocess_data()
    
    if X is None or len(X) == 0:
        print("🛑 Training aborted. Ensure your raw .wav files are copied into the folders above.")
        return

    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"📊 Dataset split complete. Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

    # Build a fast, lightweight Dense Network for TFLite edge deployment
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(40,)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(1, activation='sigmoid')  # Binary classification output (0 or 1)
    ])

    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    print("\n🚀 Commencing model training...")
    model.fit(X_train, y_train, epochs=30, batch_size=8, validation_data=(X_test, y_test))

    # Evaluate performance
    loss, accuracy = model.evaluate(X_test, y_test)
    print(f"\n✅ Model validation accuracy: {accuracy*100:.2f}%")

    # Convert trained architecture into compressed TFLite format
    print(f"📦 Compiling and exporting directly to {MODEL_OUTPUT_PATH}...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    # Create models directory if missing
    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    
    with open(MODEL_OUTPUT_PATH, "wb") as f:
        f.write(tflite_model)
    print("🎉 TFLite conversion complete! Audio agent brain is locked and loaded.")

if __name__ == "__main__":
    train_and_export()