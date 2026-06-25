from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/driving", tags=["driving"])

@router.get("/{user_id}/trips", response_model=list[schemas.Trip])
def get_user_trips(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Trip).filter(models.Trip.user_id == user_id).all()

@router.post("/{user_id}/trips", response_model=schemas.Trip)
def create_trip(user_id: int, trip: schemas.TripBase, db: Session = Depends(get_db)):
    db_trip = models.Trip(**trip.dict(), user_id=user_id)
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip
