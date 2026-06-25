import numpy as np
from flask import Flask, request, jsonify

# 1. Import your working Agents
from agents.microphone_agent import verify_audio_emergency
from agents.camera_agent import verify_camera_emergency
import requests

app = Flask(__name__)

# --- Configuration ---
ACCEL_THRESHOLD = 500.0  # Adjust this value based on your sudden movement/fall tests

# --- Sensor Logger Receiver ---
@app.route('/logs', methods=['POST'])
def receive_sensor_data():
    """Phase 1: Constantly listens to Sensor Logger pushing data from your phone."""
    data = request.json
    
    if data and 'payload' in data:
        for reading in data['payload']:
            if reading.get('name') == 'accelerometer':
                # Calculate total acceleration force magnitude: sqrt(x^2 + y^2 + z^2)
                values = reading.get('values', {})
                x = values.get('x', 0)
                y = values.get('y', 0)
                z = values.get('z', 0)
                
                magnitude = np.sqrt(x**2 + y**2 + z**2)
                
                # Check if movement crosses our abnormal threshold
                if magnitude > ACCEL_THRESHOLD:
                    print(f"\n⚠️ [STAGE 1 TRIGGERED] Severe motion magnitude detected: {magnitude:.2f} m/s²")
                    
                    # 2. Fire off Stage 2 instantly by calling your imported agent
                    threat_confirmed = verify_audio_emergency()
                    
                    if threat_confirmed:
                        print("🔥 [CRITICAL] Audio confirms threat! Stage 1 & 2 verified.")
                        
                        # 3. Fire off Stage 3 (Camera) 
                        camera_threat = verify_camera_emergency()
                        
                        if camera_threat:
                            print("🚨 [SOS TRIGGERED] Camera verified threat! Sending SOS to backend...")
                            try:
                                # Trigger backend SOS API specifically for the AI Agent
                                payload = {"user_id": 1} # Assuming default user 1 for the daemon
                                response = requests.post("http://127.0.0.1:8000/safety/agent_sos", json=payload)
                                print(f"📡 SOS Alert Response: {response.status_code}")
                            except Exception as e:
                                print(f"❌ Failed to send SOS to backend: {e}")
                        else:
                            print("🟢 [STAND DOWN] Camera is safe. False alarm.")
                    else:
                        print("🟢 [STAND DOWN] Audio is safe. False alarm.")
                        
    return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    print("🛡️ Nirvan Security Server Online.")
    print("📡 Listening for Sensor Logger stream on Port 5000...")
    print("--------------------------------------------------")
    app.run(host='0.0.0.0', port=5000)