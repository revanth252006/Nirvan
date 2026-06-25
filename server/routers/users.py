from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

# We import get_current_user from auth.py which we will add next
from .auth import get_current_user

@router.get("/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

class UserUpdate(schemas.UserBase):
    pass

@router.put("/me", response_model=schemas.User)
def update_me(user_update: UserUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_user.name = user_update.name
    current_user.email = user_update.email
    current_user.phone = user_update.phone
    db.commit()
    db.refresh(current_user)
    return current_user

import os
import shutil
from fastapi import UploadFile, File

# Create uploads dir if not exists
os.makedirs("uploads", exist_ok=True)

@router.post("/me/photo", response_model=schemas.User)
def upload_profile_photo(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Save file
    _, ext = os.path.splitext(file.filename)
    filename = f"user_{current_user.id}{ext}"
    file_path = f"uploads/{filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Generate relative URL that main_app.py serves
    photo_url = f"/static/{filename}"
    
    current_user.profile_photo_url = photo_url
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/{email}/photo", response_model=schemas.User)
def upload_user_photo(
    email: str,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        # Create user silently to fix offline registration sync issues
        from .auth import get_password_hash
        user = models.User(
            email=email,
            name="Nirvan User",
            phone="Unknown",
            hashed_password=get_password_hash("default_pass_123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    _, ext = os.path.splitext(file.filename)
    filename = f"user_{user.id}{ext}"
    file_path = f"uploads/{filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    photo_url = f"/static/{filename}"
    
    user.profile_photo_url = photo_url
    db.commit()
    db.refresh(user)
    return user
