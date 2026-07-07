import string
import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/circles", tags=["Family Circles"])

def generate_invite_code(length=6):
    """Generate a random 6-character alphanumeric invite code."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))

@router.post("/create", response_model=schemas.Circle)
def create_circle(circle: schemas.CircleCreate, user_id: int, db: Session = Depends(get_db)):
    # Verify the user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Generate a unique invite code
    invite_code = generate_invite_code()
    while db.query(models.Circle).filter(models.Circle.invite_code == invite_code).first() is not None:
        invite_code = generate_invite_code()
        
    new_circle = models.Circle(
        name=circle.name,
        invite_code=invite_code
    )
    db.add(new_circle)
    db.commit()
    db.refresh(new_circle)
    
    # Automatically add the creator to this new circle
    user.circle_id = new_circle.id
    db.commit()
    
    return new_circle

@router.post("/join")
def join_circle(invite_code: str, user_id: int, db: Session = Depends(get_db)):
    circle = db.query(models.Circle).filter(models.Circle.invite_code == invite_code).first()
    if not circle:
        raise HTTPException(status_code=404, detail="Invalid invite code")
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.circle_id = circle.id
    db.commit()
    
    return {"message": f"Successfully joined {circle.name}", "circle_id": circle.id}

@router.get("/{circle_id}/members")
def get_circle_members(circle_id: int, db: Session = Depends(get_db)):
    circle = db.query(models.Circle).filter(models.Circle.id == circle_id).first()
    if not circle:
        raise HTTPException(status_code=404, detail="Circle not found")
        
    # Return all members dynamically, unlimited size!
    members = db.query(models.User).filter(models.User.circle_id == circle_id).all()
    return [{"id": m.id, "name": m.name, "phone": m.phone} for m in members]

@router.delete("/{circle_id}/members/{user_id}")
def remove_member(circle_id: int, user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id, models.User.circle_id == circle_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Member not found in this circle")
    
    user.circle_id = None
    db.commit()
    return {"message": f"Successfully removed user from circle"}
