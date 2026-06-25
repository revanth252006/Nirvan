import sys
import numpy as np
import tensorflow as tf
import subprocess  # Added for launching the independent microphone agent
from fastapi import FastAPI, HTTPException, Request, File, UploadFile, BackgroundTasks
import os
import shutil
from agents.microphone_agent import verify_audio_file, verify_audio_emergency
from agents.camera_agent import verify_camera_emergency
import threading

app = FastAPI(title="Nirvan Motion Agent Wi-Fi Bridge")

# Global state to pause motion detection during audio analysis
is_paused_for_audio = False


# Load the TFLite model into memory globally
TFLITE_MODEL_PATH = "models/motion_model.tflite"
try:
    interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print(f"Successfully loaded TFLite engine from {TFLITE_MODEL_PATH}")
except Exception as e:
    print(f"Failed to initialize TFLite model: {e}")

@app.post("/predict")
async def predict_motion(request: Request, background_tasks: BackgroundTasks):
    global is_paused_for_audio
    
    if is_paused_for_audio:
        return {"status": "Paused", "message": "Microphone agent is analyzing audio, ignoring motion inputs."}

    try:
        body = await request.json()
        payload_list = body.get("payload", [])
        
        if not payload_list:
            return {"status": "Success", "message": "Empty payload received."}

        if len(payload_list) < 5:
            print("\n⚡ [CONNECTION SUCCESS] Phone successfully communicated with the backend via ngrok!")
            return {"status": "Success", "message": "Connection verified successfully!"}

        accel_readings = []
        gyro_readings = []

        for item in payload_list:
            sensor_name = item.get("name", item.get("sensor", "")).lower()
            sensor_data = item.get("values", item.get("data", {}))
            
            x = float(sensor_data.get("x", 0.0))
            y = float(sensor_data.get("y", 0.0))
            z = float(sensor_data.get("z", 0.0))

            # Catch both "accelerometer" and "linear acceleration"
            if "accel" in sensor_name:
                accel_readings.append([x, y, z])
            elif "gyro" in sensor_name:
                gyro_readings.append([x, y, z])

        num_samples = min(len(accel_readings), len(gyro_readings))

        if num_samples == 0:
            print(f"📥 Received packet: Accel={len(accel_readings)} rows, Gyro={len(gyro_readings)} rows. Synchronizing...")
            return {"status": "Processing", "message": "Collecting balanced streams..."}

        # Construct the full execution history matrix for this batch
        full_batch = []
        for i in range(num_samples):
            full_batch.append([
                accel_readings[i][0], accel_readings[i][1], accel_readings[i][2],
                gyro_readings[i][0],  gyro_readings[i][1],  gyro_readings[i][2]
            ])

        # DIAGNOSTIC: Calculate peak acceleration magnitude in this batch
        accel_mags = [np.linalg.norm(row[:3]) for row in full_batch]
        peak_accel = max(accel_mags) if accel_mags else 0.0
        print(f"📊 Diagnostic -> Peak Raw Accel Magnitude: {peak_accel:.2f}")

        # Sliding window parameters
        window_size = 100
        stride = 25  # Shift forward by 25 frames each step to check for spikes
        
        max_prediction = 0.0
        highest_status = "✅ Normal Activity"

        # If the batch is smaller than 100 frames, pad it out
        if len(full_batch) < window_size:
            padding_needed = window_size - len(full_batch)
            last_row = full_batch[-1]
            for _ in range(padding_needed):
                full_batch.append(last_row)
            
            input_data = np.array([full_batch], dtype=np.float32)
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()
            max_prediction = float(interpreter.get_tensor(output_details[0]['index'])[0][0])
        else:
            # Scan across the entire incoming packet block to locate the anomaly peak
            for start_idx in range(0, len(full_batch) - window_size + 1, stride):
                raw_window = full_batch[start_idx : start_idx + window_size]
                input_data = np.array([raw_window], dtype=np.float32)
                
                interpreter.set_tensor(input_details[0]['index'], input_data)
                interpreter.invoke()
                
                prediction = float(interpreter.get_tensor(output_details[0]['index'])[0][0])
                if prediction > max_prediction:
                    max_prediction = prediction

        if max_prediction > 0.3:
            highest_status = "TRIGGER_AUDIO_RECORDING"
            print("\n🚨 IMPACT DETECTED! Requesting mobile device to start recording audio...")
            
            # Pause motion detection while waiting for mobile to send audio
            is_paused_for_audio = True

        print(f"🚀 Evaluated Batch ({num_samples} samples) -> Max Score: {max_prediction:.4f} -> {highest_status}")
        return {"probability": float(max_prediction), "status": highest_status}

    except Exception as e:
        print(f"Error handling request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal script error: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "Bridge Online"}

@app.post("/verify_audio")
async def verify_audio(file: UploadFile = File(...)):
    global is_paused_for_audio
    try:
        # Save uploaded file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Analyze the file
        is_threat = verify_audio_file(temp_file_path)
        
        # Clean up
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        # Unpause motion detection so it can start listening again
        is_paused_for_audio = False
            
        if is_threat:
            print("🔥 [CRITICAL] Audio confirms threat! Ready for Stage 3 (Camera)...")
            return {"status": "AUDIO_CONFIRMED", "message": "High threat signature detected!"}
        else:
            print("🟢 [STAND DOWN] Audio is safe. Resuming motion agent.")
            return {"status": "AUDIO_SAFE", "message": "Ambient noise only."}
            
    except Exception as e:
        # Also ensure we unpause if there is an error
        is_paused_for_audio = False
        print(f"Error handling audio verification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal script error: {str(e)}")