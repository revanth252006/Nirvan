from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
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
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..database import engine

@router.get("/reset-db")
def reset_db():
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    return {"status": "Database successfully reset and schema migrated!"}

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
def check_user(email: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Mail is already existing")
    
    return {"status": "available"}

def send_email_async(to_email: str, otp: str):
    sender_email = os.getenv("EMAIL_SENDER", "safenirvan@gmail.com")
    sender_password = os.getenv("EMAIL_PASSWORD", "wkorzbncmxrhcdax")
    
    if not sender_email or not sender_password:
        print(f"📧 EMAIL OTP SIMULATION TO {to_email}: {otp} (Configure EMAIL_SENDER and EMAIL_PASSWORD for real emails)")
        return
        
    try:
        msg = MIMEMultipart()
        msg['From'] = f"Nirvan App <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = "Your Nirvan Verification Code"
        
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 20px;">
                <h2 style="color: #4C51BF;">Nirvan Registration</h2>
                <p>Your verification code is:</p>
                <h1 style="letter-spacing: 5px; color: #2B6CB0; background: #EBF8FF; padding: 15px; border-radius: 10px; display: inline-block;">{otp}</h1>
                <p>This code will expire in 10 minutes.</p>
                <p style="color: #718096; font-size: 12px; margin-top: 30px;">If you didn't request this, please ignore this email.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"✅ Real email successfully sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")

@router.post("/send-otp")
def send_otp(request: schemas.OTPRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # Clean up old OTPs for this email if any
        db.query(models.OTP).filter(models.OTP.email == request.email).delete()
        
        # Generate a random 6-digit OTP
        otp = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=10) # Valid for 10 minutes
        
        new_otp = models.OTP(email=request.email, otp_code=otp, expires_at=expires_at)
        db.add(new_otp)
        db.commit()
        
        background_tasks.add_task(send_email_async, request.email, otp)
        
        return {"message": "OTP processing started"}
    except Exception as e:
        import traceback
        error_msg = f"Exception: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/verify-email-otp")
def verify_email_otp(request: schemas.UserCreate, db: Session = Depends(get_db)):
    db_otp = db.query(models.OTP).filter(models.OTP.email == request.email, models.OTP.otp_code == request.otp).first()
    if not db_otp or db_otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    return {"status": "success"}

@router.get("/test-email")
def test_email(to_email: str = "a.revanth2006@gmail.com"):
    try:
        sender_email = os.getenv("EMAIL_SENDER", "safenirvan@gmail.com")
        sender_password = os.getenv("EMAIL_PASSWORD", "wkorzbncmxrhcdax")
        
        msg = MIMEMultipart()
        msg['From'] = f"Nirvan App <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = "Test from Render"
        msg.attach(MIMEText("Test", 'html'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return {"status": "Success! The email went through."}
    except Exception as e:
        import traceback
        return {"status": "Failed", "error": str(e), "traceback": traceback.format_exc()}

@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Verify OTP first (unless bypassed via UI)
    if user.otp != 'auto_verified_no_firebase':
        db_otp = db.query(models.OTP).filter(models.OTP.email == user.email, models.OTP.otp_code == user.otp).first()
        if not db_otp or db_otp.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if user.phone:
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
    db.query(models.OTP).filter(models.OTP.email == user.email).delete()
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
