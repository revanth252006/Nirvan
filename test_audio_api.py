import requests
import os

# 1. Start your FastAPI server in another terminal before running this:
# uvicorn server.test_api:app --host 0.0.0.0 --port 8000

API_URL = "http://127.0.0.1:8000/verify_audio"

# Grab a test file from your Kaggle dataset
TEST_FOLDER = r"D:\Nirvan\audio_training_lab\kaggle_dataset\1_anomaly"

# Find the first .wav file
files = [f for f in os.listdir(TEST_FOLDER) if f.endswith('.wav')]
if not files:
    print("❌ No .wav files found to test!")
    exit()

test_file_path = os.path.join(TEST_FOLDER, files[0])
print(f"📁 Simulating mobile phone uploading: {files[0]}")

# Open the file and send it to the FastAPI /verify_audio endpoint
with open(test_file_path, "rb") as f:
    files_payload = {"file": (files[0], f, "audio/wav")}
    try:
        print("🚀 Sending POST request to backend...")
        response = requests.post(API_URL, files=files_payload)
        
        # Print the response from the server
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is your FastAPI server running?")
        print("Run this in your terminal first: uvicorn server.test_api:app --host 0.0.0.0 --port 8000")
