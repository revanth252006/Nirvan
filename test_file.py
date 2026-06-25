import os
import numpy as np
import librosa
import tensorflow as tf

MODEL_PATH = "models/audio_anomaly.tflite"
# Pick the first file from your screaming dataset folder
TEST_FILE = r"D:\Nirvan\audio_training_lab\kaggle_dataset\1_anomaly"

# Find the first actual wav file in that folder
files = [f for f in os.listdir(TEST_FILE) if f.endswith('.wav')]
if not files:
    print("❌ No .wav files found in your anomaly folder!")
    exit()

target_path = os.path.join(TEST_FILE, files[0])
print(f"📁 Testing model against file: {files[0]}")

# Load model
interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Load and process the exact same way as training
audio, sr = librosa.load(target_path, sr=16000)
mfccs = librosa.feature.mfcc(y=audio, sr=16000, n_mfcc=40)
mfccs_processed = np.mean(mfccs.T, axis=0)

# Run Inference
input_data = np.array([mfccs_processed], dtype=np.float32)
interpreter.set_tensor(input_details[0]['index'], input_data)
interpreter.invoke()

prob = interpreter.get_tensor(output_details[0]['index'])[0][0]
print(f"📊 Prediction Probability: {prob:.4f}")
if prob > 0.5:
    print("🚨 SUCCESS: Model correctly identified the anomaly file!")
else:
    print("❌ FAILED: Model thinks the anomaly file is normal.")