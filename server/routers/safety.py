from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/safety", tags=["safety"])

@router.get("/{user_id}/places", response_model=list[schemas.SafePlace])
def get_safe_places(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.SafePlace).filter(models.SafePlace.user_id == user_id).all()

from .auth import get_current_user

@router.get("/contacts", response_model=list[schemas.EmergencyContact])
def get_emergency_contacts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.EmergencyContact).filter(models.EmergencyContact.user_id == current_user.id).all()

@router.post("/contacts", response_model=schemas.EmergencyContact)
def add_emergency_contact(contact: schemas.EmergencyContactBase, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    from fastapi import HTTPException
    existing_count = db.query(models.EmergencyContact).filter(models.EmergencyContact.user_id == current_user.id).count()
    if existing_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 emergency contacts allowed")
        
    new_contact = models.EmergencyContact(
        name=contact.name,
        phone=contact.phone,
        user_id=current_user.id
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

@router.delete("/contacts/{contact_id}")
def delete_emergency_contact(contact_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    contact = db.query(models.EmergencyContact).filter(models.EmergencyContact.id == contact_id, models.EmergencyContact.user_id == current_user.id).first()
    if not contact:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Contact not found")
    
    db.delete(contact)
    db.commit()
    return {"detail": "Contact deleted"}

@router.get("/alerts/{circle_id}", response_model=list[schemas.Alert])
def get_circle_alerts(circle_id: int, db: Session = Depends(get_db)):
    return db.query(models.Alert).filter(models.Alert.circle_id == circle_id).order_by(models.Alert.timestamp.desc()).all()

from .location import manager

@router.post("/sos", response_model=schemas.Alert)
async def trigger_sos(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.circle_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="User is not in a circle")
    
    # Create Alert
    alert = models.Alert(
        title="SOS ACTIVATED",
        message=f"{current_user.name} triggered an SOS emergency!",
        severity="critical",
        circle_id=current_user.circle_id
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # Broadcast to circle
    await manager.broadcast_to_circle(current_user.circle_id, {
        "type": "alert",
        "alert": {
            "id": alert.id,
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity,
            "timestamp": alert.timestamp.isoformat()
        }
    })
    
    return alert

from pydantic import BaseModel

class AgentSOS(BaseModel):
    user_id: int

@router.post("/agent_sos", response_model=schemas.Alert)
async def agent_trigger_sos(payload: AgentSOS, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == payload.user_id).first()
    if not user or not user.circle_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="User not found or not in a circle")
        
    alert = models.Alert(
        title="AI AGENT SOS",
        message=f"Agent detected a critical threat for {user.name}!",
        severity="critical",
        circle_id=user.circle_id
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    await manager.broadcast_to_circle(user.circle_id, {
        "type": "alert",
        "alert": {
            "id": alert.id,
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity,
            "timestamp": alert.timestamp.isoformat()
        }
    })
    return alert

@router.post("/places", response_model=schemas.SafePlace)
def add_safe_place(place: schemas.SafePlaceCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    new_place = models.SafePlace(
        name=place.name,
        address=place.address,
        lat=place.lat,
        lng=place.lng,
        user_id=current_user.id
    )
    db.add(new_place)
    db.commit()
    db.refresh(new_place)
    return new_place

@router.delete("/places/{place_id}")
def delete_safe_place(place_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    place = db.query(models.SafePlace).filter(models.SafePlace.id == place_id, models.SafePlace.user_id == current_user.id).first()
    if not place:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Place not found")
    
    db.delete(place)
    db.commit()
    return {"detail": "Safe place deleted"}
