from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database.session import get_db
from app.models.base import User
from passlib.context import CryptContext

router = APIRouter()

import hashlib
import bcrypt

def get_password_hash(password):
    pre_hashed = hashlib.sha256(password.encode()).hexdigest()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pre_hashed.encode(), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    pre_hashed = hashlib.sha256(plain_password.encode()).hexdigest()
    return bcrypt.checkpw(pre_hashed.encode(), hashed_password.encode('utf-8'))

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
        
    hashed = get_password_hash(request.password)
    new_user = User(
        username=request.username,
        hashed_password=hashed,
        api_key=User.generate_api_key()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "api_key": new_user.api_key,
        "username": new_user.username,
        "message": "Registration successful."
    }

@router.post("/login")
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    if not user.hashed_password:
        raise HTTPException(status_code=400, detail="User was created without a password. Please contact support or re-register.")
        
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    return {
        "api_key": user.api_key,
        "username": user.username,
        "message": "Login successful."
    }
