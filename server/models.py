from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Circle(Base):
    __tablename__ = "circles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    invite_code = Column(String, unique=True, index=True)

    members = relationship("User", back_populates="circle")
    alerts = relationship("Alert", back_populates="circle")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    profile_photo_url = Column(String, nullable=True)
    
    # New Fields
    is_premium = Column(Boolean, default=False)
    driving_score = Column(Integer, default=100)
    
    circle_id = Column(Integer, ForeignKey("circles.id"), nullable=True)
    circle = relationship("Circle", back_populates="members")
    
    trips = relationship("Trip", back_populates="user")
    safe_places = relationship("SafePlace", back_populates="user")
    emergency_contacts = relationship("EmergencyContact", back_populates="user")

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String) # e.g. "Home to Office"
    subtitle = Column(String) # e.g. "12 miles • 24 mins"
    score = Column(Integer) # e.g. 94
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="trips")

class SafePlace(Base):
    __tablename__ = "safe_places"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    address = Column(String)
    lat = Column(Float, default=0.0)
    lng = Column(Float, default=0.0)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="safe_places")

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    phone = Column(String)
    profile_photo_url = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="emergency_contacts")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    message = Column(String)
    severity = Column(String, default="info") # info, warning, critical
    timestamp = Column(DateTime, default=datetime.utcnow)
    circle_id = Column(Integer, ForeignKey("circles.id"))
    circle = relationship("Circle", back_populates="alerts")

class OTP(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, index=True)
    otp_code = Column(String)
    expires_at = Column(DateTime)
