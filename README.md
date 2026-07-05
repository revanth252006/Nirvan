🛡️ Nirvan: The Intelligent Family Guardian

AI-Powered Personal Safety & Real-time Emergency Response
💡 The Problem
In critical emergency situations—such as a severe car crash, a sudden fall, or an assault—victims are often physically unable to reach for their phones to dial emergency services or alert their families. Traditional safety applications rely on active manual triggers, which fundamentally fail when a user is incapacitated or unconscious.

🚀 The Solution: Nirvan
Nirvan is an autonomous, AI-driven personal safety application. It acts as a passive guardian angel, utilizing on-device Machine Learning to detect emergencies in real-time and instantly broadcast alerts to a trusted Family Circle. Instead of waiting for you to ask for help, Nirvan continuously listens and watches for you.

✨ Core Features
🧠 Autonomous AI Agents (TFLite)
Nirvan runs lightweight neural networks directly on your device to ensure total privacy and zero-latency detection:

Audio Anomaly Agent: Continuously processes microphone buffers to isolate distress sounds like screams, shattering glass, or sudden physical impacts.

Motion & Vision Agent: Tracks high-frequency camera frames and accelerometer telemetry to identify falls or high-impact vehicular crashes.

👨‍👩‍👧‍👦 Real-Time Family Circles
Live Tracking: Monitor real-time, high-precision GPS coordinates of everyone in your circle via an interactive map built with Google Maps and flutter_map.

Safe Places (Geofencing): Set custom boundaries (Home, School, Work) and receive automated push notifications when family members cross them.

🚨 Unignorable SOS Alerts
Global Vibrate Overlay: When an SOS triggers, the receiving family members' phones instantly lock into a high-visibility red emergency screen.

Continuous Haptics: Overrides typical notification settings with a looping haptic vibration pattern that cannot be muted or dismissed until physically acknowledged.

Instant Context Dispatch: Streams live location, ambient audio clips, and critical sensor data to the circle immediately.

🚗 Telematics & Driving Insights
Monitors vehicle speed, hard braking events, and phone distractions while driving to generate weekly safety scores.

🛠️ Architecture & Tech Stack
Nirvan utilizes a decoupled microservices architecture designed for fast execution, cross-platform stability, and low latency.

---

### 🛠️ Tech Matrix

| Layer | Technologies Used | Key Purpose |
| :--- | :--- | :--- |
| **Frontend Mobile App** | `Flutter (Dart)`, `Provider` | Cross-platform UI, state management, native performance. |
| **Edge Machine Learning** | `tflite_flutter` | Local on-device model inference without network dependence. |
| **Hardware Channels** | `camera`, `record`, `sensors_plus` | Access to microphone streams, accelerometer, and camera feeds. |
| **Backend API** | `Python FastAPI` | High-performance asynchronous microservice engine. |
| **Database Management** | `PostgreSQL`, `SQLAlchemy` | Persistent storage for user metrics, relational circles, and telematics. |
| **Real-Time Sync** | `Firebase Cloud Firestore` | Distributed pub-sub mechanism for instantaneous SOS broadcasting. |

---




🏃‍♂️ Getting Started & Local Setup
📋 Prerequisites
Before setting up the project locally, ensure you have the following installed:

Flutter SDK (Stable Channel)

Python 3.10+

PostgreSQL Engine

1. Backend Setup (FastAPI)
Bash
# Navigate to the backend agent directory
cd nirvan-motion-agent

# Create and activate a isolated python virtual environment
python -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate

# Install required dependencies
pip install -r requirements.txt

# Start the local asynchronous development server
uvicorn server.main_app:app --reload
2. Frontend Setup (Flutter)
Bash
# Navigate to the mobile application root
cd nirvan_mobile_app

# Fetch and cache all system packages
flutter pub get

# Generate custom launcher icons and native bindings
flutter pub run flutter_launcher_icons

# Launch the application on a connected device or emulator
flutter run
🔒 Privacy First
Nirvan is built with a strict Privacy-by-Design philosophy:

Zero Cloud Overhead: Raw audio buffers and camera frames are never recorded, saved, or streamed to any cloud provider.

Edge Execution: All machine learning inference occurs 100% locally on the device using optimized TensorFlow Lite execution kernels.

End-to-End Encryption: Critical location logs are encrypted so that only authenticated members within your explicit, user-approved Family Circle can read them.





