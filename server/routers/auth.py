from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter(prefix="/auth", tags=["Authentication"])

import random

class UserLogin(schemas.BaseModel):
    email: schemas.EmailStr
    password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_nirvan_key_replace_later")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10080)) # 1 week by default

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user


@router.get("/check-user")
def check_user(email: str, phone: str, db: Session = Depends(get_db)):
    db_phone = db.query(models.User).filter(models.User.phone == phone).first()
    if db_phone:
        raise HTTPException(status_code=400, detail="Mobile number is already existing")
        
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Mail is already existing")
    
    return {"status": "available"}

@router.post("/send-otp")
def send_otp(request: schemas.OTPRequest, db: Session = Depends(get_db)):
    # Clean up old OTPs for this phone if any
    db.query(models.OTP).filter(models.OTP.phone == request.phone).delete()
    
    # Generate a random 6-digit OTP
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=10) # Valid for 10 minutes
    
    new_otp = models.OTP(phone=request.phone, otp_code=otp, expires_at=expires_at)
    db.add(new_otp)
    db.commit()
    
    # TODO: Integrate external SMS provider (e.g. Twilio)
    # twilio_client.messages.create(body=f"Your Nirvan verification code is: {otp}", from_=TWILIO_NUMBER, to=request.phone)
    
    print(f"\n{'='*40}")
    print(f"📲 SMS SIMULATION TO {request.phone}:")
    print(f"Your Nirvan verification code is: {otp}")
    print(f"{'='*40}\n")
    return {"message": "OTP sent successfully"}

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verify OTP first (unless bypassed via UI)
    if user.otp != 'auto_verified_no_firebase':
        db_otp = db.query(models.OTP).filter(models.OTP.phone == user.phone, models.OTP.otp_code == user.otp).first()
        if not db_otp or db_otp.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_phone = db.query(models.User).filter(models.User.phone == user.phone).first()
    if db_phone:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    hashed_pw = get_password_hash(user.password)
    new_user = models.User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Remove OTP after successful registration
    db.query(models.OTP).filter(models.OTP.phone == user.phone).delete()
    db.commit()
    
    # Simulate Welcome Email
    print(f"\n{'='*40}")
    print(f"📧 EMAIL SIMULATION TO {user.email}:")
    print(f"Subject: Welcome to Nirvan, {user.name}!")
    print(f"Body: You have successfully created your Nirvan account. Stay safe!")
    print(f"{'='*40}\n")
    
    return new_user

@router.post("/login")
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    # Standard email and password login
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id, "name": user.name, "circle_id": user.circle_id}
