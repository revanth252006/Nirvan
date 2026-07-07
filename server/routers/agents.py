import os
import shutil
import numpy as np
import tensorflow as tf
import time
from fastapi import APIRouter, HTTPException, Request, File, UploadFile, BackgroundTasks, Depends

from .auth import get_current_user
from .. import models

import sys
# Adjust path to import agents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from agents.microphone_agent import verify_audio_file
from agents.camera_agent import verify_camera_file

router = APIRouter(prefix="/agents", tags=["Agents"])

# Dictionary to track which users are paused waiting for audio upload
paused_users: dict[str, float] = {}
PAUSE_TIMEOUT = 30 # seconds

# Dynamic Path Configuration for Motion Model
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
TFLITE_MODEL_PATH = os.path.join(REPO_ROOT, "models", "motion_model.tflite")

try:
    interpreter = tf.lite.Interpreter(model_path=TFLITE_MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print(f"✅ Successfully loaded Motion TFLite engine from {TFLITE_MODEL_PATH}")
except Exception as e:
    print(f"⚠️ Failed to initialize Motion TFLite model: {e}")
    interpreter = None

def _cleanup_expired_pauses():
    current_time = time.time()
    expired_users = [uid for uid, timestamp in paused_users.items() if current_time - timestamp > PAUSE_TIMEOUT]
    for uid in expired_users:
        del paused_users[uid]

@router.post("/predict")
async def predict_motion(
    request: Request, 
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user)
):
    _cleanup_expired_pauses()
    
    uid_str = str(current_user.id)
    if uid_str in paused_users:
        return {"status": "Paused", "message": "Microphone agent is analyzing audio, ignoring motion inputs."}

    if interpreter is None:
        # Fallback if model not found
        return {"probability": 0.0, "status": "✅ Normal Activity"}

    try:
        body = await request.json()
        payload_list = body.get("payload", [])
        
        if not payload_list:
            return {"status": "Success", "message": "Empty payload received."}

        if len(payload_list) < 5:
            return {"status": "Success", "message": "Connection verified successfully!"}

        accel_readings = []
        gyro_readings = []

        for item in payload_list:
            sensor_name = item.get("name", item.get("sensor", "")).lower()
            sensor_data = item.get("values", item.get("data", {}))
            
            x = float(sensor_data.get("x", 0.0))
            y = float(sensor_data.get("y", 0.0))
            z = float(sensor_data.get("z", 0.0))

            if "accel" in sensor_name:
                accel_readings.append([x, y, z])
            elif "gyro" in sensor_name:
                gyro_readings.append([x, y, z])

        num_samples = min(len(accel_readings), len(gyro_readings))

        if num_samples == 0:
            return {"status": "Processing", "message": "Collecting balanced streams..."}

        full_batch = []
        for i in range(num_samples):
            full_batch.append([
                accel_readings[i][0], accel_readings[i][1], accel_readings[i][2],
                gyro_readings[i][0],  gyro_readings[i][1],  gyro_readings[i][2]
            ])

        window_size = 100
        stride = 25
        max_prediction = 0.0
        highest_status = "✅ Normal Activity"

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
            print(f"\n🚨 IMPACT DETECTED! Requesting mobile device (User {uid_str}) to start recording audio...")
            paused_users[uid_str] = time.time()

        return {"probability": float(max_prediction), "status": highest_status}

    except Exception as e:
        print(f"Error handling request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal script error: {str(e)}")

@router.post("/verify_audio")
async def verify_audio(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    uid_str = str(current_user.id)
    os.makedirs("uploads/temp", exist_ok=True)
    temp_file_path = f"uploads/temp/user_{uid_str}_{file.filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        is_threat = verify_audio_file(temp_file_path)
            
        if is_threat:
            print(f"🔥 [CRITICAL] Audio confirms threat for User {uid_str}! Ready for Stage 3 (Camera)...")
            return {"status": "AUDIO_CONFIRMED", "message": "High threat signature detected!", "probability": 1.0}
        else:
            print(f"🟢 [STAND DOWN] Audio is safe for User {uid_str}. Resuming motion agent.")
            return {"status": "AUDIO_SAFE", "message": "Ambient noise only.", "probability": 0.0}
            
    except Exception as e:
        print(f"Error handling audio verification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal script error: {str(e)}")
    finally:
        # Guarantee cleanup even on failure
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if uid_str in paused_users:
            del paused_users[uid_str]

@router.post("/verify_camera")
async def verify_camera(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user)
):
    uid_str = str(current_user.id)
    os.makedirs("uploads/temp", exist_ok=True)
    temp_file_path = f"uploads/temp/user_{uid_str}_{file.filename}"
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        is_threat = verify_camera_file(temp_file_path)
            
        if is_threat:
            print(f"🚨 [STAGE 3 CONFIRMED] Camera detected visual threat for User {uid_str}! INITIATING SOS!")
            return {"status": "CAMERA_CONFIRMED", "message": "Visual threat detected!", "probability": 1.0}
        else:
            print(f"🟢 [CAMERA SAFE] Camera is safe for User {uid_str}.")
            return {"status": "CAMERA_SAFE", "message": "No visual threat detected.", "probability": 0.0}
            
    except Exception as e:
        print(f"Error handling camera verification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal script error: {str(e)}")
    finally:
        # Guarantee cleanup even on failure
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
