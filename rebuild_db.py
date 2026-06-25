import os
from sqlalchemy import create_engine
from server.models import Base, User, Circle, Trip, SafePlace, EmergencyContact, Alert
from server.routers.auth import get_password_hash

# Force delete the db file if possible, or just drop all
db_path = "nirvan.db"

engine = create_engine(f"sqlite:///{db_path}")

print("Dropping old tables...")
Base.metadata.drop_all(bind=engine)

print("Creating new tables...")
Base.metadata.create_all(bind=engine)

from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("Inserting Mock Data...")
# 1. Create a Circle
circle = Circle(name="Nirvan Family", invite_code="TEST12")
db.add(circle)
db.commit()

# 2. Create the User
hashed_pw = get_password_hash("password123")
user = User(
    name="Admin User",
    email="admin@test.com",
    phone="5550000000",
    hashed_password=hashed_pw,
    is_premium=True,
    driving_score=94,
    circle_id=circle.id
)
db.add(user)
db.commit()

# 3. Add Trips
db.add(Trip(title="Home to Office", subtitle="12 miles • 24 mins", score=94, user_id=user.id))
db.add(Trip(title="Office to Gym", subtitle="4 miles • 10 mins", score=98, user_id=user.id))
db.add(Trip(title="Gym to Home", subtitle="10 miles • 20 mins", score=92, user_id=user.id))

# 4. Add Safe Places
db.add(SafePlace(name="Home", address="123 Main St", lat=17.3850, lng=78.4867, user_id=user.id))
db.add(SafePlace(name="Work", address="456 Market St", lat=17.3950, lng=78.4967, user_id=user.id))
db.add(SafePlace(name="School", address="789 Education Blvd", lat=17.3750, lng=78.4767, user_id=user.id))

# 5. Add Emergency Contacts
db.add(EmergencyContact(name="Mom", phone="555-0101", user_id=user.id))
db.add(EmergencyContact(name="Dad", phone="555-0102", user_id=user.id))

# 6. Add Alerts
db.add(Alert(title="Safe Arrival", message="Mom arrived at Home", severity="info", circle_id=circle.id))
db.add(Alert(title="Speed Warning", message="Dad is driving 75 in a 55 zone", severity="warning", circle_id=circle.id))

db.commit()
print("Database successfully rebuilt and seeded with dynamic mock data!")
