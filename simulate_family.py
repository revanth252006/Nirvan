import asyncio
import json
import websockets

async def simulate_movement():
    circle_id = 1  # Assuming your first circle is ID 1
    user_id = 999  # Fake User ID
    uri = f"ws://127.0.0.1:8000/location/ws/{circle_id}/{user_id}"
    
    # Starting coordinates (Hyderabad, roughly same as default in app)
    lat = 17.3850
    lng = 78.4867
    
    print("🚗 Starting Family Member Simulator...")
    print(f"Connecting to Circle {circle_id} as User {user_id}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! 'User 999' is now sharing location.")
            
            # We must process incoming messages (like the location of the real app) 
            # otherwise the connection will timeout and drop.
            async def keep_receiving():
                try:
                    while True:
                        await websocket.recv()
                except:
                    pass
            
            asyncio.create_task(keep_receiving())
            
            while True:
                # Move slightly to simulate driving
                lat += 0.0001
                lng += 0.0001
                
                payload = {
                    "lat": lat,
                    "lng": lng,
                    "battery": 85
                }
                
                await websocket.send(json.dumps(payload))
                print(f"📍 Sent updated location: {lat:.5f}, {lng:.5f}")
                
                await asyncio.sleep(2)  # Update every 2 seconds
    except Exception as e:
        print(f"❌ Connection Failed. Make sure Python backend is running. Error: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_movement())
