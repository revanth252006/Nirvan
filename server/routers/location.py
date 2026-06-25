import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, List
from ..database import get_db
from .. import models

router = APIRouter(tags=["Live Location"])

# Circle ID -> List of active WebSocket connections
class ConnectionManager:
    def __init__(self):
        # Maps circle_id -> {user_id -> WebSocket}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, circle_id: int, user_id: int):
        await websocket.accept()
        if circle_id not in self.active_connections:
            self.active_connections[circle_id] = {}
        self.active_connections[circle_id][user_id] = websocket
        print(f"📡 User {user_id} connected to Circle {circle_id} Live Map")

    def disconnect(self, circle_id: int, user_id: int):
        if circle_id in self.active_connections:
            if user_id in self.active_connections[circle_id]:
                del self.active_connections[circle_id][user_id]
            if len(self.active_connections[circle_id]) == 0:
                del self.active_connections[circle_id]
        print(f"🔌 User {user_id} disconnected from Circle {circle_id} Live Map")

    async def broadcast_to_circle(self, circle_id: int, message: dict):
        if circle_id in self.active_connections:
            for uid, connection in self.active_connections[circle_id].items():
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending to {uid}: {e}")

import math

# State mapping: user_id -> { place_id -> is_inside }
user_place_state = {}

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371e3 # metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2-lat1)
    delta_lambda = math.radians(lon2-lon1)

    a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

manager = ConnectionManager()

@router.websocket("/location/ws/{circle_id}/{user_id}")
async def location_websocket(websocket: WebSocket, circle_id: int, user_id: int, db: Session = Depends(get_db)):
    await manager.connect(websocket, circle_id, user_id)
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    user_name = user.name if user else f"User {user_id}"

    if user_id not in user_place_state:
        user_place_state[user_id] = {}

    try:
        while True:
            data = await websocket.receive_text()
            location_data = json.loads(data)
            
            lat = location_data.get("lat")
            lng = location_data.get("lng")
            
            if lat is not None and lng is not None:
                # Check Safe Places
                places = db.query(models.SafePlace).filter(models.SafePlace.user_id == user_id).all()
                for place in places:
                    if place.lat == 0.0 and place.lng == 0.0:
                        continue
                    
                    dist = calculate_distance(lat, lng, place.lat, place.lng)
                    is_inside = dist <= 200 # 200 meters radius
                    
                    was_inside = user_place_state[user_id].get(place.id, False)
                    
                    if is_inside and not was_inside:
                        # Just arrived
                        user_place_state[user_id][place.id] = True
                        alert = models.Alert(
                            title="Safe Arrival",
                            message=f"{user_name} arrived at {place.name}",
                            severity="info",
                            circle_id=circle_id
                        )
                        db.add(alert)
                        db.commit()
                        db.refresh(alert)
                        await manager.broadcast_to_circle(circle_id, {
                            "type": "alert",
                            "alert": {
                                "id": alert.id,
                                "title": alert.title,
                                "message": alert.message,
                                "severity": alert.severity,
                                "timestamp": alert.timestamp.isoformat()
                            }
                        })
                    elif not is_inside and was_inside:
                        # Just left
                        user_place_state[user_id][place.id] = False
                        alert = models.Alert(
                            title="Departure",
                            message=f"{user_name} left {place.name}",
                            severity="info",
                            circle_id=circle_id
                        )
                        db.add(alert)
                        db.commit()
                        db.refresh(alert)
                        await manager.broadcast_to_circle(circle_id, {
                            "type": "alert",
                            "alert": {
                                "id": alert.id,
                                "title": alert.title,
                                "message": alert.message,
                                "severity": alert.severity,
                                "timestamp": alert.timestamp.isoformat()
                            }
                        })

            broadcast_msg = {
                "user_id": user_id,
                "name": user_name,
                "lat": lat,
                "lng": lng,
                "battery": location_data.get("battery", 100)
            }
            
            await manager.broadcast_to_circle(circle_id, broadcast_msg)
            
    except WebSocketDisconnect:
        manager.disconnect(circle_id, user_id)
        # Notify others that this user went offline
        await manager.broadcast_to_circle(circle_id, {
            "user_id": user_id,
            "name": user_name,
            "status": "offline"
        })
