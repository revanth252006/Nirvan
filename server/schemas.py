from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Trip Schemas ---
class TripBase(BaseModel):
    title: str
    subtitle: str
    score: int

class Trip(TripBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

# --- SafePlace Schemas ---
class SafePlaceBase(BaseModel):
    name: str
    address: str

class SafePlaceCreate(SafePlaceBase):
    lat: float
    lng: float

class SafePlace(SafePlaceBase):
    id: int
    user_id: int
    lat: float = 0.0
    lng: float = 0.0
    class Config:
        from_attributes = True

# --- EmergencyContact Schemas ---
class EmergencyContactBase(BaseModel):
    name: str
    phone: str
    profile_photo_url: Optional[str] = None

class EmergencyContact(EmergencyContactBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

# --- Alert Schemas ---
class AlertBase(BaseModel):
    title: str
    message: str
    severity: str

class Alert(AlertBase):
    id: int
    timestamp: datetime
    circle_id: int
    class Config:
        from_attributes = True

# --- Circle Schemas ---
class CircleBase(BaseModel):
    name: str

class CircleCreate(CircleBase):
    pass

class Circle(CircleBase):
    id: int
    invite_code: str
    alerts: List[Alert] = []
    class Config:
        from_attributes = True

# --- User Schemas ---
class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    profile_photo_url: Optional[str] = None

class UserCreate(UserBase):
    password: str
    otp: str

class OTPRequest(BaseModel):
    email: str

class User(UserBase):
    id: int
    is_premium: bool
    driving_score: int
    circle_id: Optional[int] = None
    circle: Optional[Circle] = None
    trips: List[Trip] = []
    safe_places: List[SafePlace] = []
    emergency_contacts: List[EmergencyContact] = []
    class Config:
        from_attributes = True

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str
    circle_id: Optional[int] = None

class TokenData(BaseModel):
    email: Optional[str] = None
