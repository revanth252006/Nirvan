import os
import sys
import time
import numpy as np
import tensorflow as tf
import cv2

sys.stdout.reconfigure(encoding='utf-8')

# Dynamic Path Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(REPO_ROOT, "models", "camera_anomaly.tflite")

# Inference Settings
IMG_SIZE = (224, 224)
CAPTURE_DURATION = 3  # seconds
FRAMES_TO_ANALYZE = 5

def load_tflite_model():
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Error: Camera model missing at {MODEL_PATH}")
        print("Please train the model first using 'python src/train_camera.py'")
        return None
    try:
        interpreter = tf.lite.Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()
        return interpreter
    except Exception as e:
        print(f"❌ Error loading TFLite model: {e}")
        return None

def preprocess_frame(frame):
    # Resize and convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb_frame, IMG_SIZE)
    # MobileNetV2 preprocessing: scale pixels to [-1, 1]
    input_data = (np.float32(resized) / 127.5) - 1.0
    return np.expand_dims(input_data, axis=0)

def run_inference(interpreter, preprocessed_frame):
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    interpreter.set_tensor(input_details[0]['index'], preprocessed_frame)
    interpreter.invoke()
    
    return interpreter.get_tensor(output_details[0]['index'])[0][0]

def verify_camera_emergency():
    """Wakes up the camera, captures a short clip, analyzes frames, and returns True if threat detected."""
    interpreter = load_tflite_model()
    # If model is not trained yet, default to safe so the pipeline doesn't break
    if interpreter is None:
        print("⚠️ Camera model not found. Defaulting to safe.")
        return False

    print(f"\n📷 [STAGE 3 ACTIVATED] Audio threat confirmed. Waking up Camera for {CAPTURE_DURATION}s...")
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Could not access the webcam.")
        return False

    frames = []
    start_time = time.time()
    
    # Capture frames for CAPTURE_DURATION seconds
    while (time.time() - start_time) < CAPTURE_DURATION:
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
        else:
            break
        # Slight delay to avoid capturing too many identical frames
        time.sleep(0.1)
        
    cap.release()
    
    if not frames:
        print("❌ Error: No frames captured from webcam.")
        return False

    print(f"🎛️ Captured {len(frames)} frames. Analyzing {min(FRAMES_TO_ANALYZE, len(frames))} samples...")
    
    # Select a few evenly spaced frames to analyze
    indices = np.linspace(0, len(frames) - 1, min(FRAMES_TO_ANALYZE, len(frames)), dtype=int)
    
    max_probability = 0.0
    for idx in indices:
        preprocessed = preprocess_frame(frames[idx])
        prob = run_inference(interpreter, preprocessed)
        if prob > max_probability:
            max_probability = prob
            
    print(f"📊 Camera Threat Probability: {max_probability:.4f}")
    
    if max_probability > 0.5:
        print("🚨 [CAMERA CONFIRMED] VISUAL THREAT DETECTED! 🚨")
        return True
    else:
        print("🟢 [CAMERA SAFE] No visual threat detected. You're safe.")
        return False

def verify_camera_file(file_path):
    """Reads an image file, preprocesses it, and returns True if anomaly detected."""
    interpreter = load_tflite_model()
    if interpreter is None:
        return False

    print(f"\n📷 [STAGE 3 ACTIVATED] Analyzing uploaded camera image: {file_path}")
    
    frame = cv2.imread(file_path)
    if frame is None:
        print(f"❌ Error loading image file: {file_path}")
        return False

    preprocessed = preprocess_frame(frame)
    probability = run_inference(interpreter, preprocessed)
    
    print(f"📊 Camera Threat Probability: {probability:.4f}")
    
    if probability > 0.5:
        print("🚨 [CAMERA CONFIRMED] VISUAL THREAT DETECTED! 🚨")
        return True
    else:
        print("🟢 [CAMERA SAFE] No visual threat detected. You're safe.")
        return False

if __name__ == "__main__":
    verify_camera_emergency()
