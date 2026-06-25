import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import numpy as np
import librosa
import tensorflow as tf
import sounddevice as sd

# Dynamic Path Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(REPO_ROOT, "models", "audio_anomaly.tflite")

# DSP Settings
SAMPLE_RATE = 16000
DURATION = 5
N_MFCC = 40

def load_tflite_model():
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Audio model missing at {MODEL_PATH}")
        return None
    interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tflites() if hasattr(interpreter, "allocate_tflites") else interpreter.allocate_tensors()
    return interpreter

def run_inference(interpreter, mfcc_features):
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    input_data = np.array([mfcc_features], dtype=np.float32)
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    return interpreter.get_tensor(output_details[0]['index'])[0][0]

# --- THIS IS THE NEW MODULAR FUNCTION ---
def verify_audio_emergency():
    """Wakes up the mic, records for 10s, and returns True if anomaly detected."""
    interpreter = load_tflite_model()
    if interpreter is None:
        return False

    print("\n🎤 [STAGE 2 ACTIVATED] Motion triggered audio verification. Recording 5s...")
    
    # Record audio
    audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    
    audio_flat = audio_data.flatten()
    peak_volume = np.max(np.abs(audio_flat))
    
    if peak_volume >= 0.005:
        # Normalize volume to match training data
        audio_flat = audio_flat / peak_volume

    print("🎛️ Analyzing audio signature...")
    mfccs = librosa.feature.mfcc(y=audio_flat, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
    mfccs_processed = np.mean(mfccs.T, axis=0)
    
    probability = run_inference(interpreter, mfccs_processed)
    print(f"📊 Audio Threat Probability: {probability:.4f}")
    
    if probability > 0.5:
        print("🚨 [AUDIO CONFIRMED] High threat signature detected!")
        return True
    else:
        print("🟢 [AUDIO SAFE] False alarm. Ambient noise only.")
        return False

def verify_audio_file(file_path):
    """Reads a .wav file, extracts features, and returns True if anomaly detected."""
    interpreter = load_tflite_model()
    if interpreter is None:
        return False

    print(f"\n🎤 [STAGE 2 ACTIVATED] Analyzing uploaded audio file: {file_path}")
    
    # Load audio
    try:
        audio, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=DURATION)
    except Exception as e:
        print(f"❌ Error loading audio file: {e}")
        return False
        
    # Ensure exact sample pad/truncate for consistency
    required_samples = SAMPLE_RATE * DURATION
    if len(audio) < required_samples:
        audio = np.pad(audio, (0, required_samples - len(audio)), 'constant')
    else:
        audio = audio[:required_samples]
    
    audio_flat = audio.flatten()
    peak_volume = np.max(np.abs(audio_flat))
    
    if peak_volume >= 0.005:
        # Normalize volume to match training data
        audio_flat = audio_flat / peak_volume

    print("🎛️ Analyzing audio signature...")
    mfccs = librosa.feature.mfcc(y=audio_flat, sr=SAMPLE_RATE, n_mfcc=N_MFCC)
    mfccs_processed = np.mean(mfccs.T, axis=0)
    
    probability = run_inference(interpreter, mfccs_processed)
    print(f"📊 Audio Threat Probability: {probability:.4f}")
    
    if probability > 0.5:
        print("🚨 [AUDIO CONFIRMED] High threat signature detected!")
        return True
    else:
        print("🟢 [AUDIO SAFE] False alarm. Ambient noise only.")
        return False

if __name__ == "__main__":
    # If this script is run directly from the terminal (or subprocess), execute the live mic function
    verify_audio_emergency()